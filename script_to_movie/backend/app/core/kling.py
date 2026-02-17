"""Kling AI API client for video generation.

Uses httpx for async HTTP and PyJWT for authentication.
Reads credentials from environment variables directly (avoids modifying shared config).
"""

import asyncio
import os
import time

import httpx
import jwt

BASE_URL = "https://api.klingai.com"


class KlingClient:
    def __init__(self):
        self._http_client: httpx.AsyncClient | None = None

    def _get_credentials(self) -> tuple[str, str]:
        access_key = os.environ.get("KLING_ACCESS_KEY", "")
        secret_key = os.environ.get("KLING_SECRET_KEY", "")
        if not access_key or not secret_key:
            raise RuntimeError(
                "KLING_ACCESS_KEY and KLING_SECRET_KEY must be set in environment"
            )
        return access_key, secret_key

    def _generate_token(self) -> str:
        access_key, secret_key = self._get_credentials()
        now = int(time.time())
        payload = {
            "iss": access_key,
            "exp": now + 1800,  # 30 minute expiry
            "nbf": now - 5,
            "iat": now,
        }
        headers = {"alg": "HS256", "typ": "JWT"}
        return jwt.encode(payload, secret_key, algorithm="HS256", headers=headers)

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=BASE_URL,
                timeout=httpx.Timeout(60.0),
            )
        return self._http_client

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._generate_token()}"}

    async def text_to_video(
        self,
        prompt: str,
        model: str = "kling-v2",
        duration: str = "5",
        aspect_ratio: str = "16:9",
    ) -> str:
        """Submit a text-to-video generation task. Returns the task_id."""
        payload = {
            "model_name": model,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }
        response = await self.http.post(
            "/v1/videos/text2video",
            json=payload,
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Kling API error: {data.get('message', data)}")
        return data["data"]["task_id"]

    async def poll_task(
        self,
        task_id: str,
        poll_interval: float = 10.0,
        max_wait: float = 600.0,
    ) -> dict:
        """Poll a task until it succeeds or fails. Returns the task result dict."""
        elapsed = 0.0
        while elapsed < max_wait:
            response = await self.http.get(
                f"/v1/videos/text2video/{task_id}",
                headers=self._auth_headers(),
            )
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 0:
                raise RuntimeError(f"Kling API error: {data.get('message', data)}")

            task_data = data["data"]
            status = task_data.get("task_status")

            if status == "succeed":
                return task_data
            elif status == "failed":
                raise RuntimeError(
                    f"Kling task {task_id} failed: "
                    f"{task_data.get('task_status_msg', 'unknown error')}"
                )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Kling task {task_id} timed out after {max_wait}s")

    async def generate_video(
        self,
        prompt: str,
        model: str = "kling-v2",
        duration: str = "5",
        aspect_ratio: str = "16:9",
        poll_interval: float = 10.0,
        max_wait: float = 600.0,
    ) -> tuple[str, bytes]:
        """High-level: submit task, poll until done, download video.

        Returns (video_url, video_bytes).
        """
        task_id = await self.text_to_video(
            prompt=prompt, model=model, duration=duration, aspect_ratio=aspect_ratio
        )
        print(f"  Kling task submitted: {task_id}")

        result = await self.poll_task(
            task_id, poll_interval=poll_interval, max_wait=max_wait
        )

        videos = result.get("task_result", {}).get("videos", [])
        if not videos:
            raise RuntimeError(f"Kling task {task_id} returned no videos")

        video_url = videos[0]["url"]
        print(f"  Video ready: {video_url}")

        video_response = await self.http.get(video_url)
        video_response.raise_for_status()
        return video_url, video_response.content


kling_client = KlingClient()
