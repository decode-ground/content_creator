import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.project import Project
from app.workflow.service import start_workflow

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class StartWorkflowRequest(BaseModel):
    workflowType: str = "full_pipeline"


@router.post("/{project_id}/start")
async def start_workflow_endpoint(
    project_id: int,
    body: StartWorkflowRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status not in ("draft", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start workflow: project status is '{project.status}'",
        )

    project.status = "starting"
    project.progress = 0
    project.errorMessage = None
    await db.commit()

    asyncio.create_task(start_workflow(project_id, body.workflowType))

    return {"success": True, "message": "Workflow started"}


@router.get("/{project_id}/status")
async def get_workflow_status(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "projectId": project.id,
        "status": project.status,
        "progress": project.progress,
        "errorMessage": project.errorMessage,
    }
