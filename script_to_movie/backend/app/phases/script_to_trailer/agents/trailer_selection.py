import logging

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.llm import llm_client
from app.models.project import Project
from app.models.scene import Scene
from app.phases.script_to_trailer.prompts import TRAILER_SELECTION_PROMPT

logger = logging.getLogger(__name__)


class TrailerSelectionResult(BaseModel):
    selectedSceneNumbers: list[int]


async def select_trailer_scenes(db: AsyncSession, project: Project) -> list[Scene]:
    logger.info(f"Starting trailer scene selection for project {project.id}")

    result = await db.execute(
        select(Scene).where(Scene.projectId == project.id).order_by(Scene.sceneNumber)
    )
    scenes = result.scalars().all()
    scenes_by_number = {s.sceneNumber: s for s in scenes}

    scenes_text = "\n".join(
        f"Scene {s.sceneNumber} ({s.title}): {s.description}"
        for s in scenes
    )

    llm_result = await llm_client.invoke_structured(
        messages=[
            {
                "role": "user",
                "content": f"Total scenes: {len(scenes)}\n\nScene breakdown:\n{scenes_text}",
            }
        ],
        output_schema=TrailerSelectionResult,
        system=TRAILER_SELECTION_PROMPT,
        max_tokens=4096,
    )

    selected_numbers = llm_result.selectedSceneNumbers
    logger.info(f"Selected scenes for trailer: {selected_numbers}")

    # Reorder: selected scenes get order 1..N, others get N+1..
    selected_scenes = []
    for i, scene_num in enumerate(selected_numbers, start=1):
        if scene_num in scenes_by_number:
            scene = scenes_by_number[scene_num]
            scene.order = i
            selected_scenes.append(scene)

    next_order = len(selected_scenes) + 1
    for scene in scenes:
        if scene.sceneNumber not in selected_numbers:
            scene.order = next_order
            next_order += 1

    await db.commit()

    project.progress = 70
    await db.commit()

    logger.info(f"Reordered scenes: {len(selected_scenes)} trailer scenes at front")
    return selected_scenes
