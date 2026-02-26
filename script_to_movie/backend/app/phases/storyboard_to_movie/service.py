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
import json
import logging

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm_client
from app.models.project import Project
from app.models.scene import Scene
from app.models.character import Character
from app.models.setting import Setting
from app.models.video import VideoPrompt, GeneratedVideo
from app.models.final_movie import FinalMovie
from app.phases.storyboard_to_movie.agents.video_assembly import assemble_final_movie
from app.phases.storyboard_to_movie.agents.video_generation import VideoGenerationAgent
from app.phases.storyboard_to_movie.agents.video_prompt import VideoPromptAgent
from app.phases.storyboard_to_movie.prompts import (
    VIDEO_PROMPT_SYSTEM_PROMPT,
    VideoPromptOutput,
)
from app.phases.storyboard_to_movie.video_generator import (
    VideoClip,
    generate_video_clip,
    assemble_trailer,
)

logger = logging.getLogger(__name__)


async def run_phase(db: AsyncSession, project_id: int) -> dict:
    """Execute all Phase 3 steps in sequence."""
    results: dict = {}

    r = await run_video_prompts(db, project_id)
    results["prompts"] = r
    if r.get("status") == "error":
        return {"status": "error", "phase": "prompts", "message": r.get("message"), "results": results}

    r = await run_video_generation(db, project_id)
    results["generation"] = r
    if r.get("status") == "error":
        return {"status": "error", "phase": "generation", "message": r.get("message"), "results": results}

    r = await run_video_assembly(db, project_id)
    results["assembly"] = r

    return {"status": r.get("status", "unknown"), "results": results}


async def generate_trailer(db: AsyncSession, project_id: int) -> dict:
    """Generate a fast-paced multi-scene trailer by creating a 5-second clip for every
    scene and concatenating them with ffmpeg into one continuous video.
    """
    # 1. Fetch project and verify it's been parsed
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    if project.status not in ("parsed", "generating_videos", "completed", "failed"):
        raise ValueError(
            f"Project must be parsed before generating trailer. Current status: {project.status}"
        )

    # 2. Clean up old records from previous runs
    await db.execute(delete(GeneratedVideo).where(GeneratedVideo.projectId == project_id))
    await db.execute(delete(VideoPrompt).where(VideoPrompt.projectId == project_id))
    await db.execute(delete(FinalMovie).where(FinalMovie.projectId == project_id))
    await db.commit()

    # 3. Update status
    project.status = "generating_videos"
    project.progress = 5
    await db.commit()

    try:
        # 4. Fetch scenes, characters, settings
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

        character_map = {c.name: c for c in characters}
        setting_map = {s.name: s for s in settings}
        total_scenes = len(scenes)

        logger.info(
            "Generating trailer for project %d: %d scenes × 5s clips",
            project_id,
            total_scenes,
        )

        # Phase A: Generate per-scene video prompts via Claude (fast, sequential)
        video_prompts_by_scene: list[tuple] = []

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
                f"{setting_description or 'No specific setting description'}"
            )

            video_prompt: VideoPromptOutput = await llm_client.invoke_structured(
                messages=[{"role": "user", "content": user_message}],
                output_schema=VideoPromptOutput,
                system=VIDEO_PROMPT_SYSTEM_PROMPT,
                max_tokens=1024,
            )

            db_video_prompt = VideoPrompt(
                sceneId=scene.id,
                projectId=project_id,
                prompt=video_prompt.prompt,
                duration=5,  # always 5s for fast-paced trailer cuts
                style=f"{video_prompt.style} | {video_prompt.cameraMovement}",
            )
            db.add(db_video_prompt)
            await db.commit()

            video_prompts_by_scene.append((scene, video_prompt))

            project.progress = int(((i + 1) / total_scenes) * 30) + 5
            await db.commit()

        logger.info(
            "All %d prompts generated for project %d — generating clips sequentially",
            total_scenes,
            project_id,
        )
        project.progress = 35
        await db.commit()

        # Phase B: Generate one 5-second clip per scene, sequentially
        clips: list[VideoClip] = []

        for i, (scene, vp) in enumerate(video_prompts_by_scene):
            logger.info(
                "Generating clip %d/%d for project %d (scene %d)",
                i + 1, total_scenes, project_id, scene.id,
            )
            clip = await generate_video_clip(
                prompt=vp.prompt,
                duration=5,
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

            clips.append(clip)

            project.progress = 35 + int(((i + 1) / total_scenes) * 55)
            await db.commit()

        project.progress = 90
        await db.commit()

        # Phase C: Concatenate all clips into one trailer with ffmpeg
        logger.info(
            "Assembling trailer for project %d from %d clips",
            project_id,
            len(clips),
        )
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

        project.status = "completed"
        project.progress = 100
        project.errorMessage = None
        await db.commit()

        logger.info(
            "Trailer complete for project %d: %d clips, %ds total at %s",
            project_id,
            len(clips),
            trailer.totalDuration,
            trailer.movieUrl,
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
    return await VideoPromptAgent().safe_execute(db, project_id)


async def run_video_generation(db: AsyncSession, project_id: int) -> dict:
    """Generate video clips using storyboard images as references. Creates GeneratedVideo records."""
    return await VideoGenerationAgent().safe_execute(db, project_id)


async def run_tts_generation(db: AsyncSession, project_id: int) -> dict:
    """TTS is handled inside VideoAssemblyAgent. This stub kept for API compatibility."""
    return {"status": "success", "message": "TTS is handled during /assemble step"}


async def run_video_assembly(db: AsyncSession, project_id: int) -> dict:
    """Combine video + audio per scene, then assemble final movie. Creates FinalMovie record."""
    return await assemble_final_movie(db, project_id)


async def get_generation_status(db: AsyncSession, project_id: int) -> dict:
    """Return current generation status for the project."""
    from app.models.storyboard import StoryboardImage
    from app.models.video import VideoPrompt, GeneratedVideo
    from app.models.final_movie import FinalMovie

    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        return {"status": "error", "message": f"Project {project_id} not found"}

    total_scenes = (
        await db.execute(
            select(Scene).where(Scene.projectId == project_id)
        )
    )
    total_scenes_count = len(total_scenes.scalars().all())

    prompts_result = await db.execute(
        select(VideoPrompt).where(VideoPrompt.projectId == project_id)
    )
    prompts_count = len(prompts_result.scalars().all())

    videos_result = await db.execute(
        select(GeneratedVideo).where(
            GeneratedVideo.projectId == project_id,
            GeneratedVideo.status == "completed",
        )
    )
    videos_count = len(videos_result.scalars().all())

    movie_result = await db.execute(
        select(FinalMovie).where(FinalMovie.projectId == project_id)
    )
    movie = movie_result.scalar_one_or_none()

    return {
        "project_id": project_id,
        "project_status": project.status,
        "project_progress": project.progress,
        "total_scenes": total_scenes_count,
        "prompts_generated": prompts_count,
        "videos_generated": videos_count,
        "movie_assembled": movie is not None,
        "movie_url": movie.movieUrl if movie else None,
    }
