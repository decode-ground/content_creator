"""Workflow service — wraps orchestrator, manages background execution."""
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.project import Project

logger = logging.getLogger(__name__)


async def _run_pipeline(project_id: int) -> None:
    """Run the full pipeline in a background task with its own DB session."""
    from app.phases.script_to_trailer.service import analyze_script
    from app.phases.storyboard_to_movie.service import generate_trailer
    from app.phases.trailer_to_storyboard.service import run_generate_storyboards

    async with AsyncSessionLocal() as db:
        try:
            # Check current status to skip completed phases
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            current_status = project.status if project else "draft"

            # Phase 1: Parse script (skip if already parsed)
            if current_status in ("draft", "parsing", "failed"):
                logger.info("Starting Phase 1 (script analysis) for project %d", project_id)
                await analyze_script(db, project_id)

            # Phase 3: Generate trailer videos
            logger.info("Starting Phase 3 (trailer generation) for project %d", project_id)
            await generate_trailer(db, project_id)

            # Phase 2: Extract storyboard frames from the generated trailer
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            if project and project.trailerKey:
                logger.info("Starting Phase 2 (storyboard extraction) for project %d", project_id)
                await run_generate_storyboards(db, project_id)
                # Restore completed status after Phase 2 finishes
                result = await db.execute(select(Project).where(Project.id == project_id))
                project = result.scalar_one_or_none()
                if project:
                    project.status = "completed"
                    project.progress = 100
                    await db.commit()

            logger.info("Pipeline complete for project %d", project_id)
        except Exception as e:
            logger.error("Pipeline failed for project %d: %s", project_id, e)
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            if project:
                project.status = "failed"
                project.errorMessage = str(e)
                await db.commit()


async def start_workflow(project_id: int, workflow_type: str) -> None:
    """Start the full pipeline: Parse Script → Generate Trailer with Kling AI.

    Delegates to _run_pipeline which handles Phase 1 (Claude script analysis)
    and Phase 3 (Kling AI video generation) in sequence.
    """
    logger.info(f"Workflow '{workflow_type}' starting for project {project_id}")
    await _run_pipeline(project_id)
