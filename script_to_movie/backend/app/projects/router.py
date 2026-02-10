from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectListResponse
from app.schemas.scene import SceneResponse
from app.schemas.character import CharacterResponse
from app.schemas.setting import SettingResponse
from app.schemas.storyboard import StoryboardImageResponse
from app.schemas.video import FinalMovieResponse
from app.projects import service

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/")
async def create_project(
    body: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, int]:
    project = await service.create_project(
        db, user.id, body.title, body.description, body.scriptContent
    )
    return {"projectId": project.id}


@router.get("/")
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[ProjectListResponse]:
    projects = await service.list_projects(db, user.id)
    return [ProjectListResponse.model_validate(p) for p in projects]


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ProjectResponse:
    project = await service.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}/scenes")
async def get_scenes(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[SceneResponse]:
    project = await service.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    scenes = await service.get_project_scenes(db, project_id)
    return [SceneResponse.model_validate(s) for s in scenes]


@router.get("/{project_id}/characters")
async def get_characters(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[CharacterResponse]:
    project = await service.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    characters = await service.get_project_characters(db, project_id)
    return [CharacterResponse.model_validate(c) for c in characters]


@router.get("/{project_id}/settings")
async def get_settings(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[SettingResponse]:
    project = await service.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    settings_list = await service.get_project_settings(db, project_id)
    return [SettingResponse.model_validate(s) for s in settings_list]


@router.get("/{project_id}/storyboards")
async def get_storyboards(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[StoryboardImageResponse]:
    project = await service.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    storyboards = await service.get_project_storyboards(db, project_id)
    return [StoryboardImageResponse.model_validate(s) for s in storyboards]


@router.get("/{project_id}/movie")
async def get_movie(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> FinalMovieResponse | None:
    project = await service.get_project(db, project_id, user.id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    movie = await service.get_project_movie(db, project_id)
    if not movie:
        return None
    return FinalMovieResponse.model_validate(movie)
