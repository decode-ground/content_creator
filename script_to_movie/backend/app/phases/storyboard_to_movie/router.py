from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.phases.storyboard_to_movie import service

router = APIRouter(prefix="/api/phases/storyboard-to-movie", tags=["storyboard-to-movie"])


@router.post("/{project_id}/prompts")
async def generate_video_prompts(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Generate optimized video prompts from scene descriptions."""
    return await service.run_video_prompts(db, project_id)


@router.post("/{project_id}/generate")
async def generate_videos(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Generate video clips using storyboard images as references."""
    return await service.run_video_generation(db, project_id)


@router.post("/{project_id}/assemble")
async def assemble_movie(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Combine video + TTS audio per scene and assemble final movie."""
    return await service.run_video_assembly(db, project_id)


@router.get("/{project_id}/status")
async def get_status(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Check video generation and assembly status."""
    return await service.get_generation_status(db, project_id)
