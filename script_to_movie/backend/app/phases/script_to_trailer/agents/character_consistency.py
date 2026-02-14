import json
import logging

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.llm import llm_client
from app.models.project import Project
from app.models.scene import Scene
from app.models.character import Character
from app.phases.script_to_trailer.prompts import CHARACTER_CONSISTENCY_PROMPT

logger = logging.getLogger(__name__)


class CharacterData(BaseModel):
    name: str
    description: str
    visualDescription: str


class CharacterConsistencyResult(BaseModel):
    characters: list[CharacterData]


async def extract_characters(db: AsyncSession, project: Project) -> list[Character]:
    logger.info(f"Starting character extraction for project {project.id}")

    # Get existing scenes
    result = await db.execute(
        select(Scene).where(Scene.projectId == project.id).order_by(Scene.sceneNumber)
    )
    scenes = result.scalars().all()

    scenes_text = "\n".join(
        f"Scene {s.sceneNumber} ({s.title}): {s.description} [Characters: {s.characters}]"
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
        output_schema=CharacterConsistencyResult,
        system=CHARACTER_CONSISTENCY_PROMPT,
        max_tokens=8192,
    )

    logger.info(f"Extracted {len(llm_result.characters)} characters")

    characters = []
    for char_data in llm_result.characters:
        character = Character(
            projectId=project.id,
            name=char_data.name,
            description=char_data.description,
            visualDescription=char_data.visualDescription,
        )
        db.add(character)
        characters.append(character)

    await db.commit()

    for character in characters:
        await db.refresh(character)

    project.progress = 30
    await db.commit()

    logger.info(f"Saved {len(characters)} characters for project {project.id}")
    return characters
