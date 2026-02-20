# Phase 3: Storyboard to Full Movie — Developer Guide

## What This Phase Does

Takes each scene's storyboard image and description, and:
1. Generates optimized video prompts from scene descriptions
2. Generates a video clip for each scene using image-to-video generation (storyboard image as visual reference, scene description as text prompt)
3. Generates TTS (text-to-speech) audio from each scene's dialogue
4. Combines video + audio per scene
5. Assembles all scene videos into the final full movie

## How It Fits in the Pipeline

```
    ┌─────────────────────┐
    │ Phase 1: Script     │  ← Created scenes with dialogue
    └──────┬──────────────┘
           ↓
    ┌─────────────────────┐
    │ Phase 2: Storyboard │  ← Validated/enhanced frames
    └──────┬──────────────┘
           ↓
    What you receive:
    • Scene records (description, dialogue, characters, setting, duration, order)
    • StoryboardImage records (one per scene, with imageUrl)
           ↓
    ┌─────────────┐
    │  THIS PHASE  │  ← You are here
    └──────┬──────┘
           ↓
    What you produce:
    • Video clip per scene (with TTS audio)
    • Final assembled full movie (MP4)
```

## Your Input (What to Read from DB)

```python
from sqlalchemy import select
from app.models.scene import Scene
from app.models.storyboard import StoryboardImage

# Get all scenes in order
result = await db.execute(
    select(Scene)
    .where(Scene.projectId == project_id)
    .order_by(Scene.order)
)
scenes = result.scalars().all()
# Each scene has:
#   .description — visual description of the scene (use as video prompt)
#   .dialogue — spoken lines (use for TTS audio generation)
#   .characters — JSON string of character names
#   .setting — location name
#   .duration — estimated duration in seconds
#   .order — scene sequence number

# Get storyboard frames (one per scene)
result = await db.execute(
    select(StoryboardImage).where(StoryboardImage.projectId == project_id)
)
frames = result.scalars().all()
# Each frame has:
#   .sceneId — links to the scene
#   .imageUrl — S3 URL of the storyboard image (use as image reference for video gen)
#   .status — should be "completed"
```

## Your Output (What to Write to DB)

### 1. Video Prompt Records

```python
from app.models.video import VideoPrompt

video_prompt = VideoPrompt(
    sceneId=scene.id,
    projectId=project_id,
    prompt="Camera slowly pans across a rain-soaked alley. Detective Harris steps forward...",
    duration=scene.duration or 10,
    style="cinematic, film noir, moody lighting",
)
db.add(video_prompt)
```

### 2. Generated Video Records

```python
from app.models.video import GeneratedVideo
from app.core.storage import storage_client

# After generating video from API:
video_url = await storage_client.upload(
    key=f"projects/{project_id}/videos/scene_{scene.sceneNumber}.mp4",
    data=video_bytes,
    content_type="video/mp4",
)

generated_video = GeneratedVideo(
    sceneId=scene.id,
    projectId=project_id,
    videoUrl=video_url,
    videoKey=f"projects/{project_id}/videos/scene_{scene.sceneNumber}.mp4",
    duration=clip_duration,
    status="completed",
)
db.add(generated_video)
```

### 3. Final Movie Record

```python
from app.models.final_movie import FinalMovie

movie_url = await storage_client.upload(
    key=f"projects/{project_id}/final_movie.mp4",
    data=final_movie_bytes,
    content_type="video/mp4",
)

final_movie = FinalMovie(
    projectId=project_id,
    movieUrl=movie_url,
    movieKey=f"projects/{project_id}/final_movie.mp4",
    duration=total_duration,
    status="completed",
)
db.add(final_movie)
```

### 4. Update Project Status

```python
project.status = "completed"
project.progress = 100
await db.commit()
```

## Your Files (Implement in This Order)

| # | File | What It Does |
|---|------|-------------|
| 1 | `prompts.py` | LLM prompts for generating video motion descriptions |
| 2 | `agents/video_prompt.py` | Creates optimized video gen prompts from scene descriptions |
| 3 | `video_generator.py` | Abstract interface for video generation API + placeholder |
| 4 | `agents/video_generation.py` | Calls video API with storyboard image + prompt |
| 5 | `agents/video_assembly.py` | TTS generation + video+audio combining + final assembly |
| 6 | `service.py` | Calls agents in sequence, updates project status |

## Step-by-Step Implementation Guide

### Step 1: Create the Video Generator Interface

In `video_generator.py`:

```python
from abc import ABC, abstractmethod


class VideoGenerator(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        duration: int = 5,
    ) -> bytes:
        """
        Generate a video clip.

        Args:
            prompt: Text description of the scene/motion
            image_url: URL of the reference image (storyboard frame)
            duration: Desired clip duration in seconds

        Returns:
            Video bytes (MP4)
        """
        ...


class PlaceholderVideoGenerator(VideoGenerator):
    async def generate(self, prompt, image_url=None, duration=5):
        raise NotImplementedError("Connect a real video generation API here")
```

When ready, implement with your chosen API:
- **Runway Gen-3**: Best quality, image-to-video support
- **Kling AI**: Good quality, reasonable cost
- **Replicate (SVD/etc.)**: Cost-effective, many models

### Step 2: Implement Video Prompt Agent

This agent takes scene descriptions and creates optimized prompts for video generation:

