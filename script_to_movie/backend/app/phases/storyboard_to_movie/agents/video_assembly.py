"""Final video assembly — standalone function, no agent class needed.

Takes all already-generated scene videos and concatenates them into one
final movie using ffmpeg.

Pipeline per scene:
    1. Download the generated video clip from its URL
    2. If the scene has dialogue, generate TTS audio (gTTS) and merge with video
    3. Collect the clip for concatenation

Final step:
    4. Write clips.txt and run ffmpeg concat demuxer
    5. Upload to S3 (local fallback if S3 unavailable)
    6. Create FinalMovie record, set project status to "completed", progress to 100

Requirements:
    - ffmpeg must be installed: `brew install ffmpeg`
    - gTTS: already in pyproject.toml
"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import storage_client
from app.models.final_movie import FinalMovie
from app.models.project import Project
from app.models.scene import Scene
from app.models.video import GeneratedVideo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers (sync — run via asyncio.to_thread)
# ---------------------------------------------------------------------------

def _run_ffmpeg(*args: str) -> None:
    """Run ffmpeg with the given args, raise RuntimeError on failure."""
    cmd = ["ffmpeg", "-y", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr[-600:]}")


def _generate_tts(text: str, output_path: str) -> None:
    """Generate an MP3 file from text using gTTS (Google TTS, no API key)."""
    from gtts import gTTS  # lazy import so missing dep doesn't break startup

    gTTS(text=text, lang="en", slow=False).save(output_path)


def _clean_dialogue(dialogue: str) -> str:
    """Strip 'CHARACTER_NAME: ' prefixes so TTS reads only the spoken text."""
    lines = []
    for line in dialogue.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            speaker, _, rest = line.partition(":")
            speaker = speaker.strip()
            if speaker.isupper() or (
                speaker.replace(" ", "").isalpha() and speaker[0].isupper()
            ):
                lines.append(rest.strip())
                continue
        lines.append(line)
    return " ".join(lines) if lines else dialogue


async def _upload_or_save_locally(data: bytes, key: str) -> str:
    """Upload to S3; if S3 is not configured, save under media/ and return the path."""
    try:
        return await storage_client.upload(
            key=key, data=data, content_type="video/mp4"
        )
    except Exception as e:
        logger.warning("S3 upload failed (%s) — saving to local media/", e)
        local_path = os.path.join("media", key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(data)
        return local_path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def assemble_final_movie(db: AsyncSession, project_id: int) -> dict:
    """Concatenate all generated scene videos into one final movie.

    Args:
        db: Async SQLAlchemy session.
        project_id: The project whose scenes to assemble.

    Returns:
        Dict with status, message, clips_assembled, total_duration, movie_url.
    """
    # 1. Query scenes ordered by Scene.order
    scenes_result = await db.execute(
        select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
    )
    scenes = list(scenes_result.scalars().all())

    if not scenes:
        return {"status": "error", "message": "No scenes found"}

    # 2. Load completed GeneratedVideo records, keyed by sceneId
    videos_result = await db.execute(
        select(GeneratedVideo).where(
            GeneratedVideo.projectId == project_id,
            GeneratedVideo.status == "completed",
        )
    )
    video_by_scene = {v.sceneId: v for v in videos_result.scalars().all()}

    if not video_by_scene:
        return {
            "status": "error",
            "message": "No completed videos found — run video generation first",
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        scene_clips: list[str] = []

        # 3. Download each clip (and optionally merge TTS audio)
        async with httpx.AsyncClient(timeout=120.0) as client:
            for scene in scenes:
                video = video_by_scene.get(scene.id)
                if not video or not video.videoUrl:
                    logger.warning(
                        "Scene %d: no completed video, skipping", scene.sceneNumber
                    )
                    continue

                # Download the clip
                raw_path = os.path.join(tmpdir, f"raw_{scene.order:03d}.mp4")
                try:
                    resp = await client.get(video.videoUrl)
                    resp.raise_for_status()
                    with open(raw_path, "wb") as f:
                        f.write(resp.content)
                except Exception as e:
                    logger.error(
                        "Scene %d: failed to download video (%s), skipping",
                        scene.sceneNumber,
                        e,
                    )
                    continue

                output_path = raw_path

                # TTS + merge if the scene has dialogue
                if scene.dialogue and scene.dialogue.strip():
                    audio_path = os.path.join(tmpdir, f"audio_{scene.order:03d}.mp3")
                    try:
                        tts_text = _clean_dialogue(scene.dialogue)
                        await asyncio.to_thread(_generate_tts, tts_text, audio_path)

                        combined_path = os.path.join(
                            tmpdir, f"combined_{scene.order:03d}.mp4"
                        )
                        await asyncio.to_thread(
                            _run_ffmpeg,
                            "-i", raw_path,
                            "-i", audio_path,
                            "-map", "0:v:0",
                            "-map", "1:a:0",
                            "-c:v", "copy",
                            "-c:a", "aac",
                            "-shortest",
                            combined_path,
                        )
                        output_path = combined_path
                        logger.info(
                            "Scene %d: TTS merged successfully", scene.sceneNumber
                        )
                    except Exception as e:
                        logger.warning(
                            "Scene %d: TTS/merge failed (%s) — using video only",
                            scene.sceneNumber,
                            e,
                        )

                scene_clips.append(output_path)

        if not scene_clips:
            return {
                "status": "error",
                "message": "All clips failed to download — nothing to assemble",
            }

        # 4. Concatenate all scene clips into one final movie
        final_path = os.path.join(tmpdir, "final_movie.mp4")
        if len(scene_clips) == 1:
            shutil.copy(scene_clips[0], final_path)
        else:
            list_file = os.path.join(tmpdir, "clips.txt")
            with open(list_file, "w") as f:
                for clip_path in scene_clips:
                    f.write(f"file '{clip_path}'\n")
            await asyncio.to_thread(
                _run_ffmpeg,
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-movflags", "+faststart",
                final_path,
            )

        # 5. Upload to S3 (local fallback)
        movie_key = f"projects/{project_id}/final_movie.mp4"
        with open(final_path, "rb") as f:
            movie_bytes = f.read()

        movie_url = await _upload_or_save_locally(movie_bytes, movie_key)

        # 6. Compute total duration from DB records
        total_duration = sum(
            video_by_scene[s.id].duration or 0
            for s in scenes
            if s.id in video_by_scene
        )

        # 7. Create FinalMovie record and mark project complete
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()

        db.add(
            FinalMovie(
                projectId=project_id,
                movieUrl=movie_url,
                movieKey=movie_key,
                duration=total_duration,
                status="completed",
            )
        )
        if project:
            project.status = "completed"
            project.progress = 100

        await db.commit()

        logger.info(
            "Project %d: final movie assembled — %d clips, %ds total → %s",
            project_id,
            len(scene_clips),
            total_duration,
            movie_url,
        )

        # 8. Return summary dict
        return {
            "status": "success",
            "message": f"Assembled {len(scene_clips)} clips into final movie",
            "clips_assembled": len(scene_clips),
            "total_duration": total_duration,
            "movie_url": movie_url,
        }
