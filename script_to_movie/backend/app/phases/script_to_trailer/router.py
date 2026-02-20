from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.phases.script_to_trailer.service import analyze_script, run_phase1
from app.phases.script_to_trailer.agents.script_analysis import analyze_script as agent_analyze_script
from app.phases.script_to_trailer.agents.character_consistency import extract_characters
from app.phases.script_to_trailer.agents.setting_consistency import extract_settings
from app.phases.script_to_trailer.agents.trailer_selection import select_trailer_scenes

router = APIRouter(prefix="/api/phases/script-to-trailer", tags=["script-to-trailer"])


async def _get_project(project_id: int, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


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
async def characters_endpoint(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await _get_project(project_id, db)
    characters = await extract_characters(db, project)
    return {"success": True, "charactersCount": len(characters)}


@router.post("/{project_id}/settings")
async def settings_endpoint(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await _get_project(project_id, db)
    settings = await extract_settings(db, project)
    return {"success": True, "settingsCount": len(settings)}


@router.post("/{project_id}/select-scenes")
async def select_scenes_endpoint(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await _get_project(project_id, db)
    selected = await select_trailer_scenes(db, project)
    return {"success": True, "selectedCount": len(selected)}


@router.post("/{project_id}/run-all")
async def run_all_endpoint(project_id: int, db: AsyncSession = Depends(get_db)):
    await run_phase1(db, project_id)
    return {"success": True, "status": "phase1_complete"}
