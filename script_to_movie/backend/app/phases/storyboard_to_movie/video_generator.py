"""Kling AI video generator — text-to-video with mock fallback.

Uses Kling AI's API to generate video clips from text prompts.
Falls back to placeholder videos when Kling API credits are unavailable.
"""

import asyncio
import logging
import os
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx
import jwt

from app.config import get_settings

logger = logging.getLogger(__name__)

KLING_BASE_URL = "https://api.klingai.com/v1"
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 360  # 60 minutes max wait

# Public domain sample video for mock/demo mode
MOCK_VIDEO_URL = "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"


@dataclass
class VideoClip:
    videoUrl: str
    videoKey: str
    duration: int


@dataclass
class AssembledTrailer:
    movieUrl: str
    movieKey: str
    totalDuration: int


def _generate_kling_token() -> str:
    """Generate a JWT token for Kling AI API authentication."""
    settings = get_settings()
    now = int(time.time())
    payload = {
        "iss": settings.kling_api_key,
        "exp": now + 1800,  # 30 minutes
        "nbf": now - 5,
    }
    return jwt.encode(payload, settings.kling_secret_key, algorithm="HS256")


def _mock_video_clip(prompt: str, duration: int, project_id: int, scene_id: int) -> VideoClip:
    """Return a placeholder video clip for demo purposes."""
    video_key = f"projects/{project_id}/videos/scene-{scene_id}-{uuid.uuid4().hex[:8]}.mp4"
    logger.info(
        "Using mock video for project %d scene %d (Kling API unavailable): %s",
        project_id,
        scene_id,
        prompt[:60],
    )
    return VideoClip(
        videoUrl=MOCK_VIDEO_URL,
        videoKey=video_key,
        duration=duration if duration in (5, 10) else 5,
    )


async def generate_video_clip(
    prompt: str,
    duration: int,
    project_id: int,
    scene_id: int,
) -> VideoClip:
    """Generate a video clip for a single scene using Kling AI.

    Falls back to mock video if Kling API returns insufficient balance
    or if credentials are not configured.
    """
    settings = get_settings()
    if not settings.kling_api_key or not settings.kling_secret_key:
        logger.warning("Kling API keys not configured — using mock video")
        return _mock_video_clip(prompt, duration, project_id, scene_id)

    kling_duration = "5" if duration <= 7 else "10"

    token = _generate_kling_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    request_body = {
        "model_name": settings.kling_model,
        "prompt": prompt,
        "duration": kling_duration,
        "aspect_ratio": "16:9",
    }

    video_key = f"projects/{project_id}/videos/scene-{scene_id}-{uuid.uuid4().hex[:8]}.mp4"

    logger.info(
        "Submitting Kling AI task for project %d scene %d (%ss): %s",
        project_id,
        scene_id,
        kling_duration,
        prompt[:80],
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{KLING_BASE_URL}/videos/text2video",
                headers=headers,
                json=request_body,
            )

            # Check for errors in response body (Kling returns error codes even on 200)
            if response.status_code != 200:
                try:
                    body = response.json()
                except Exception:
                    body = {"raw": response.text}
                logger.warning(
                    "Kling API HTTP %d for project %d scene %d (model=%s): %s",
                    response.status_code,
                    project_id,
                    scene_id,
                    settings.kling_model,
                    body,
                )
                if response.status_code == 429 or body.get("code") == 1102:
                    return _mock_video_clip(prompt, duration, project_id, scene_id)
                response.raise_for_status()

            result = response.json()

            # Check for error codes in 200 responses
            if result.get("code") != 0:
                logger.warning(
                    "Kling API error code %s for project %d scene %d (model=%s): %s",
                    result.get("code"),
                    project_id,
                    scene_id,
                    settings.kling_model,
                    result.get("message", result),
                )
                if result.get("code") == 1102:
                    return _mock_video_clip(prompt, duration, project_id, scene_id)
                raise RuntimeError(f"Kling API error: {result.get('message', result)}")

            task_id = result["data"]["task_id"]
            logger.info("Kling task created: %s", task_id)

            # Poll for completion
            for attempt in range(MAX_POLL_ATTEMPTS):
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

                if attempt > 0 and attempt % 100 == 0:
                    token = _generate_kling_token()
                    headers["Authorization"] = f"Bearer {token}"

                poll_response = await client.get(
                    f"{KLING_BASE_URL}/videos/text2video/{task_id}",
                    headers=headers,
                )
                poll_response.raise_for_status()
                poll_result = poll_response.json()

                task_status = poll_result["data"]["task_status"]
                logger.info(
                    "Kling task %s status: %s (attempt %d)",
                    task_id,
                    task_status,
                    attempt + 1,
                )

                if task_status in ("completed", "succeed"):
                    videos = poll_result["data"]["task_result"]["videos"]
                    video_url = videos[0]["url"]

                    logger.info(
                        "Kling video ready for project %d scene %d: %s",
                        project_id,
                        scene_id,
                        video_url,
                    )

                    return VideoClip(
                        videoUrl=video_url,
                        videoKey=video_key,
                        duration=int(kling_duration),
                    )

                if task_status == "failed":
                    error_msg = poll_result.get("data", {}).get(
                        "task_status_msg", "Unknown error"
                    )
                    raise RuntimeError(
                        f"Kling video generation failed for task {task_id}: {error_msg}"
                    )

        raise TimeoutError(
            f"Kling video generation timed out after "
            f"{MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s for task {task_id}"
        )

    except httpx.HTTPStatusError as e:
        response_body = ""
        try:
            response_body = e.response.text
        except Exception:
            pass
        logger.warning(
            "Kling API error for project %d scene %d: %s — response: %s — using mock video",
            project_id,
            scene_id,
            str(e),
            response_body,
        )
        return _mock_video_clip(prompt, duration, project_id, scene_id)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning(
            "Kling API connection error for project %d scene %d: %s — using mock video",
            project_id,
            scene_id,
            str(e),
        )
        return _mock_video_clip(prompt, duration, project_id, scene_id)


