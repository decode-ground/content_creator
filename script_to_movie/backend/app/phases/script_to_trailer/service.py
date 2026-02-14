import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import Project
from app.phases.script_to_trailer.agents.script_analysis import analyze_script
from app.phases.script_to_trailer.agents.character_consistency import extract_characters
from app.phases.script_to_trailer.agents.setting_consistency import extract_settings
from app.phases.script_to_trailer.agents.trailer_selection import select_trailer_scenes

logger = logging.getLogger(__name__)


async def run_phase1(db: AsyncSession, project_id: int) -> None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    try:
        logger.info(f"Phase 1 starting for project {project_id}")

        # Step 1: Analyze script → extract scenes
        await analyze_script(db, project)

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
