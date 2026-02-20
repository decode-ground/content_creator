"""VideoGenerationAgent — calls Kling AI (or mock) to produce one video clip per scene."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scene import Scene
from app.models.storyboard import StoryboardImage
from app.models.video import GeneratedVideo, VideoPrompt
from app.phases.base_agent import BaseAgent
from app.phases.storyboard_to_movie.video_generator import generate_video_clip


class VideoGenerationAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "video_generation"

    async def execute(self, db: AsyncSession, project_id: int) -> dict:
        # 1. Read scenes in order
        scenes_result = await db.execute(
            select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
        )
        scenes = list(scenes_result.scalars().all())

        if not scenes:
            return {"status": "error", "message": "No scenes found"}

        # 2. Build lookups: sceneId → VideoPrompt, sceneId → StoryboardImage
        prompts_result = await db.execute(
            select(VideoPrompt).where(VideoPrompt.projectId == project_id)
        )
        prompt_by_scene = {vp.sceneId: vp for vp in prompts_result.scalars().all()}

        frames_result = await db.execute(
            select(StoryboardImage).where(StoryboardImage.projectId == project_id)
        )
        frame_by_scene = {f.sceneId: f for f in frames_result.scalars().all()}

        videos_created = 0
        errors: list[str] = []

        for scene in scenes:
            vp = prompt_by_scene.get(scene.id)
            if not vp:
                errors.append(
                    f"Scene {scene.sceneNumber}: no video prompt — run /prompts first"
                )
                continue

            # Storyboard image URL is the visual reference for image-to-video
            frame = frame_by_scene.get(scene.id)
            image_url = frame.imageUrl if frame else None

            try:
                clip = await generate_video_clip(
                    prompt=vp.prompt,
                    duration=vp.duration or 5,
                    project_id=project_id,
                    scene_id=scene.id,
                    image_url=image_url,  # storyboard frame as visual reference
                )
                db.add(
                    GeneratedVideo(
                        sceneId=scene.id,
                        projectId=project_id,
                        videoUrl=clip.videoUrl,
                        videoKey=clip.videoKey,
                        duration=clip.duration,
                        status="completed",
                    )
                )
                await db.commit()
                videos_created += 1
                self.logger.info(
                    "Scene %d/%d clip ready (image_ref=%s): %s",
                    scene.sceneNumber,
                    len(scenes),
                    bool(image_url),
                    clip.videoUrl[:70],
                )
            except Exception as e:
                self.logger.error(
                    "Video generation failed for scene %d: %s", scene.id, e
                )
                errors.append(f"Scene {scene.sceneNumber}: {e}")
                db.add(
                    GeneratedVideo(
                        sceneId=scene.id,
                        projectId=project_id,
                        status="failed",
                        errorMessage=str(e),
                    )
                )
                await db.commit()

        return {
            "status": "success" if not errors else "partial",
            "message": f"Generated {videos_created}/{len(scenes)} video clips",
            "videos_created": videos_created,
            "errors": errors,
        }
