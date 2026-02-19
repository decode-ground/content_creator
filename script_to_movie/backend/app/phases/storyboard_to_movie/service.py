"""
Phase 3: Storyboard to Full Movie
====================================

Orchestrates the agents that generate video clips from storyboard frames,
add TTS audio for dialogue, and assemble the final movie.

INPUT (what must exist in DB before this phase runs):
    - Scene records (description, dialogue, characters, setting, duration, order)
    - StoryboardImage records (one per scene, with imageUrl and status="completed")

OUTPUT (what this phase creates in DB):
    - VideoPrompt records (sceneId, projectId, prompt, duration, style)
    - GeneratedVideo records (sceneId, projectId, videoUrl, videoKey, duration, status)
    - FinalMovie record (projectId, movieUrl, movieKey, duration, status)

STATUS UPDATES:
    - Project.status: "generating_storyboard" → "generating_videos" → "assembling" → "completed"
    - Project.progress: 66 → 100

CRITICAL REQUIREMENTS:
    - Image-to-video: storyboard image is the VISUAL REFERENCE, scene description is the TEXT PROMPT
    - TTS: Generate audio from Scene.dialogue for each scene (ElevenLabs, OpenAI TTS, or similar)
    - Audio sync: TTS audio duration should inform video clip duration
    - Assembly: Combine video + audio per scene, then concatenate all scenes in order
    - Output: MP4, H.264, 1080p, 24fps

The workflow orchestrator calls: await run_phase(db, project_id)
"""
import asyncio
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm_client
from app.models.project import Project
from app.models.scene import Scene
from app.models.character import Character
from app.models.setting import Setting
from app.models.video import VideoPrompt, GeneratedVideo
from app.models.final_movie import FinalMovie
from app.phases.storyboard_to_movie.prompts import (
    VIDEO_PROMPT_SYSTEM_PROMPT,
    VideoPromptOutput,
)
from app.phases.storyboard_to_movie.video_generator import (
    generate_video_clip,
    assemble_trailer,
)

logger = logging.getLogger(__name__)


async def run_phase(db: AsyncSession, project_id: int) -> dict:
    """
    Execute Phase 3.

    1. Load scenes + storyboard images
    2. For each scene: generate video prompt from scene description
    3. For each scene: call video API with storyboard image + prompt
    4. For each scene: generate TTS audio from dialogue
    5. Combine video + audio per scene
    6. Assemble all scenes into final movie
    7. Upload to S3, create FinalMovie record
    8. Update project status to "completed", progress to 100
    """
    raise NotImplementedError("Phase 3 service not yet implemented")


