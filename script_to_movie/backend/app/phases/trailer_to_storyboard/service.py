"""
Phase 2: Trailer to Storyboard
================================

Downloads the trailer video produced by Phase 1, extracts candidate frames
for each scene using ffmpeg, and uses Claude Vision to select the best frame
per scene. Every selected frame is stored as a StoryboardImage record for
Phase 3 to use as a visual reference for video generation.

INPUT (what must exist in DB before this phase runs):
    - Project with trailerKey set (trailer video uploaded to S3 by Phase 1)
    - Scene records (description, dialogue, characters, setting, duration, order)
    - Character records with visualDescription
    - Setting records with visualDescription

OUTPUT (what this phase creates in DB):
    - StoryboardImage records (one per scene, status="completed" or "failed")

STATUS UPDATES:
    - Project.status: "phase1_complete" → "generating_storyboard"
    - Project.progress: 33 → 66

The workflow orchestrator calls: await run_phase(db, project_id)
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.scene import Scene
from app.models.storyboard import StoryboardImage
from app.phases.trailer_to_storyboard.agents.storyboard_prompt import StoryboardPromptAgent

logger = logging.getLogger(__name__)


async def run_phase(db: AsyncSession, project_id: int) -> dict:
    """Execute Phase 2 — called by the workflow orchestrator."""
    return await run_generate_storyboards(db, project_id)


async def run_generate_storyboards(db: AsyncSession, project_id: int) -> dict:
    """Extract and select storyboard frames from the trailer. Called by the phase router."""
    # Update project status
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        return {"status": "error", "message": f"Project {project_id} not found"}

    project.status = "generating_storyboard"
    project.progress = 40
    await db.commit()

    try:
        result = await StoryboardPromptAgent().safe_execute(db, project_id)

        if result.get("status") in ("success", "partial"):
            project.progress = 66
        else:
            project.status = "failed"
            project.errorMessage = result.get("message", "Storyboard generation failed")

        await db.commit()
        return result

    except Exception as e:
        logger.error("Phase 2 failed for project %d: %s", project_id, e)
        project.status = "failed"
        project.errorMessage = str(e)
        await db.commit()
        raise


async def get_generation_status(db: AsyncSession, project_id: int) -> dict:
    """Return current storyboard generation status for the project."""
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        return {"status": "error", "message": f"Project {project_id} not found"}

    scenes_result = await db.execute(
        select(Scene).where(Scene.projectId == project_id)
    )
    total_scenes = len(scenes_result.scalars().all())

    frames_result = await db.execute(
        select(StoryboardImage).where(StoryboardImage.projectId == project_id)
    )
    all_frames = frames_result.scalars().all()
    completed = sum(1 for f in all_frames if f.status == "completed")
    failed = sum(1 for f in all_frames if f.status == "failed")

    return {
        "project_id": project_id,
        "project_status": project.status,
        "project_progress": project.progress,
        "total_scenes": total_scenes,
        "frames_completed": completed,
        "frames_failed": failed,
        "frames_pending": total_scenes - len(all_frames),
    }
