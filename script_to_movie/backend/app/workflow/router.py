from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.video import WorkflowStatusResponse
from app.workflow import service

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class StartWorkflowRequest(BaseModel):
    workflowType: str = "full_pipeline"


@router.post("/{project_id}/start")
async def start_workflow(
    project_id: int,
    body: StartWorkflowRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Start the full pipeline for a project."""
    return await service.start_workflow(db, project_id, body.workflowType)


@router.get("/{project_id}/status")
async def get_status(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> WorkflowStatusResponse:
    """Get current workflow status and progress."""
    return await service.get_workflow_status(db, project_id)


@router.post("/{project_id}/pause")
async def pause(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Pause workflow execution."""
    await service.pause_workflow(db, project_id)
    return {"message": "Workflow paused"}


@router.post("/{project_id}/resume")
async def resume(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Resume paused workflow."""
    await service.resume_workflow(db, project_id)
    return {"message": "Workflow resumed"}
