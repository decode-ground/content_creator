from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_user
from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectListResponse
from app.projects import service

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def _get_user_id(
    db: Annotated[AsyncSession, Depends(get_db)],
    session: Annotated[str | None, Cookie()] = None,
) -> int | None:
    if not session:
        return None
    user = await get_current_user(db, session)
    return user.id if user else None


@router.post("", response_model=dict)
async def create_project(
    data: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int | None, Depends(_get_user_id)] = None,
):
    project = await service.create_project(db, data, user_id or 1)
    return {"projectId": project.id}


@router.get("", response_model=list[ProjectListResponse])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int | None, Depends(_get_user_id)] = None,
):
    return await service.list_projects(db, user_id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
