import json
import logging

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.llm import llm_client
from app.models.project import Project
from app.models.scene import Scene
from app.phases.script_to_trailer.prompts import SCRIPT_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class SceneData(BaseModel):
    sceneNumber: int
    title: str
    description: str
    setting: str
    characters: list[str]
    estimatedDuration: int


class ScriptAnalysisResult(BaseModel):
    scenes: list[SceneData]


async def analyze_script(db: AsyncSession, project: Project) -> list[Scene]:
    logger.info(f"Starting script analysis for project {project.id}")

    project.status = "analyzing"
    project.progress = 10
    await db.commit()

    result = await llm_client.invoke_structured(
        messages=[
            {"role": "user", "content": f"Analyze this screenplay:\n\n{project.scriptContent}"}
        ],
        output_schema=ScriptAnalysisResult,
        system=SCRIPT_ANALYSIS_PROMPT,
        max_tokens=8192,
    )

    logger.info(f"Extracted {len(result.scenes)} scenes from script")

    scenes = []
    for scene_data in result.scenes:
        scene = Scene(
            projectId=project.id,
            sceneNumber=scene_data.sceneNumber,
            title=scene_data.title,
            description=scene_data.description,
            setting=scene_data.setting,
            characters=json.dumps(scene_data.characters),
            duration=scene_data.estimatedDuration,
            order=scene_data.sceneNumber,
        )
        db.add(scene)
        scenes.append(scene)

    await db.commit()

    # Refresh to get IDs
    for scene in scenes:
        await db.refresh(scene)

    project.progress = 20
    await db.commit()

    logger.info(f"Saved {len(scenes)} scenes for project {project.id}")
    return scenes
