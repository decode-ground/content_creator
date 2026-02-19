"""Kling AI video generator — text-to-video with mock fallback.

Uses Kling AI's API to generate video clips from text prompts.
Falls back to placeholder videos when Kling API credits are unavailable.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass

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
        "model_name": "kling-v2-master",
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

            # Check for billing/balance errors — fall back to mock
            if response.status_code == 429:
                body = response.json()
                if body.get("code") == 1102:
                    logger.warning(
                        "Kling API: insufficient balance (code 1102) — using mock video"
                    )
                    return _mock_video_clip(prompt, duration, project_id, scene_id)

            response.raise_for_status()
            result = response.json()

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

                if task_status == "completed":
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
    """Assemble individual scene clips into a final trailer video.

    Currently returns a placeholder — real assembly requires ffmpeg/MoviePy.
    """
    movie_id = uuid.uuid4().hex[:8]
    movie_key = f"projects/{project_id}/trailers/trailer-{movie_id}.mp4"

    total_duration = sum(c.duration for c in clips)
    if len(clips) > 1:
        total_duration -= int(transition_duration * (len(clips) - 1))

    logger.info(
        "Trailer assembly for project %d: %d clips, %ds total",
        project_id,
        len(clips),
        total_duration,
    )

    trailer_url = clips[0].videoUrl if clips else ""

    return AssembledTrailer(
        movieUrl=trailer_url,
        movieKey=movie_key,
        totalDuration=total_duration,
    )
