"""
Phase 1: Script to Trailer
===========================

Orchestrates the agents that transform a raw script/plot into a structured
screenplay with visual descriptions and a trailer video.

INPUT (what exists in DB before this phase runs):
    - Project.scriptContent — raw script/plot text from user
    - Project.title — movie title

OUTPUT (what this phase creates in DB):
    - Scene records with: sceneNumber, title, description, dialogue,
      setting, characters (JSON), duration, order
    - Character records with: name, description, visualDescription
    - Setting records with: name, description, visualDescription
    - Project.trailerUrl / Project.trailerKey — generated trailer video
    - StoryboardImage records — one per scene, frames extracted from trailer
      (imageUrl, imageKey, sceneId, projectId)

STATUS UPDATES:
    - Project.status: "draft" → "parsing" → "parsed"
    - Project.progress: 0 → 33

CRITICAL REQUIREMENTS:
    - EVERY scene must include dialogue if there are spoken parts (feeds TTS in Phase 3)
    - Character visualDescriptions must be detailed and consistent across all scenes
    - EVERY scene must get exactly one StoryboardImage (Phase 3 needs it for video generation)
    - Trailer video is generated via text-to-video API using scene descriptions

The workflow orchestrator calls: await run_phase(db, project_id)
"""
from sqlalchemy.ext.asyncio import AsyncSession


async def run_phase(db: AsyncSession, project_id: int) -> dict:
    """
    Execute all Phase 1 agents in sequence.

    1. ScriptAnalysisAgent — parse script into scenes with dialogue
    2. CharacterConsistencyAgent — generate character visual descriptions
    3. SettingConsistencyAgent — generate setting visual descriptions
    4. TrailerGenerationAgent — generate trailer video, extract one frame per scene

    If any agent fails, update project.status = "failed" and
    project.errorMessage with the error detail.
    """
    raise NotImplementedError("Phase 1 service not yet implemented")


async def run_script_analysis(db: AsyncSession, project_id: int) -> dict:
    """Parse script into scenes with dialogue. Creates Scene records."""
    raise NotImplementedError("Phase 1: script analysis not yet implemented")


async def run_character_consistency(db: AsyncSession, project_id: int) -> dict:
    """Generate consistent character visual descriptions. Creates Character records."""
    raise NotImplementedError("Phase 1: character consistency not yet implemented")


async def run_setting_consistency(db: AsyncSession, project_id: int) -> dict:
    """Generate consistent setting visual descriptions. Creates Setting records."""
    raise NotImplementedError("Phase 1: setting consistency not yet implemented")


async def run_trailer_generation(db: AsyncSession, project_id: int) -> dict:
    """Generate trailer video and extract one frame per scene. Creates StoryboardImage records."""
    raise NotImplementedError("Phase 1: trailer generation not yet implemented")
