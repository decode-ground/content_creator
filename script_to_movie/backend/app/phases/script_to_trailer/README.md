# Phase 1: Script to Trailer — Developer Guide

## What This Phase Does

Takes a movie title and script/plot text from the user, and:
1. Breaks the script into a full screenplay with individual scenes (including all dialogue)
2. Generates detailed, consistent visual descriptions for every character
3. Generates detailed, consistent visual descriptions for every setting/location
4. Generates a trailer video using a text-to-video API
5. Extracts one key frame from the trailer for each scene

## How It Fits in the Pipeline

```
User uploads script/plot
         ↓
    ┌─────────────┐
    │  THIS PHASE  │  ← You are here
    └──────┬──────┘
           ↓
    What you produce:
    • Scene records (with dialogue)
    • Character records (with visual descriptions)
    • Setting records (with visual descriptions)
    • Trailer video
    • One storyboard frame per scene
           ↓
    ┌─────────────────────┐
    │ Phase 2: Storyboard │  ← Reads your scenes + frames
    └──────┬──────────────┘
           ↓
    ┌─────────────────────┐
    │ Phase 3: Full Movie │  ← Uses your frames for video generation
    └─────────────────────┘
```

## Your Input (What to Read from DB)

```python
from sqlalchemy import select
from app.models.project import Project

result = await db.execute(select(Project).where(Project.id == project_id))
project = result.scalar_one_or_none()

# project.title — movie title
# project.scriptContent — the raw script/plot text from the user
```

## Your Output (What to Write to DB)

### 1. Scene Records
```python
from app.models.scene import Scene
import json

scene = Scene(
    projectId=project_id,
    sceneNumber=1,
    title="The Dark Alley",
    description="A dimly lit alley in downtown Chicago at night. Rain falls on wet cobblestones...",
    dialogue="DETECTIVE HARRIS: (whispering) Stay behind me.\nSARAH: What did you see?",
    setting="Downtown Chicago - Dark Alley",
    characters=json.dumps(["Detective Harris", "Sarah"]),
    duration=45,  # estimated seconds
    order=1,
)
db.add(scene)
```

### 2. Character Records
```python
from app.models.character import Character

character = Character(
    projectId=project_id,
    name="Detective Harris",
    description="A weathered homicide detective in his late 40s, haunted by an unsolved case.",
    visualDescription="Male, late 40s, short graying brown hair, square jaw with stubble, "
        "tired dark brown eyes with crow's feet, wearing a rumpled dark gray trench coat "
        "over a white dress shirt with loosened navy tie, medium build, 5'11\", "
        "carries a worn leather shoulder holster",
)
db.add(character)
```

### 3. Setting Records
```python
from app.models.setting import Setting

setting = Setting(
    projectId=project_id,
    name="Downtown Chicago - Dark Alley",
    description="A narrow alley between two brick buildings in a rough neighborhood.",
    visualDescription="Narrow urban alley, wet red brick walls, dim yellow streetlight "
        "at far end, overflowing dumpster, fire escape ladders, puddles reflecting "
        "neon signs from the street, steam rising from a manhole, nighttime, "
        "film noir lighting with hard shadows",
)
db.add(setting)
```

### 4. Trailer Video
```python
from app.models.project import Project
from app.core.storage import storage_client

# After generating trailer video bytes from text-to-video API:
trailer_url = await storage_client.upload(
    key=f"projects/{project_id}/trailer.mp4",
    data=trailer_video_bytes,
    content_type="video/mp4",
)

# Update project
project.trailerUrl = trailer_url
project.trailerKey = f"projects/{project_id}/trailer.mp4"
await db.commit()
```

### 5. Storyboard Frames (one per scene)
```python
from app.models.storyboard import StoryboardImage

# After extracting frames from the trailer video:
for scene in scenes:
    frame_url = await storage_client.upload(
        key=f"projects/{project_id}/frames/scene_{scene.sceneNumber}.png",
        data=frame_bytes,
        content_type="image/png",
    )
    storyboard = StoryboardImage(
        sceneId=scene.id,
        projectId=project_id,
        imageUrl=frame_url,
        imageKey=f"projects/{project_id}/frames/scene_{scene.sceneNumber}.png",
        prompt=f"Frame for scene {scene.sceneNumber}: {scene.description[:200]}",
        status="completed",
    )
    db.add(storyboard)
```

### 6. Update Project Status
```python
project.status = "parsed"
project.progress = 33
await db.commit()
```

## Your Files (Implement in This Order)

