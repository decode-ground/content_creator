# Phase 3: Storyboard to Movie

## Role

Generates video clips from storyboard frames and assembles them into the final trailer. This is the final phase of the pipeline.

## Pipeline Position

```
[Script to Trailer] → [Trailer to Storyboard] → [THIS PHASE] → [Final Movie]
```

## Input

- Storyboard images (from Phase 2)
- Scene descriptions and durations
- Character/setting context

## Output

- Video clips for each scene
- Assembled final trailer video

## Endpoints to Implement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/phases/storyboard-to-movie/{project_id}/prompts` | POST | Generate video prompts |
| `/api/phases/storyboard-to-movie/{project_id}/generate` | POST | Generate video clips |
| `/api/phases/storyboard-to-movie/{project_id}/assemble` | POST | Assemble final trailer |
| `/api/phases/storyboard-to-movie/{project_id}/status` | GET | Check generation status |

## Files to Implement

| File | Responsibility |
|------|----------------|
| `agents/video_prompt.py` | Generate optimized video prompts |
| `agents/video_generation.py` | Handle video generation API calls |
| `agents/video_assembly.py` | Combine clips with transitions |
| `video_generator.py` | Video generation + FFmpeg assembly |
| `service.py` | Orchestrate the full video pipeline |
| `router.py` | API endpoints |

## Design Decisions

### 1. Video Generation API

Which API should power video generation from storyboard images?

| API | Pros | Cons | Cost | Duration |
|-----|------|------|------|----------|
| **Runway Gen-3 Alpha** | Highest quality, best motion | Expensive, may have waitlist | ~$0.50-2.00/video | 5-10s |
| **Pika Labs** | Good quality, accessible API | Newer, evolving API | ~$0.20-0.50/video | 3-5s |
| **Kling AI** | Long-form generation, good quality | API access varies by region | ~$0.10-0.30/video | 5-10s |
| **Luma Dream Machine** | Good motion, fast | Limited control options | ~$0.20-0.40/video | 5s |
| **Stable Video Diffusion** (Replicate) | Cost-effective, open source | Lower quality, short clips | ~$0.02-0.10/video | 2-4s |
| **Minimax** | Good quality, reasonable cost | Newer entrant | ~$0.10-0.25/video | 5-6s |

**Dependency to add** (choose one):
```toml
"replicate>=0.15.0",    # For Replicate-hosted models
"httpx>=0.26.0",        # For direct API calls to any service
"runwayml>=0.1.0",      # Official Runway SDK (if available)
```

**Questions to answer:**
- What's your budget per trailer?
- How important is motion quality vs. cost?
- What clip duration do you need?

### 2. Video Generation Approach

How should videos be generated from storyboard images?

| Approach | Description | Trade-off |
|----------|-------------|-----------|
| **Image-to-video** | Animate storyboard frames directly | Consistent with storyboards, limited motion |
| **Text-to-video** | Generate from scene descriptions only | More creative motion but less visual control |
| **Hybrid** | Image as start frame + text motion prompts | Best balance of control and motion |
| **Multi-frame interpolation** | Generate start/end frames, interpolate between | Smooth transitions, more predictable |

**Questions to answer:**
- How closely should videos match storyboard images?
- Is creative motion interpretation acceptable?

### 3. Motion/Camera Prompting

What motion elements should be included in video prompts?

| Element | Options |
|---------|---------|
| **Camera movement** | Static, pan left/right, tilt up/down, zoom in/out, dolly, tracking |
| **Subject motion** | Walking, running, gesturing, subtle breathing, dramatic action |
| **Environment motion** | Wind, rain, crowd movement, lighting changes |
| **Speed/pacing** | Slow motion, normal speed, time-lapse |
| **Atmosphere** | Mood shifts, lighting transitions |

**Questions to answer:**
- Should motion be inferred from scene descriptions or explicitly specified?
- How much camera movement is appropriate for trailers?

### 4. Video Assembly Tool

**FFmpeg is required** for combining clips. Choose a Python wrapper:

| Tool | Pros | Cons |
|------|------|------|
| **MoviePy** | Pythonic API, easy transitions, good docs | Memory-heavy for long videos |
| **ffmpeg-python** | Low-level control, memory efficient | Steeper learning curve |
| **Direct FFmpeg subprocess** | Full control, most efficient | Command-line complexity |
| **PyAV** | Fast, Pythonic FFmpeg bindings | Less documentation |

```toml
"moviepy>=1.0.3",       # Recommended for ease of use
# OR
"ffmpeg-python>=0.2.0", # For more control
```

### 5. Transitions Between Clips

