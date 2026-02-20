"""
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
from app.phases.script_to_trailer.agents.script_analysis import analyze_script as agent_analyze_script
from app.phases.script_to_trailer.agents.character_consistency import extract_characters
from app.phases.script_to_trailer.agents.setting_consistency import extract_settings
from app.phases.script_to_trailer.agents.trailer_selection import select_trailer_scenes

logger = logging.getLogger(__name__)


async def run_phase1(db: AsyncSession, project_id: int) -> None:
    """Run the full Phase 1 pipeline using sub-agents.

    This is the orchestrator called by the workflow service. It delegates
    to individual agents for each step.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    try:
        logger.info(f"Phase 1 starting for project {project_id}")

        # Step 1: Analyze script → extract scenes
        await agent_analyze_script(db, project)

        # Step 2: Extract characters with visual descriptions
        await extract_characters(db, project)

        # Step 3: Extract settings with visual descriptions
        await extract_settings(db, project)

        # Step 4: Select trailer scenes
        await select_trailer_scenes(db, project)

        project.status = "phase1_complete"
        project.progress = 100
        await db.commit()

        logger.info(f"Phase 1 complete for project {project_id}")

    except Exception as e:
        logger.error(f"Phase 1 failed for project {project_id}: {e}")
        project.status = "failed"
        project.errorMessage = str(e)
        await db.commit()
        raise


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