```python
from app.phases.base_agent import BaseAgent
from pydantic import BaseModel


class VideoPromptOutput(BaseModel):
    motion_description: str  # camera movement + subject motion
    style_guidance: str      # cinematic style, lighting, mood
    duration: int            # clip duration in seconds


class VideoPromptAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "video_prompt"

    async def execute(self, db, project_id):
        # 1. Load scenes
        # 2. For each scene, ask Claude to generate a video prompt:
        #    - Describe camera movement (pan, zoom, tracking shot)
        #    - Describe subject motion (walking, gesturing, etc.)
        #    - Include mood and atmosphere
        # 3. Create VideoPrompt records
        # 4. Return summary
```

### Step 3: Implement Video Generation Agent

```python
class VideoGenerationAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "video_generation"

    async def execute(self, db, project_id):
        # 1. Load scenes + their VideoPrompts + their StoryboardImages
        # 2. For each scene:
        #    - Get the storyboard image URL (visual reference)
        #    - Get the video prompt text
        #    - Call video_generator.generate(prompt=..., image_url=...)
        #    - Upload video to S3
        #    - Create GeneratedVideo record
        # 3. Update project status to "generating_videos"
```

### Step 4: Implement Video Assembly Agent

This is the most complex agent. It handles TTS and final assembly:

```python
class VideoAssemblyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "video_assembly"

    async def execute(self, db, project_id):
        # 1. Load scenes (ordered) + their GeneratedVideo records
        # 2. For each scene with dialogue:
        #    - Generate TTS audio from scene.dialogue
        #    - Combine video + audio for that scene
        # 3. Concatenate all scene videos in order
        # 4. Upload final movie to S3
        # 5. Create FinalMovie record
        # 6. Update project status to "completed", progress to 100
```

**TTS Options:**
- **OpenAI TTS**: `pip install openai` → `client.audio.speech.create()`
- **ElevenLabs**: `pip install elevenlabs` → high-quality voice cloning
- **Google Cloud TTS**: `pip install google-cloud-texttospeech`

**Video Assembly Options (choose one):**
```python
# MoviePy (easier)
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

clip = VideoFileClip("scene_1.mp4")
audio = AudioFileClip("scene_1_dialogue.mp3")
clip_with_audio = clip.set_audio(audio)
final = concatenate_videoclips([clip1, clip2, clip3])
final.write_videofile("final_movie.mp4", codec="libx264", fps=24)

# ffmpeg-python (more control)
import ffmpeg
(
    ffmpeg
    .input("scene_1.mp4")
    .output("output.mp4", vcodec="libx264", acodec="aac")
    .run()
)
```

### Step 5: Wire Up service.py

```python
async def run_phase(db, project_id):
    # 1. Run VideoPromptAgent
    # 2. Run VideoGenerationAgent
    # 3. Run VideoAssemblyAgent (includes TTS + assembly)
    # 4. Update project to completed
```

## Critical Requirements

1. **Image-to-video**: The storyboard image is the VISUAL REFERENCE. The scene description is the TEXT PROMPT. Both must be sent to the video generation API. The video should look like the storyboard frame but with motion.

2. **TTS from Scene.dialogue**: Every scene with dialogue must have generated audio. Parse the dialogue field to extract character lines. Consider different voices for different characters.

3. **Audio-video sync**: The TTS audio duration may differ from the video duration. Options:
   - Generate video to match audio duration
   - Speed up/slow down audio to match video
   - Pad shorter clips with silence

4. **Scene order**: Assemble scenes using `Scene.order` field. The final movie should play scenes in the correct sequence.

5. **Output format**: MP4, H.264 codec, 1080p (1920x1080), 24fps. This ensures broad playback compatibility.

6. **FFmpeg required**: You'll need FFmpeg installed on the system for video processing. `brew install ffmpeg` on macOS.

## Testing Your Work

Before testing Phase 3, you need Phase 1 and 2 data. You can either:
- Run Phases 1 and 2 first
- Manually insert Scene + StoryboardImage records with real image URLs

```bash
# Generate video prompts
curl -X POST http://localhost:8000/api/phases/storyboard-to-movie/1/prompts \
  -b "session=YOUR_TOKEN"

# Generate videos
curl -X POST http://localhost:8000/api/phases/storyboard-to-movie/1/generate \
  -b "session=YOUR_TOKEN"

# Assemble final movie
curl -X POST http://localhost:8000/api/phases/storyboard-to-movie/1/assemble \
  -b "session=YOUR_TOKEN"

# Check status
curl http://localhost:8000/api/phases/storyboard-to-movie/1/status \
  -b "session=YOUR_TOKEN"

# Get the final movie
curl http://localhost:8000/api/projects/1/movie -b "session=YOUR_TOKEN"
```

## Dependencies

### System dependency (must be installed separately)

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

ffmpeg is used by `agents/video_assembly.py` to merge TTS audio into video clips and to concatenate all scene clips into the final movie.

### Python packages

Add these to `backend/pyproject.toml` when you're ready:

```toml
"gTTS>=2.3.0",           # Text-to-speech (used by video assembly)
"httpx>=0.26.0",         # Async HTTP for downloading clips / calling APIs

# Video generation API (pick one)
"replicate>=0.15.0",     # Replicate (many models)
```

## Reference

See `AGENT_ARCHITECTURE.md` in the project root for the overall agent design patterns.
