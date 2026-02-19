from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.phases.script_to_trailer.service import analyze_script
from app.phases.script_to_trailer import service

router = APIRouter(prefix="/api/phases/script-to-trailer", tags=["script-to-trailer"])


@router.post("/{project_id}/analyze")
async def analyze_project_script(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Parse a project's script content and extract scenes, characters, and settings."""
    try:
        result = await analyze_script(db, project_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script analysis failed: {str(e)}")


@router.post("/{project_id}/characters")
async def generate_characters(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Generate consistent character visual descriptions."""
    return await service.run_character_consistency(db, project_id)


@router.post("/{project_id}/settings")
async def generate_settings(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Generate consistent setting visual descriptions."""
    return await service.run_setting_consistency(db, project_id)


@router.post("/{project_id}/trailer")
async def generate_trailer(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Generate trailer video and extract one frame per scene."""
    return await service.run_trailer_generation(db, project_id)
