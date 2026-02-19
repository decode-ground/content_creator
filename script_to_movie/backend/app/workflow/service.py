"""Workflow service — wraps orchestrator, manages background execution."""
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.phases.script_to_trailer.service import run_phase1

logger = logging.getLogger(__name__)


async def _run_pipeline(project_id: int) -> None:
    """Run the full pipeline in a background task with its own DB session."""
    from app.phases.script_to_trailer.service import analyze_script
    from app.phases.storyboard_to_movie.service import generate_trailer

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
    """Start the pipeline as a background task. Returns immediately.

    Uses its own DB session since it runs detached from the request lifecycle.
    Signature matches what main's workflow router expects:
        asyncio.create_task(start_workflow(project_id, body.workflowType))
    """
    logger.info(f"Workflow '{workflow_type}' starting for project {project_id}")

    async with AsyncSessionLocal() as db:
        try:
            if workflow_type == "full_pipeline":
                # Phase 1: Script to Trailer (sub-agent orchestration)
                await run_phase1(db, project_id)

                # Phase 2 & 3 will be added by other developers
                logger.info(f"Workflow complete for project {project_id}")
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

        except Exception as e:
            logger.error(f"Workflow failed for project {project_id}: {e}")
            # Error status is already set by run_phase1's error handler
