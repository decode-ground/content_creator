# CLAUDE.md — Script-to-Movie Backend

## Project Overview

This is the backend for Script-to-Movie, an AI pipeline that converts screenplays into full-length generated movies. Built with Python 3.11+, FastAPI, async SQLAlchemy, and MySQL.

The pipeline has 3 phases, each assigned to a different developer:
- **Phase 1** (`app/phases/script_to_trailer/`): Parse scripts with Claude LLM → extract scenes with dialogue → generate character/setting visual descriptions → create trailer video → extract frames
- **Phase 2** (`app/phases/trailer_to_storyboard/`): Validate scene-to-frame mapping → enhance/regenerate poor frames → produce quality storyboard
- **Phase 3** (`app/phases/storyboard_to_movie/`): Image-to-video generation → TTS audio from dialogue → assemble full movie

## Quick Start

```bash
# System dependency — required for Phase 3 video assembly
brew install ffmpeg      # macOS (or apt-get install ffmpeg on Linux)

cd script_to_movie/backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # Edit with your API keys
alembic upgrade head    # Create database tables
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Architecture — What You Can and Cannot Modify

```
app/
  core/          ← SHARED — DO NOT MODIFY
  config.py      ← SHARED — DO NOT MODIFY
  main.py        ← SHARED — DO NOT MODIFY
  models/        ← SHARED — DO NOT MODIFY
  schemas/       ← SHARED — DO NOT MODIFY
  auth/          ← SHARED — DO NOT MODIFY
  projects/      ← SHARED — DO NOT MODIFY
  system/        ← SHARED — DO NOT MODIFY
  phases/
    base_agent.py            ← SHARED — DO NOT MODIFY (your agents inherit from this)
    script_to_trailer/       ← Phase 1 developer ONLY
    trailer_to_storyboard/   ← Phase 2 developer ONLY
    storyboard_to_movie/     ← Phase 3 developer ONLY
  workflow/      ← Will be wired up after all phases work
```

## How to Use Core Modules

### Database (async SQLAlchemy)

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.models.scene import Scene

# READ — get a project
result = await db.execute(select(Project).where(Project.id == project_id))
project = result.scalar_one_or_none()

# READ — get scenes ordered
result = await db.execute(
    select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
)
scenes = result.scalars().all()

# WRITE — create a new record
scene = Scene(projectId=project_id, sceneNumber=1, title="Opening", ...)
db.add(scene)
await db.commit()
await db.refresh(scene)  # reload DB-generated fields like id, createdAt

# WRITE — update a record
project.status = "parsed"
project.progress = 33
await db.commit()

# WRITE — bulk create
db.add_all([scene1, scene2, scene3])
await db.commit()
```

### LLM Client (Claude API)

```python
from app.core.llm import llm_client

# Simple text response
response = await llm_client.invoke(
    messages=[{"role": "user", "content": "Analyze this script: ..."}],
    system="You are a professional screenplay analyst.",
    max_tokens=4096,
)
# response is a string

# Structured response (returns a Pydantic model instance)
from pydantic import BaseModel

class SceneAnalysis(BaseModel):
    title: str
    description: str
    dialogue: str
    characters: list[str]

result = await llm_client.invoke_structured(
    messages=[{"role": "user", "content": "Extract scene details from: ..."}],
    output_schema=SceneAnalysis,
    system="Extract structured scene data.",
)
# result.title, result.description, etc.

# JSON response (returns a dict)
data = await llm_client.invoke_json(
    messages=[{"role": "user", "content": "Return a JSON list of scenes..."}],
    system="Return valid JSON only.",
)
```

### S3 Storage

```python
from app.core.storage import storage_client

# Upload
url = await storage_client.upload(
    key=f"projects/{project_id}/videos/scene_1.mp4",
    data=video_bytes,
    content_type="video/mp4",
)

# Download
data = await storage_client.download(key="projects/1/videos/scene_1.mp4")

# Presigned URL (for frontend)
url = storage_client.get_presigned_url(key="projects/1/videos/scene_1.mp4")
```

## Agent Pattern

Every agent inherits from `BaseAgent` and follows the same pattern:

```python
from app.phases.base_agent import BaseAgent

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my_agent"

    async def execute(self, db: AsyncSession, project_id: int) -> dict:
        # 1. READ from database
        # 2. PROCESS (call LLM, external API, etc.)
        # 3. WRITE results back to database
        # 4. RETURN summary dict
        return {"status": "success", "message": "Done", "items_created": 5}
```

See the complete example at the bottom of `app/phases/base_agent.py`.

## Coding Conventions

- **Async everywhere**: All database and API calls use `await`
- **Error handling in agents**: Catch exceptions, return `{"status": "error", "message": ...}`
- **File naming**: `snake_case.py`
- **Class naming**: `PascalCase`
- **Database columns**: `camelCase` (matches existing models)
- **API endpoints**: `kebab-case` in URLs
- **Imports**: Always use full paths (`from app.models.scene import Scene`), not relative imports

## Data Flow Between Phases

```
Phase 1 WRITES:                    Phase 2 READS:
  Scene records (with dialogue) ──→  Scene records
  Character records ────────────→  Character records
  Setting records ──────────────→  Setting records
  StoryboardImage records ──────→  StoryboardImage records
  Project.trailerUrl

Phase 2 WRITES:                    Phase 3 READS:
  Updated StoryboardImage ──────→  StoryboardImage records (imageUrl)
                                   Scene records (description, dialogue)

Phase 3 WRITES:
  VideoPrompt records
  GeneratedVideo records
  FinalMovie record
  Project.status = "completed"
```

Phases communicate ONLY through the database. Never import code from another phase.

## Phase Assignments

### Phase 1: Script to Trailer
- **Branch**: `phase-1/script-to-trailer`
- **Directory**: `app/phases/script_to_trailer/`
- **Start with**: Read `README.md` in your phase directory
- **Key tool**: `llm_client.invoke_structured()` for parsing scripts with Claude

### Phase 2: Trailer to Storyboard
- **Branch**: `phase-2/trailer-to-storyboard`
- **Directory**: `app/phases/trailer_to_storyboard/`
- **Start with**: Read `README.md` in your phase directory
- **Key tool**: Image generation API (you choose which one)

### Phase 3: Storyboard to Movie
- **Branch**: `phase-3/storyboard-to-movie`
- **Directory**: `app/phases/storyboard_to_movie/`
- **Start with**: Read `README.md` in your phase directory
- **Key tools**: Video generation API + TTS API + moviepy/ffmpeg for assembly