What transitions should connect video clips?

| Transition | Use Case | Duration |
|------------|----------|----------|
| **Hard cut** | Fast-paced action, tension | 0s |
| **Cross-dissolve** | Scene changes, time passage | 0.5-1.5s |
| **Fade to black** | Major section breaks, dramatic pause | 0.5-1s |
| **Fade from black** | Opening, new section | 0.5-1s |
| **Wipe** | Stylistic choice, retro feel | 0.3-0.5s |
| **Motion blur** | High-energy transitions | 0.2-0.5s |

**Questions to answer:**
- Should transitions be consistent or vary by scene type?
- What's the default transition style?

### 6. Audio Integration

Should the trailer include audio?

| Option | Description | Complexity |
|--------|-------------|------------|
| **No audio** | Silent trailer, simplest approach | Low |
| **Background music** | Add royalty-free or licensed track | Medium |
| **AI-generated music** | Generate custom score (Suno, Udio, etc.) | Medium-High |
| **Ambient sound** | Generate scene-appropriate sound effects | Medium |
| **Text-to-speech** | AI narration or dialogue | Medium |
| **Full audio mix** | Music + sound effects + dialogue | High |

**Audio dependencies** (if needed):
```toml
"pydub>=0.25.0",        # Audio manipulation
```

**Questions to answer:**
- Is audio in scope for v1?
- Who provides the music (user upload vs. generated)?

### 7. Video Output Specifications

| Specification | Options | Recommendation |
|---------------|---------|----------------|
| **Resolution** | 720p, 1080p, 4K | 1080p (1920x1080) for quality/size balance |
| **Codec** | H.264, H.265, VP9 | H.264 for broad compatibility |
| **Format** | MP4, WebM, MOV | MP4 for universal playback |
| **Frame rate** | 24fps, 30fps, 60fps | 24fps for cinematic feel |
| **Bitrate** | 5-20 Mbps | 10-15 Mbps for good quality |
| **Total duration** | 30s, 60s, 90s, 2min | Depends on scene count |

### 8. Background Processing

Video generation takes 1-5 minutes per clip. **Background processing is required.**

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **FastAPI BackgroundTasks** | Built-in, simple | Single-server only, no persistence |
| **Celery + Redis** | Industry standard, distributed | Complex setup, more infrastructure |
| **ARQ** | Async-native, simpler than Celery | Less ecosystem, still needs Redis |
| **Dramatiq** | Good Celery alternative | Less common |
| **RQ (Redis Queue)** | Simple Redis-based queue | Synchronous workers |

```toml
# Choose one:
"celery>=5.3.0",        # + redis
"arq>=0.25.0",          # Async Redis queue
"dramatiq>=1.15.0",     # Alternative to Celery
```

**Questions to answer:**
- Do you need distributed processing (multiple workers)?
- Is job persistence/recovery important?
- How will you handle long-running jobs if server restarts?

### 9. Error Handling & Recovery

| Scenario | Strategy |
|----------|----------|
| **Video generation timeout** | Retry with shorter duration, or skip scene |
| **API rate limit** | Queue with delays, use multiple API keys |
| **Partial clip failure** | Generate remaining clips, mark failed for retry |
| **Assembly failure** | Keep individual clips, allow manual retry |
| **Storage upload failure** | Local fallback, retry upload later |

**Questions to answer:**
- Should failed clips block the entire trailer?
- How do you handle partial results?

## Implementation Steps

1. **Set up video generation client** in `video_generator.py`:
   ```python
   import replicate

   async def generate_video(image_url: str, prompt: str, duration: int) -> str:
       output = await replicate.async_run(
           "stability-ai/stable-video-diffusion",
           input={"image": image_url, "motion_bucket_id": 127}
       )
       return output  # Video URL
   ```

2. **Implement video prompt agent**:
   - Add motion/camera movement descriptions
   - Specify duration and pacing
   - Include audio/atmosphere guidance

3. **Implement video assembly** with moviepy:
   ```python
   from moviepy.editor import VideoFileClip, concatenate_videoclips

   def assemble_clips(clip_paths: list[str], output_path: str):
       clips = [VideoFileClip(p) for p in clip_paths]
       final = concatenate_videoclips(clips, method="compose")
       final.write_videofile(output_path, codec="libx264")
   ```

4. **Implement background task processing**:
   - Queue video generation jobs
   - Poll for completion
   - Update status in database

5. **Update project status**:
   - `generating_storyboard` → `generating_videos` → `assembling` → `completed`

## Reference

See original implementation: `script_to_movie/server/videoGenerator.ts`
