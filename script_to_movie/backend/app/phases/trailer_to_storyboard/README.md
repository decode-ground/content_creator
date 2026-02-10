# Phase 2: Trailer to Storyboard — Developer Guide

## What This Phase Does

Takes the scenes, character/setting descriptions, and trailer frames produced by Phase 1, and organizes them into a validated movie storyboard. Ensures every scene has a corresponding frame that adequately depicts it. If a frame is missing or poor quality, regenerates it using an image generation API.

## How It Fits in the Pipeline

```
    ┌─────────────────────┐
    │ Phase 1: Script     │
    └──────┬──────────────┘
           ↓
    What Phase 1 gives you:
    • Scene records (description, dialogue, characters, setting)
    • Character records (with visualDescription)
    • Setting records (with visualDescription)
    • StoryboardImage records (one frame per scene, from trailer)
           ↓
    ┌─────────────┐
    │  THIS PHASE  │  ← You are here
    └──────┬──────┘
           ↓
    What you produce:
    • Validated/enhanced StoryboardImage records
    • Every scene paired with a quality frame
           ↓
    ┌─────────────────────┐
    │ Phase 3: Full Movie │  ← Uses your frames as image references
    └─────────────────────┘      for video generation
```

## Your Input (What to Read from DB)

```python
from sqlalchemy import select
from app.models.scene import Scene
from app.models.character import Character
from app.models.setting import Setting
from app.models.storyboard import StoryboardImage

# Get all scenes in order
result = await db.execute(
    select(Scene)
    .where(Scene.projectId == project_id)
    .order_by(Scene.order)
)
scenes = result.scalars().all()
# Each scene has: .description, .dialogue, .setting, .characters (JSON string)

# Get character visual descriptions
result = await db.execute(
    select(Character).where(Character.projectId == project_id)
)
characters = result.scalars().all()
# Each character has: .name, .visualDescription

# Get setting visual descriptions
result = await db.execute(
    select(Setting).where(Setting.projectId == project_id)
)
settings = result.scalars().all()
# Each setting has: .name, .visualDescription

# Get existing storyboard frames (from Phase 1)
result = await db.execute(
    select(StoryboardImage).where(StoryboardImage.projectId == project_id)
)
frames = result.scalars().all()
# Each frame has: .sceneId, .imageUrl, .imageKey, .prompt, .status
```

## Your Output (What to Write/Update in DB)

### 1. Validate Scene-to-Frame Mapping

```python
# Build a map of scene_id -> frame
frame_map = {f.sceneId: f for f in frames}

for scene in scenes:
    if scene.id not in frame_map:
        # MISSING FRAME — must generate one
        # Use image generation API with scene + character + setting descriptions
        pass
```

### 2. Regenerate Poor Frames

If a frame doesn't adequately depict its scene, regenerate it:

```python
from app.core.storage import storage_client

# Generate a better image prompt using Claude
prompt = await self.llm.invoke(
    messages=[{
        "role": "user",
        "content": f"Create an image generation prompt for this scene:\n"
            f"Scene: {scene.description}\n"
            f"Characters: {character_descriptions}\n"
            f"Setting: {setting_description}\n"
            f"Make it cinematic, 16:9 aspect ratio, detailed lighting and composition."
    }],
    system="You are an expert at writing image generation prompts for cinematic storyboards.",
)

# Call your image generation API
image_bytes = await image_generator.generate(prompt)

# Upload to S3
image_url = await storage_client.upload(
    key=f"projects/{project_id}/storyboard/scene_{scene.sceneNumber}.png",
    data=image_bytes,
    content_type="image/png",
)

# Update the StoryboardImage record
frame.imageUrl = image_url
frame.imageKey = f"projects/{project_id}/storyboard/scene_{scene.sceneNumber}.png"
frame.prompt = prompt
frame.status = "completed"
await db.commit()
```

### 3. Update Project Status

```python
from sqlalchemy import select
from app.models.project import Project

result = await db.execute(select(Project).where(Project.id == project_id))
project = result.scalar_one_or_none()
project.status = "generating_storyboard"
project.progress = 66
await db.commit()
```

