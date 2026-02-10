# Phase 3: Storyboard to Movie -- Task Plan

## Overview

You are building Phase 3 of the Script-to-Movie pipeline. Your job is to take each scene's storyboard image and description, generate a video clip for each scene, add dialogue audio via text-to-speech, and assemble everything into the final full movie.

**You read Phase 1 and 2's output from the database. Your output is the final movie.**

---

## Current State of Your Directory

```
app/phases/storyboard_to_movie/
|-- __init__.py            <-- Empty
|-- router.py              <-- API endpoints (DONE - 4 endpoints wired up)
|-- service.py             <-- Service contract (DONE - method signatures with NotImplementedError)
|-- prompts.py             <-- YOU CREATE THIS (LLM prompt strings)
|-- video_generator.py     <-- YOU CREATE THIS (video generation API interface)
+-- agents/
    |-- __init__.py        <-- Empty
    |-- video_prompt.py    <-- YOU CREATE THIS
    |-- video_generation.py<-- YOU CREATE THIS
    +-- video_assembly.py  <-- YOU CREATE THIS
```

### What's Already Done For You

- **`router.py`** has 4 working endpoints:
  - `POST /{project_id}/prompts` -- calls `run_video_prompts()`
  - `POST /{project_id}/generate` -- calls `run_video_generation()`
  - `POST /{project_id}/assemble` -- calls `run_video_assembly()`
  - `GET /{project_id}/status` -- calls `get_generation_status()`

- **`service.py`** has method signatures that currently raise `NotImplementedError`. You replace the `raise` with actual implementation.

---

## Tasks (in order)

### Task 1: Create `prompts.py`

- [ ] Write system prompt for generating video motion descriptions from scene descriptions
- [ ] The prompt should instruct the LLM to describe:
  - Camera movement (pan, zoom, tracking shot, etc.)
  - Subject motion (walking, gesturing, etc.)
  - Mood and atmosphere
  - Lighting and visual style

### Task 2: Create `video_generator.py`

- [ ] Create abstract `VideoGenerator` base class with `generate(prompt, image_url, duration) -> bytes`
- [ ] Create `PlaceholderVideoGenerator` that raises `NotImplementedError`
- [ ] (Later) Implement a real generator using your chosen API

**Video generation API options (image-to-video):**
- Runway Gen-3: Best quality, image-to-video support
- Kling AI: Good quality, reasonable cost
- Replicate (SVD, etc.): Cost-effective, many models

**Important:** The storyboard image is the VISUAL REFERENCE (what the video should look like). The scene description is the TEXT PROMPT (what motion/action to add). Both must be sent to the API.

### Task 3: Create `agents/video_prompt.py`

- [ ] Create `VideoPromptAgent` class that inherits from `BaseAgent`
- [ ] Define Pydantic output schema for structured LLM responses
- [ ] Implement `execute()` method:
  - Read all Scene records for this project (ordered by `Scene.order`)
  - For each scene, ask Claude to generate an optimized video prompt
  - Create `VideoPrompt` records in the database

**What to write to the database:**
```python
VideoPrompt(
    sceneId=scene.id,
    projectId=project_id,
    prompt="Camera slowly pans across rain-soaked alley. Detective Harris steps forward...",
    duration=scene.duration or 10,
    style="cinematic, film noir, moody lighting",
)
```

### Task 4: Create `agents/video_generation.py`

- [ ] Create `VideoGenerationAgent` class that inherits from `BaseAgent`
- [ ] Implement `execute()` method:
  - Read scenes, their VideoPrompts, and their StoryboardImages
  - For each scene:
    - Get the storyboard image URL (visual reference)
    - Get the video prompt text
    - Call `video_generator.generate(prompt=..., image_url=...)`
    - Upload the generated video to S3
    - Create `GeneratedVideo` records in the database

**What to write to the database:**
```python
GeneratedVideo(
    sceneId=scene.id,
    projectId=project_id,
    videoUrl=video_url,
    videoKey=f"projects/{project_id}/videos/scene_{scene.sceneNumber}.mp4",
    duration=clip_duration,
    status="completed",
)
```

### Task 5: Create `agents/video_assembly.py`

This is the most complex agent. It handles TTS audio generation and final movie assembly.

- [ ] Create `VideoAssemblyAgent` class that inherits from `BaseAgent`
- [ ] Implement TTS (text-to-speech) generation:
  - For each scene with dialogue, generate audio from `scene.dialogue`
  - Consider using different voices for different characters
