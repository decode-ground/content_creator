"""
Phase 2: Trailer to Storyboard
================================

Orchestrates the agents that validate and enhance trailer frames into a
structured movie storyboard.

INPUT (what must exist in DB before this phase runs):
    - Project with status="parsed"
    - Scene records (description, dialogue, characters, setting, order)
      via: select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
    - Character records with visualDescription
    - Setting records with visualDescription
    - StoryboardImage records (one per scene, from Phase 1's trailer frame extraction)

OUTPUT (what this phase creates/updates in DB):
    - Updated StoryboardImage records (validated, possibly regenerated with
      better prompts if frames don't adequately depict their scenes)

STATUS UPDATES:
    - Project.status: "parsed" → "generating_storyboard"
    - Project.progress: 33 → 66

CRITICAL REQUIREMENTS:
    - Validate every scene has exactly one StoryboardImage — flag missing ones
    - Each storyboard frame must visually depict its scene well enough to serve
      as an image reference for video generation in Phase 3
    - If a frame poorly represents its scene, regenerate it using an image
      generation API with a prompt incorporating character/setting visualDescriptions

The workflow orchestrator calls: await run_phase(db, project_id)
"""
from sqlalchemy.ext.asyncio import AsyncSession


async def run_phase(db: AsyncSession, project_id: int) -> dict:
    """
    Execute Phase 2.

    1. Load all scenes and their StoryboardImage records
    2. Validate scene-to-frame mapping (every scene has one image)
    3. Evaluate if each frame adequately depicts its scene
    4. Regenerate poor frames using image generation API
    5. Update project status and progress
    """
    raise NotImplementedError("Phase 2 service not yet implemented")


async def run_generate_storyboards(db: AsyncSession, project_id: int) -> dict:
    """Validate and regenerate storyboard frames. Called by the phase router."""
    raise NotImplementedError("Phase 2: storyboard generation not yet implemented")


async def get_generation_status(db: AsyncSession, project_id: int) -> dict:
    """Return current generation status for the project."""
    raise NotImplementedError("Phase 2: status check not yet implemented")
