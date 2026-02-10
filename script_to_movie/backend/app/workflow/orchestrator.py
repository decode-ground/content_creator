"""
Workflow Orchestrator
=====================

Runs the full 3-phase pipeline sequentially for a given project.
Each phase service exposes a run_phase(db, project_id) function.

The orchestrator:
1. Calls Phase 1 run_phase (script → scenes/characters/settings + trailer + frames)
2. Calls Phase 2 run_phase (validates/enhances storyboard frames)
3. Calls Phase 3 run_phase (generates videos + TTS + assembles final movie)

It updates project.status and project.progress between phases.
If any phase fails, it stops and marks the project as failed.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.phases.script_to_trailer.service import run_phase as run_phase_1
from app.phases.trailer_to_storyboard.service import run_phase as run_phase_2
from app.phases.storyboard_to_movie.service import run_phase as run_phase_3


async def run_full_pipeline(db: AsyncSession, project_id: int) -> dict:
    """
    Run all 3 phases sequentially.

    Progress: 0 → 33 (after Phase 1) → 66 (after Phase 2) → 100 (after Phase 3)
    Status: draft → parsing → parsed → generating_storyboard → generating_videos → assembling → completed
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return {"status": "error", "message": "Project not found"}

    phases = [
        ("Phase 1: Script to Trailer", run_phase_1),
        ("Phase 2: Trailer to Storyboard", run_phase_2),
        ("Phase 3: Storyboard to Movie", run_phase_3),
    ]

    for phase_name, run_phase in phases:
        phase_result = await run_phase(db, project_id)
        if phase_result.get("status") == "error":
            project.status = "failed"
            project.errorMessage = f"{phase_name} failed: {phase_result.get('message')}"
            await db.commit()
            return {"status": "error", "message": project.errorMessage}

    return {"status": "success", "message": "Full pipeline completed"}
