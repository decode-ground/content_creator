"""Workflow service — wraps orchestrator, manages background execution."""
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.schemas.video import WorkflowStatusResponse

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


async def start_workflow(db: AsyncSession, project_id: int, workflow_type: str) -> dict:
    """Start the pipeline as a background task. Returns immediately."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Launch pipeline in background so the HTTP response returns immediately
    asyncio.create_task(_run_pipeline(project_id))
    return {"success": True}


async def get_workflow_status(db: AsyncSession, project_id: int) -> WorkflowStatusResponse:
    """Return current workflow status for a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return WorkflowStatusResponse(
            projectId=project_id,
            status="not_found",
            progress=0,
            error="Project not found",
        )
    return WorkflowStatusResponse(
        projectId=project.id,
        status=project.status,
        progress=project.progress,
        error=project.errorMessage,
    )


async def pause_workflow(db: AsyncSession, project_id: int) -> None:
    raise NotImplementedError("Workflow pause not yet implemented")


async def resume_workflow(db: AsyncSession, project_id: int) -> None:
    raise NotImplementedError("Workflow resume not yet implemented")
