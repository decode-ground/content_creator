"""StoryboardPromptAgent — extracts the best frame per scene from the trailer video
using Claude Vision to evaluate frame quality against scene context."""
import base64
import json
import logging
import os
import subprocess
import tempfile

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import storage_client
from app.models.character import Character
from app.models.project import Project
from app.models.scene import Scene
from app.models.setting import Setting
from app.models.storyboard import StoryboardImage
from app.phases.base_agent import BaseAgent
from app.phases.trailer_to_storyboard.prompts import FRAME_EVALUATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

FRAMES_PER_SCENE = 5  # candidate frames to extract per scene


class FrameEvaluation(BaseModel):
    best_frame_index: int  # 0-based index, or -1 if none are adequate
    reasoning: str


def _get_video_duration(video_path: str) -> float:
    """Return video duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            video_path,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())


def _extract_frame(video_path: str, timestamp: float) -> bytes | None:
    """Extract a single JPEG frame at the given timestamp. Returns None on failure."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                "-f", "image2",
                "-y",
                tmp_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        with open(tmp_path, "rb") as f:
            return f.read()
    except Exception:
        return None
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


class StoryboardPromptAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "storyboard_prompt"

    async def execute(self, db: AsyncSession, project_id: int) -> dict:
        # 1. Load project
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            return {"status": "error", "message": "Project not found"}
        if not project.trailerKey:
            return {"status": "error", "message": "No trailer video found — run Phase 1 first"}

        # 2. Load scenes, characters, settings from Phase 1
        scenes_result = await db.execute(
            select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
        )
        scenes = list(scenes_result.scalars().all())
        if not scenes:
            return {"status": "error", "message": "No scenes found — run Phase 1 first"}

        chars_result = await db.execute(
            select(Character).where(Character.projectId == project_id)
        )
        character_map = {c.name: c for c in chars_result.scalars().all()}

        settings_result = await db.execute(
            select(Setting).where(Setting.projectId == project_id)
        )
        setting_map = {s.name: s for s in settings_result.scalars().all()}

        # 3. Download trailer video from S3
        self.logger.info("Downloading trailer for project %d", project_id)
        video_bytes = await storage_client.download(project.trailerKey)

        frames_extracted = 0
        frames_failed = 0
        errors = []

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
            tmp_video.write(video_bytes)
            tmp_video_path = tmp_video.name

        try:
            # 4. Get video duration and map each scene to its time window
            video_duration = _get_video_duration(tmp_video_path)
            self.logger.info(
                "Trailer duration: %.1fs for %d scenes", video_duration, len(scenes)
            )

            # Scenes are stored in order; their durations map sequentially to the video
            cumulative = 0.0
            scene_windows: list[tuple[float, float]] = []
            for scene in scenes:
                duration = scene.duration or 8
                scene_windows.append((cumulative, cumulative + duration))
                cumulative += duration

            # 5. Process each scene
            for i, scene in enumerate(scenes):
                start_ts, end_ts = scene_windows[i]

                # Build context from Phase 1 character and setting descriptions
                scene_char_names = json.loads(scene.characters or "[]")
                char_desc = "\n".join(
                    f"- {name}: {character_map[name].visualDescription}"
                    for name in scene_char_names
                    if name in character_map and character_map[name].visualDescription
                ) or "No specific characters"

                setting_obj = setting_map.get(scene.setting or "")
                setting_desc = (
                    f"{setting_obj.name}: {setting_obj.visualDescription}"
                    if setting_obj and setting_obj.visualDescription
                    else scene.setting or "No specific setting"
                )

                # If this scene's window starts beyond the video, it wasn't in the trailer
                if start_ts >= video_duration:
                    self.logger.warning(
                        "Scene %d starts at t=%.1fs but trailer is only %.1fs — skipping",
                        scene.sceneNumber, start_ts, video_duration,
                    )
                    frames_failed += 1
                    errors.append(
                        f"Scene {scene.sceneNumber}: outside trailer duration"
                    )
                    await self._upsert_storyboard(
                        db, scene, project_id,
                        image_url="", image_key="",
                        prompt="Scene not covered by trailer",
                        status="failed",
                    )
                    continue

                actual_end = min(end_ts, video_duration)
                candidates = self._extract_candidate_frames(
                    tmp_video_path, start_ts, actual_end
                )

                if not candidates:
                    self.logger.warning(
                        "Scene %d: ffmpeg extracted no frames", scene.sceneNumber
                    )
                    frames_failed += 1
                    errors.append(f"Scene {scene.sceneNumber}: frame extraction failed")
                    await self._upsert_storyboard(
                        db, scene, project_id,
                        image_url="", image_key="",
                        prompt="Frame extraction failed",
                        status="failed",
                    )
                    continue

                # 6. Use Claude Vision to pick the best frame
                best_idx = await self._pick_best_frame(
                    scene, char_desc, setting_desc, candidates
                )

                if best_idx < 0:
                    self.logger.warning(
                        "Scene %d: Claude Vision found no adequate frame among %d candidates",
                        scene.sceneNumber, len(candidates),
                    )
                    frames_failed += 1
                    errors.append(f"Scene {scene.sceneNumber}: no adequate frame found")
                    await self._upsert_storyboard(
                        db, scene, project_id,
                        image_url="", image_key="",
                        prompt=f"No adequate frame found at t={start_ts:.1f}–{actual_end:.1f}s",
                        status="failed",
                    )
                    continue

                # 7. Upload the selected frame to S3
                image_key = (
                    f"projects/{project_id}/storyboard/scene_{scene.sceneNumber}.jpg"
                )
                image_url = await storage_client.upload(
                    key=image_key,
                    data=candidates[best_idx],
                    content_type="image/jpeg",
                )

                await self._upsert_storyboard(
                    db, scene, project_id,
                    image_url=image_url,
                    image_key=image_key,
                    prompt=(
                        f"Trailer frame {best_idx + 1}/{len(candidates)} "
                        f"at t={start_ts:.1f}–{actual_end:.1f}s — {scene.description[:120]}"
                    ),
                    status="completed",
                )

                frames_extracted += 1
                self.logger.info(
                    "Scene %d: saved frame %d/%d from t=%.1f–%.1fs",
                    scene.sceneNumber, best_idx + 1, len(candidates),
                    start_ts, actual_end,
                )

        finally:
            if os.path.exists(tmp_video_path):
                os.unlink(tmp_video_path)

        total = len(scenes)
        return {
            "status": "success" if frames_failed == 0 else "partial",
            "message": (
                f"Processed {total} scenes: "
                f"{frames_extracted} extracted, {frames_failed} failed"
            ),
            "frames_extracted": frames_extracted,
            "frames_failed": frames_failed,
            "errors": errors,
        }

    def _extract_candidate_frames(
        self, video_path: str, start_ts: float, end_ts: float
    ) -> list[bytes]:
        """Extract up to FRAMES_PER_SCENE evenly-spaced frames within [start_ts, end_ts],
        skipping the first and last 10% of the window to avoid transition frames."""
        duration = end_ts - start_ts
        if duration <= 0:
            return []

        margin = duration * 0.1
        sample_start = start_ts + margin
        sample_end = end_ts - margin
        if sample_end <= sample_start:
            sample_start, sample_end = start_ts, end_ts

        count = min(FRAMES_PER_SCENE, max(1, int(duration)))
        step = (sample_end - sample_start) / max(count - 1, 1)
        timestamps = [sample_start + step * j for j in range(count)]

        frames = []
        for ts in timestamps:
            data = _extract_frame(video_path, ts)
            if data:
                frames.append(data)
        return frames

    async def _pick_best_frame(
        self,
        scene: Scene,
        char_desc: str,
        setting_desc: str,
        frames: list[bytes],
    ) -> int:
        """Use Claude Vision to pick the best frame. Returns 0-based index or -1."""
        content: list[dict] = [
            {
                "type": "text",
                "text": (
                    f"Scene {scene.sceneNumber}: {scene.title}\n"
                    f"Description: {scene.description}\n\n"
                    f"Characters present:\n{char_desc}\n\n"
                    f"Setting:\n{setting_desc}\n\n"
                    f"Below are {len(frames)} candidate frames extracted from the trailer. "
                    f"Select the best frame that represents this scene, "
                    f"or return -1 if none are adequate."
                ),
            }
        ]
        for frame_bytes in frames:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.b64encode(frame_bytes).decode(),
                },
            })

        try:
            evaluation: FrameEvaluation = await self.llm.invoke_structured(
                messages=[{"role": "user", "content": content}],
                output_schema=FrameEvaluation,
                system=FRAME_EVALUATION_SYSTEM_PROMPT,
                max_tokens=512,
            )
            self.logger.info(
                "Vision eval scene %d: frame %d — %s",
                scene.sceneNumber, evaluation.best_frame_index, evaluation.reasoning,
            )
            return evaluation.best_frame_index
        except Exception as e:
            self.logger.warning(
                "Vision eval failed for scene %d: %s — defaulting to frame 0",
                scene.sceneNumber, e,
            )
            return 0  # default to first frame if the vision call itself fails

    async def _upsert_storyboard(
        self,
        db: AsyncSession,
        scene: Scene,
        project_id: int,
        image_url: str,
        image_key: str,
        prompt: str,
        status: str,
    ) -> None:
        """Create or update the StoryboardImage record for a scene."""
        existing_result = await db.execute(
            select(StoryboardImage).where(
                StoryboardImage.sceneId == scene.id,
                StoryboardImage.projectId == project_id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            existing.imageUrl = image_url
            existing.imageKey = image_key
            existing.prompt = prompt
            existing.status = status
        else:
            db.add(StoryboardImage(
                sceneId=scene.id,
                projectId=project_id,
                imageUrl=image_url,
                imageKey=image_key,
                prompt=prompt,
                status=status,
            ))
        await db.commit()
