from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.phases.trailer_to_storyboard import service

router = APIRouter(prefix="/api/phases/trailer-to-storyboard", tags=["trailer-to-storyboard"])


@router.post("/{project_id}/generate")
async def generate_storyboards(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Validate and regenerate storyboard frames for each scene."""
    return await service.run_generate_storyboards(db, project_id)


@router.get("/{project_id}/status")
async def get_status(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Check storyboard generation status."""
    return await service.get_generation_status(db, project_id)
