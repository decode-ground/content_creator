"""Workflow service — wraps orchestrator, manages background execution."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.video import WorkflowStatusResponse


async def start_workflow(db: AsyncSession, project_id: int, workflow_type: str) -> dict:
    """Start the pipeline. Returns {"success": True}."""
    raise NotImplementedError("Workflow start not yet implemented")


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
