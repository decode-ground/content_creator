"""
Phase 1: Script to Trailer
===========================

Orchestrates the agents that transform a raw script/plot into a structured
screenplay with visual descriptions and a trailer video.

INPUT (what exists in DB before this phase runs):
    - Project.scriptContent — raw script/plot text from user
    - Project.title — movie title

OUTPUT (what this phase creates in DB):
    - Scene records with: sceneNumber, title, description, dialogue,
      setting, characters (JSON), duration, order
    - Character records with: name, description, visualDescription
    - Setting records with: name, description, visualDescription
    - Project.trailerUrl / Project.trailerKey — generated trailer video
    - StoryboardImage records — one per scene, frames extracted from trailer
      (imageUrl, imageKey, sceneId, projectId)

STATUS UPDATES:
    - Project.status: "draft" → "parsing" → "parsed"
    - Project.progress: 0 → 33

CRITICAL REQUIREMENTS:
    - EVERY scene must include dialogue if there are spoken parts (feeds TTS in Phase 3)
    - Character visualDescriptions must be detailed and consistent across all scenes
    - EVERY scene must get exactly one StoryboardImage (Phase 3 needs it for video generation)
    - Trailer video is generated via text-to-video API using scene descriptions

The workflow orchestrator calls: await run_phase(db, project_id)
"""
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm_client
from app.models.project import Project
from app.models.scene import Scene
from app.models.character import Character
from app.models.setting import Setting
from app.phases.script_to_trailer.prompts import (
    SCRIPT_ANALYSIS_SYSTEM_PROMPT,
    ScriptAnalysisOutput,
)

logger = logging.getLogger(__name__)


async def run_phase(db: AsyncSession, project_id: int) -> dict:
    """
    Execute all Phase 1 agents in sequence.

    1. ScriptAnalysisAgent — parse script into scenes with dialogue
    2. CharacterConsistencyAgent — generate character visual descriptions
    3. SettingConsistencyAgent — generate setting visual descriptions
    4. TrailerGenerationAgent — generate trailer video, extract one frame per scene

    If any agent fails, update project.status = "failed" and
    project.errorMessage with the error detail.
    """
    raise NotImplementedError("Phase 1 service not yet implemented")


async def analyze_script(db: AsyncSession, project_id: int) -> dict:
    """Analyze a project's script content using Claude and store the results.

    Takes the project's title + scriptContent, sends them to Claude with the
    universal prompt, and stores the extracted scenes, characters, and settings.
    """
    # 1. Fetch project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # 2. Update status to parsing
    project.status = "parsing"
    project.progress = 10
    await db.commit()

    try:
        # 3. Call Claude with the universal prompt
        user_message = f"Title: {project.title}\n\nContent:\n{project.scriptContent}"

        analysis: ScriptAnalysisOutput = await llm_client.invoke_structured(
            messages=[{"role": "user", "content": user_message}],
            output_schema=ScriptAnalysisOutput,
            system=SCRIPT_ANALYSIS_SYSTEM_PROMPT,
            max_tokens=8192,
        )

        # 4. Update project's script content with the enriched version
        project.scriptContent = analysis.script
        project.progress = 40
        await db.commit()

        # 5. Store characters
        for char in analysis.characters:
            db_character = Character(
                projectId=project_id,
                name=char.name,
                description=char.description,
                visualDescription=char.visualDescription,
            )
            db.add(db_character)
        await db.commit()
        project.progress = 60
        await db.commit()

        # 6. Store settings
        for setting in analysis.settings:
            db_setting = Setting(
                projectId=project_id,
                name=setting.name,
                description=setting.description,
                visualDescription=setting.visualDescription,
            )
            db.add(db_setting)
        await db.commit()
        project.progress = 80
        await db.commit()

        # 7. Store scenes
        for scene in analysis.scenes:
            db_scene = Scene(
                projectId=project_id,
                sceneNumber=scene.sceneNumber,
                title=scene.title,
                description=scene.description,
                setting=scene.setting,
                characters=json.dumps(scene.characters),
                duration=scene.duration,
                order=scene.sceneNumber - 1,
            )
            db.add(db_scene)
        await db.commit()

        # 8. Update status to parsed
        project.status = "parsed"
        project.progress = 100
        project.errorMessage = None
        await db.commit()

        logger.info(
            "Script analysis complete for project %d: %d scenes, %d characters, %d settings",
            project_id,
            len(analysis.scenes),
            len(analysis.characters),
            len(analysis.settings),
        )

        return {
            "success": True,
            "sceneCount": len(analysis.scenes),
            "characterCount": len(analysis.characters),
            "settingCount": len(analysis.settings),
        }

    except Exception as e:
        logger.error("Script analysis failed for project %d: %s", project_id, str(e))
        project.status = "failed"
        project.progress = 0
        project.errorMessage = str(e)
        await db.commit()
        raise


async def run_character_consistency(db: AsyncSession, project_id: int) -> dict:
    """Generate consistent character visual descriptions. Creates Character records."""
    raise NotImplementedError("Phase 1: character consistency not yet implemented")


async def run_setting_consistency(db: AsyncSession, project_id: int) -> dict:
    """Generate consistent setting visual descriptions. Creates Setting records."""
    raise NotImplementedError("Phase 1: setting consistency not yet implemented")


async def run_trailer_generation(db: AsyncSession, project_id: int) -> dict:
    """Generate trailer video and extract one frame per scene. Creates StoryboardImage records."""
    raise NotImplementedError("Phase 1: trailer generation not yet implemented")