async def assemble_trailer(
    clips: list[VideoClip],
    project_id: int,
    transition_duration: float = 0.5,
) -> AssembledTrailer:
    """Assemble individual scene clips into a final trailer video using ffmpeg."""
    if not clips:
        raise ValueError("Cannot assemble trailer: no clips provided")

    movie_id = uuid.uuid4().hex[:8]
    movie_key = f"projects/{project_id}/trailers/trailer-{movie_id}.mp4"

    total_duration = sum(c.duration for c in clips)

    logger.info(
        "Assembling trailer for project %d: %d clips, %ds total",
        project_id,
        len(clips),
        total_duration,
    )

    # If only one clip, just use it directly
    if len(clips) == 1:
        return AssembledTrailer(
            movieUrl=clips[0].videoUrl,
            movieKey=movie_key,
            totalDuration=total_duration,
        )

    # Multiple clips: concatenate with ffmpeg
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Download all clips
            clip_files = []
            async with httpx.AsyncClient(timeout=60.0) as client:
                for i, clip in enumerate(clips):
                    clip_path = tmpdir_path / f"clip_{i:03d}.mp4"
                    logger.info(f"Downloading clip {i+1}/{len(clips)}: {clip.videoUrl}")
                    response = await client.get(clip.videoUrl)
                    response.raise_for_status()
                    clip_path.write_bytes(response.content)
                    clip_files.append(clip_path)

            # Create concat list file for ffmpeg
            concat_file = tmpdir_path / "concat.txt"
            with open(concat_file, "w") as f:
                for clip_path in clip_files:
                    f.write(f"file '{clip_path.absolute()}'\n")

            # Run ffmpeg to concatenate and re-encode (ensures compatibility)
            output_path = tmpdir_path / "trailer.mp4"
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c:v", "libx264",      # Re-encode video to H.264
                "-preset", "fast",       # Fast encoding
                "-crf", "23",           # Quality (lower = better, 23 is default)
                "-c:a", "aac",          # Re-encode audio to AAC
                "-b:a", "128k",         # Audio bitrate
                "-movflags", "+faststart",  # Web optimization
                str(output_path),
            ]

            logger.info(f"Running ffmpeg: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg failed: {result.stderr}")
                raise RuntimeError(f"ffmpeg concatenation failed: {result.stderr}")

            # For now, store locally (in production you'd upload to S3)
            # Create output directory if needed
            output_dir = Path("./trailers")
            output_dir.mkdir(exist_ok=True)

            final_path = output_dir / f"trailer-{movie_id}.mp4"
            final_path.write_bytes(output_path.read_bytes())

            trailer_url = f"/trailers/trailer-{movie_id}.mp4"

            logger.info(
                "Trailer assembled for project %d: %s (%d clips, %ds)",
                project_id,
                trailer_url,
                len(clips),
                total_duration,
            )

            return AssembledTrailer(
                movieUrl=trailer_url,
                movieKey=movie_key,
                totalDuration=total_duration,
            )

    except Exception as e:
        logger.error(f"Trailer assembly failed: {e}")
        # Fallback: just return first clip
        return AssembledTrailer(
            movieUrl=clips[0].videoUrl,
            movieKey=movie_key,
            totalDuration=clips[0].duration,
        )
