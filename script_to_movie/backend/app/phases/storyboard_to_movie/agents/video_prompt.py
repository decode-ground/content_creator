"""VideoPromptAgent — generates optimised Kling video prompts for each scene via Claude."""
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.scene import Scene
from app.models.setting import Setting
from app.models.video import VideoPrompt
from app.phases.base_agent import BaseAgent
from app.phases.storyboard_to_movie.prompts import VIDEO_PROMPT_SYSTEM_PROMPT, VideoPromptOutput


class VideoPromptAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "video_prompt"

    async def execute(self, db: AsyncSession, project_id: int) -> dict:
        # 1. Read all scenes in order
        scenes_result = await db.execute(
            select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
        )
        scenes = list(scenes_result.scalars().all())

        if not scenes:
            return {"status": "error", "message": "No scenes found. Run Phase 1 first."}

        # 2. Load character and setting visual descriptions for context
        chars_result = await db.execute(
            select(Character).where(Character.projectId == project_id)
        )
        character_map = {c.name: c for c in chars_result.scalars().all()}

        settings_result = await db.execute(
            select(Setting).where(Setting.projectId == project_id)
        )
        setting_map = {s.name: s for s in settings_result.scalars().all()}

        prompts_created = 0

        for scene in scenes:
            scene_characters = json.loads(scene.characters or "[]")
            char_descriptions = "\n".join(
                f"- {name}: {character_map[name].visualDescription}"
                for name in scene_characters
                if name in character_map and character_map[name].visualDescription
            )

            setting_obj = setting_map.get(scene.setting or "")
            setting_description = ""
            if setting_obj and setting_obj.visualDescription:
                setting_description = (
                    f"Setting: {setting_obj.name}\n{setting_obj.visualDescription}"
                )

            user_message = (
                f"Scene {scene.sceneNumber}: {scene.title}\n\n"
                f"Description: {scene.description}\n\n"
                f"Characters present:\n{char_descriptions or 'No specific characters'}\n\n"
                f"{setting_description or 'No specific setting description'}\n\n"
                f"Scene duration target: {scene.duration or 8} seconds"
            )

            result: VideoPromptOutput = await self.llm.invoke_structured(
                messages=[{"role": "user", "content": user_message}],
                output_schema=VideoPromptOutput,
                system=VIDEO_PROMPT_SYSTEM_PROMPT,
                max_tokens=2048,
            )

            db.add(
                VideoPrompt(
                    sceneId=scene.id,
                    projectId=project_id,
                    prompt=result.prompt,
                    duration=result.duration,
                    style=f"{result.style} | {result.cameraMovement}",
                )
            )
            await db.commit()
            prompts_created += 1
            self.logger.info(
                "Generated video prompt %d/%d for project %d",
                prompts_created,
                len(scenes),
                project_id,
            )

        return {
            "status": "success",
            "message": f"Generated {prompts_created} video prompts",
            "prompts_created": prompts_created,
        }