async def generate_trailer(db: AsyncSession, project_id: int) -> dict:
    """Generate a video trailer from a parsed script.

    Takes the project's scenes, characters, and settings (produced by Phase 1),
    generates optimized video prompts for each scene using Claude, creates
    video clips, and assembles them into a final trailer.
    """
    # 1. Fetch project and verify it's been parsed
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    if project.status not in ("parsed", "completed", "failed"):
        raise ValueError(
            f"Project must be parsed before generating trailer. Current status: {project.status}"
        )

    # 2. Update status
    project.status = "generating_videos"
    project.progress = 5
    await db.commit()

    try:
        # 3. Fetch scenes, characters, settings
        scenes_result = await db.execute(
            select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
        )
        scenes = list(scenes_result.scalars().all())

        characters_result = await db.execute(
            select(Character).where(Character.projectId == project_id)
        )
        characters = list(characters_result.scalars().all())

        settings_result = await db.execute(
            select(Setting).where(Setting.projectId == project_id)
        )
        settings = list(settings_result.scalars().all())

        if not scenes:
            raise ValueError("No scenes found — run Parse Script first")

        # Build lookup maps
        character_map = {c.name: c for c in characters}
        setting_map = {s.name: s for s in settings}

        total_scenes = len(scenes)

        # Phase A: Generate all video prompts (sequential — uses Claude LLM)
        video_prompts_by_scene = []

        for i, scene in enumerate(scenes):
            scene_characters = json.loads(scene.characters or "[]")
            char_descriptions = "\n".join(
                f"- {name}: {character_map[name].visualDescription}"
                for name in scene_characters
                if name in character_map and character_map[name].visualDescription
            )

            setting_obj = setting_map.get(scene.setting or "")
            setting_description = ""
            if setting_obj and setting_obj.visualDescription:
                setting_description = f"Setting: {setting_obj.name}\n{setting_obj.visualDescription}"

            user_message = (
                f"Scene {scene.sceneNumber}: {scene.title}\n\n"
                f"Description: {scene.description}\n\n"
                f"Characters present:\n{char_descriptions or 'No specific characters'}\n\n"
                f"{setting_description or 'No specific setting description'}\n\n"
                f"Scene duration target: {scene.duration or 8} seconds"
            )

            video_prompt: VideoPromptOutput = await llm_client.invoke_structured(
                messages=[{"role": "user", "content": user_message}],
                output_schema=VideoPromptOutput,
                system=VIDEO_PROMPT_SYSTEM_PROMPT,
                max_tokens=2048,
            )

            db_video_prompt = VideoPrompt(
                sceneId=scene.id,
                projectId=project_id,
                prompt=video_prompt.prompt,
                duration=video_prompt.duration,
                style=f"{video_prompt.style} | {video_prompt.cameraMovement}",
            )
            db.add(db_video_prompt)
            await db.commit()

            video_prompts_by_scene.append((scene, video_prompt))

            project.progress = int(((i + 1) / total_scenes) * 40) + 5
            await db.commit()

        logger.info(
            "All %d video prompts generated for project %d — submitting to Kling in parallel",
            total_scenes,
            project_id,
        )
        project.progress = 45
        await db.commit()

        # Phase B: Generate all video clips in PARALLEL (all Kling tasks run simultaneously)
        async def _generate_and_store(scene: Scene, vp: VideoPromptOutput) -> VideoClip:
            clip = await generate_video_clip(
                prompt=vp.prompt,
                duration=vp.duration,
                project_id=project_id,
                scene_id=scene.id,
            )
            db_video = GeneratedVideo(
                sceneId=scene.id,
                projectId=project_id,
                videoUrl=clip.videoUrl,
                videoKey=clip.videoKey,
                duration=clip.duration,
                status="completed",
            )
            db.add(db_video)
            await db.commit()
            return clip

        clips = await asyncio.gather(
            *[_generate_and_store(scene, vp) for scene, vp in video_prompts_by_scene]
        )
        clips = list(clips)

        project.progress = 90
        await db.commit()

        # 6. Assemble trailer from clips
        trailer = await assemble_trailer(clips, project_id)

        db_movie = FinalMovie(
            projectId=project_id,
            movieUrl=trailer.movieUrl,
            movieKey=trailer.movieKey,
            duration=trailer.totalDuration,
            status="completed",
        )
        db.add(db_movie)
        await db.commit()

        # 7. Update project status
        project.status = "completed"
        project.progress = 100
        project.errorMessage = None
        await db.commit()

        logger.info(
            "Trailer generation complete for project %d: %d clips, %ds total",
            project_id,
            len(clips),
            trailer.totalDuration,
        )

        return {
            "success": True,
            "trailerUrl": trailer.movieUrl,
            "totalDuration": trailer.totalDuration,
            "clipCount": len(clips),
        }

    except Exception as e:
        logger.error("Trailer generation failed for project %d: %s", project_id, str(e))
        project.status = "failed"
        project.progress = 0
        project.errorMessage = str(e)
        await db.commit()
        raise


async def run_video_prompts(db: AsyncSession, project_id: int) -> dict:
    """Generate optimized video prompts from scene descriptions. Creates VideoPrompt records."""
    raise NotImplementedError("Phase 3: video prompts not yet implemented")


async def run_video_generation(db: AsyncSession, project_id: int) -> dict:
    """Generate video clips using storyboard images as references. Creates GeneratedVideo records."""
    raise NotImplementedError("Phase 3: video generation not yet implemented")


async def run_tts_generation(db: AsyncSession, project_id: int) -> dict:
    """Generate TTS audio from Scene.dialogue for each scene."""
    raise NotImplementedError("Phase 3: TTS generation not yet implemented")


async def run_video_assembly(db: AsyncSession, project_id: int) -> dict:
    """Combine video + audio per scene, then assemble final movie. Creates FinalMovie record."""
    raise NotImplementedError("Phase 3: video assembly not yet implemented")


async def get_generation_status(db: AsyncSession, project_id: int) -> dict:
    """Return current generation status for the project."""
    raise NotImplementedError("Phase 3: status check not yet implemented")