- [ ] Implement video + audio combining:
  - For each scene, merge the generated video clip with its TTS audio
  - Handle audio-video duration mismatch (pad shorter media with silence, or adjust speed)
- [ ] Implement final assembly:
  - Concatenate all scene videos in order (by `Scene.order`)
  - Export as MP4, H.264 codec, 1080p (1920x1080), 24fps
  - Upload final movie to S3
  - Create `FinalMovie` record
  - Update project status to "completed" and progress to 100

**TTS API options:**
- OpenAI TTS: `pip install openai` -- `client.audio.speech.create()`
- ElevenLabs: `pip install elevenlabs` -- high-quality voice cloning
- Google Cloud TTS: `pip install google-cloud-texttospeech`

**Video assembly options:**
```python
# MoviePy (easier to use)
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

clip = VideoFileClip("scene_1.mp4")
audio = AudioFileClip("scene_1_dialogue.mp3")
clip_with_audio = clip.set_audio(audio)
final = concatenate_videoclips([clip1, clip2, clip3])
final.write_videofile("final_movie.mp4", codec="libx264", fps=24)

# ffmpeg-python (more control)
import ffmpeg
ffmpeg.input("scene_1.mp4").output("output.mp4", vcodec="libx264", acodec="aac").run()
```

**What to write to the database:**
```python
FinalMovie(
    projectId=project_id,
    movieUrl=movie_url,
    movieKey=f"projects/{project_id}/final_movie.mp4",
    duration=total_duration,
    status="completed",
)

project.status = "completed"
project.progress = 100
```

### Task 6: Wire up `service.py`

- [ ] Import your agents and video generator
- [ ] Implement `run_video_prompts()` -- create VideoPromptAgent, call `agent.safe_execute()`
- [ ] Implement `run_video_generation()` -- create VideoGenerationAgent, call `agent.safe_execute()`
- [ ] Implement `run_video_assembly()` -- create VideoAssemblyAgent, call `agent.safe_execute()`
- [ ] Implement `run_phase()` -- call all 3 methods in sequence
- [ ] Implement `get_generation_status()` -- count completed videos vs. total scenes

### Task 7: Add dependencies

- [ ] Add your chosen packages to `backend/pyproject.toml`:
  ```toml
  # Video processing (pick one)
  "moviepy>=1.0.3",        # Easier API
  # OR
  "ffmpeg-python>=0.2.0",  # More control

  # TTS (pick one)
  "openai>=1.0.0",         # OpenAI TTS
  # OR
  "elevenlabs>=0.2.0",     # ElevenLabs

  # Video generation API (pick one)
  "replicate>=0.15.0",     # Replicate
  "httpx>=0.26.0",         # Direct HTTP API calls
  ```

- [ ] Install FFmpeg on your system: `brew install ffmpeg` (macOS)

### Task 8: Test everything

- [ ] Make sure Phase 1 and 2 data exists in the database first
- [ ] Test `POST /{project_id}/prompts` -- verify VideoPrompt records created
- [ ] Test `POST /{project_id}/generate` -- verify GeneratedVideo records created
- [ ] Test `POST /{project_id}/assemble` -- verify FinalMovie record created
- [ ] Test `GET /{project_id}/status` -- verify progress reporting
- [ ] Verify the final movie plays correctly and has audio

---

## Key Things to Get Right

1. **Image-to-video: the storyboard image is the VISUAL REFERENCE.** The video should look like the storyboard frame but with motion added. The scene description is the TEXT PROMPT that describes what motion/action to show.

2. **TTS from Scene.dialogue.** Every scene with dialogue must have generated audio. Parse the dialogue field to extract character lines (format: `CHARACTER_NAME: spoken line`).

3. **Audio-video sync.** TTS audio duration may differ from video duration. Options:
   - Generate video to match audio duration
   - Speed up/slow down audio to match video
   - Pad shorter media with silence

4. **Scene order.** Assemble scenes using `Scene.order` field. The final movie must play scenes in the correct sequence.

5. **Output format.** MP4, H.264 codec, 1080p (1920x1080), 24fps for broad playback compatibility.

---

## Reference

- See `base_agent.py` for a complete example agent with the read-process-write pattern
- See your `README.md` for detailed code examples, database queries, and assembly patterns
- See `backend/CLAUDE.md` for how to use the database, LLM client, and S3 storage