| # | File | What It Does |
|---|------|-------------|
| 1 | `prompts.py` | All LLM prompt strings for script parsing, character/setting descriptions |
| 2 | `agents/script_analysis.py` | Parses script → creates Scene records with dialogue |
| 3 | `agents/character_consistency.py` | Reads scenes → creates Character records with visual descriptions |
| 4 | `agents/setting_consistency.py` | Reads scenes → creates Setting records with visual descriptions |
| 5 | `agents/trailer_generation.py` | Generates trailer video via text-to-video API, extracts frames |
| 6 | `service.py` | Calls agents in sequence, updates project status |

**Note:** Rename `agents/trailer_selection.py` to `agents/trailer_generation.py` — the name better reflects what it does.

## Step-by-Step Implementation Guide

### Step 1: Define Your LLM Output Schemas

In your agent files, define Pydantic models for what you want Claude to return:

```python
from pydantic import BaseModel

class ExtractedScene(BaseModel):
    title: str
    description: str  # visual description of what happens
    dialogue: str     # all spoken lines, formatted as "CHARACTER: line"
    setting: str      # location name
    characters: list[str]  # character names in this scene
    estimated_duration: int  # seconds

class ScriptBreakdown(BaseModel):
    scenes: list[ExtractedScene]
```

### Step 2: Implement ScriptAnalysisAgent

```python
from app.phases.base_agent import BaseAgent

class ScriptAnalysisAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "script_analysis"

    async def execute(self, db, project_id):
        # 1. Read project.scriptContent
        # 2. Call self.llm.invoke_structured() with ScriptBreakdown schema
        # 3. Create Scene records from the result
        # 4. Return {"status": "success", "scenes_created": N}
```

See the example agent in `base_agent.py` for the complete pattern.

### Step 3: Implement Character/Setting Agents

These agents READ the Scene records you just created and generate visual descriptions:
- Read all scenes → extract unique character names → ask Claude for detailed visual descriptions → create Character records
- Same pattern for settings

### Step 4: Implement Trailer Generation

1. Build a text prompt from all scene descriptions
2. Call a text-to-video API to generate a trailer
3. Extract one frame per scene from the video (using ffmpeg/moviepy)
4. Upload trailer + frames to S3
5. Create StoryboardImage records

### Step 5: Wire Up service.py

Your `service.py` already has method signatures. Implement them by instantiating and calling each agent:

```python
from app.phases.script_to_trailer.agents.script_analysis import ScriptAnalysisAgent

async def run_script_analysis(db, project_id):
    agent = ScriptAnalysisAgent()
    return await agent.safe_execute(db, project_id)
```

## Critical Requirements

1. **EVERY scene must have dialogue** if there are spoken parts. Phase 3 uses `Scene.dialogue` to generate TTS audio. If you skip dialogue, the movie will be silent.

2. **Character visualDescriptions must be detailed and consistent.** These descriptions are used by Phase 2 and 3 to maintain visual consistency across all generated images and videos. Include: age, gender, hair, eye color, build, clothing, distinguishing features.

3. **EVERY scene must get exactly one StoryboardImage.** Phase 3 uses these images as visual references for video generation. A scene without a frame = no video for that scene.

4. **Visual descriptions should be image-generation-friendly.** Write them as if they're image prompts: specific, visual, descriptive. Avoid abstract concepts.

## Testing Your Work

```bash
# 1. Start the server
cd backend && uvicorn app.main:app --reload

# 2. Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@test.com","name":"Dev","password":"password123"}'
# Save the session cookie from the response

# 3. Create a project with a script
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -b "session=YOUR_TOKEN" \
  -d '{"title":"Test Movie","scriptContent":"Your test script here..."}'

# 4. Run script analysis
curl -X POST http://localhost:8000/api/phases/script-to-trailer/1/analyze \
  -b "session=YOUR_TOKEN"

# 5. Verify scenes were created
curl http://localhost:8000/api/projects/1/scenes -b "session=YOUR_TOKEN"

# 6. Run character/setting generation
curl -X POST http://localhost:8000/api/phases/script-to-trailer/1/characters \
  -b "session=YOUR_TOKEN"
curl -X POST http://localhost:8000/api/phases/script-to-trailer/1/settings \
  -b "session=YOUR_TOKEN"

# 7. Verify
curl http://localhost:8000/api/projects/1/characters -b "session=YOUR_TOKEN"
curl http://localhost:8000/api/projects/1/settings -b "session=YOUR_TOKEN"
```

## Reference

The old TypeScript implementation is at `server/agents/ScriptAnalysisAgent.ts` — it shows the same multi-step LLM pattern but in TypeScript. The Python equivalent uses `self.llm.invoke_structured()` instead of `structuredLLMCall()`.