## Your Files (Implement in This Order)

| # | File | What It Does |
|---|------|-------------|
| 1 | `prompts.py` | LLM prompts for evaluating frames and generating image prompts |
| 2 | `agents/storyboard_prompt.py` | Evaluates frame-scene match, generates optimized image prompts |
| 3 | `image_generator.py` | Abstract interface for image generation API + placeholder |
| 4 | `service.py` | Orchestrates validation and regeneration |

## Step-by-Step Implementation Guide

### Step 1: Create the Image Generator Interface

In `image_generator.py`, define an abstract interface so you can swap APIs later:

```python
from abc import ABC, abstractmethod


class ImageGenerator(ABC):
    @abstractmethod
    async def generate(self, prompt: str, width: int = 1024, height: int = 576) -> bytes:
        """Generate an image from a prompt. Returns image bytes."""
        ...


class PlaceholderImageGenerator(ImageGenerator):
    """Returns a placeholder for testing until a real API is connected."""
    async def generate(self, prompt: str, width: int = 1024, height: int = 576) -> bytes:
        # For testing: return a minimal 1x1 PNG or download a placeholder
        # Replace this with a real API (DALL-E, Flux, Stable Diffusion, etc.)
        raise NotImplementedError("Connect a real image generation API here")
```

When you're ready, implement a real generator:
- **DALL-E 3**: `pip install openai` → use `AsyncOpenAI().images.generate()`
- **Replicate (Flux/SDXL)**: `pip install replicate` → use `replicate.async_run()`
- **Any HTTP API**: `pip install httpx` → make async HTTP calls

### Step 2: Implement the Storyboard Prompt Agent

This agent does two things:
1. **Evaluates** if each trailer frame adequately depicts its scene
2. **Generates** better image prompts when regeneration is needed

The key is incorporating character and setting visual descriptions into the prompt to maintain consistency.

```python
from app.phases.base_agent import BaseAgent

class StoryboardPromptAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "storyboard_prompt"

    async def execute(self, db, project_id):
        # 1. Load scenes, characters, settings, frames
        # 2. For each scene, check if it has a frame
        # 3. If missing or poor, generate an optimized image prompt:
        #    - Include scene description
        #    - Include relevant character visualDescriptions
        #    - Include setting visualDescription
        #    - Add cinematic style guidance
        # 4. Return list of scenes needing regeneration with their prompts
```

### Step 3: Wire Up service.py

```python
async def run_generate_storyboards(db, project_id):
    # 1. Run StoryboardPromptAgent to identify and create prompts
    # 2. For scenes needing regeneration, call image_generator
    # 3. Upload new images to S3
    # 4. Update StoryboardImage records
    # 5. Update project status
```

## Critical Requirements

1. **Every scene must have exactly one StoryboardImage.** Phase 3 uses these as visual references for video generation. Validate this — if Phase 1 missed any, generate them here.

2. **Frames must visually depict their scenes.** A generic or unrelated frame will produce poor video in Phase 3. The image should match the scene's setting, characters, and action.

3. **Use character/setting visualDescriptions in image prompts.** This is how visual consistency is maintained. Always include the relevant character appearances and setting details from Phase 1.

4. **16:9 aspect ratio** for video compatibility (1024x576 or 1920x1080).

## Testing Your Work

Before testing Phase 2, you need Phase 1 data in the database. You can either:
- Run Phase 1 first (if implemented)
- Manually insert test Scene + Character + Setting + StoryboardImage records

```bash
# Check storyboard frames for a project
curl http://localhost:8000/api/projects/1/storyboards -b "session=YOUR_TOKEN"

# Run storyboard generation/validation
curl -X POST http://localhost:8000/api/phases/trailer-to-storyboard/1/generate \
  -b "session=YOUR_TOKEN"

# Check status
curl http://localhost:8000/api/phases/trailer-to-storyboard/1/status \
  -b "session=YOUR_TOKEN"

# Verify updated storyboards
curl http://localhost:8000/api/projects/1/storyboards -b "session=YOUR_TOKEN"
```

## Reference

See `AGENT_ARCHITECTURE.md` in the project root for the overall agent design patterns.
