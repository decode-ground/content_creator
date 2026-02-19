import logging

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.llm import llm_client
from app.models.project import Project
from app.models.scene import Scene
from app.models.setting import Setting
from app.phases.script_to_trailer.prompts import SETTING_CONSISTENCY_PROMPT

logger = logging.getLogger(__name__)


class SettingData(BaseModel):
    name: str
    description: str
    visualDescription: str


class SettingConsistencyResult(BaseModel):
    settings: list[SettingData]


async def extract_settings(db: AsyncSession, project: Project) -> list[Setting]:
    logger.info(f"Starting setting extraction for project {project.id}")

    result = await db.execute(
        select(Scene).where(Scene.projectId == project.id).order_by(Scene.sceneNumber)
    )
    scenes = result.scalars().all()

    scenes_text = "\n".join(
        f"Scene {s.sceneNumber} ({s.title}): {s.description} [Setting: {s.setting}]"
        for s in scenes
    )

    llm_result = await llm_client.invoke_structured(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Screenplay:\n{project.scriptContent}\n\n"
                    f"Scene breakdown:\n{scenes_text}"
                ),
            }
        ],
        output_schema=SettingConsistencyResult,
        system=SETTING_CONSISTENCY_PROMPT,
        max_tokens=8192,
    )

    logger.info(f"Extracted {len(llm_result.settings)} settings")

    settings = []
    for setting_data in llm_result.settings:
        setting = Setting(
            projectId=project.id,
            name=setting_data.name,
            description=setting_data.description,
            visualDescription=setting_data.visualDescription,
        )
        db.add(setting)
        settings.append(setting)

    await db.commit()

    for setting in settings:
        await db.refresh(setting)

    project.progress = 50
    await db.commit()

    logger.info(f"Saved {len(settings)} settings for project {project.id}")
    return settings
