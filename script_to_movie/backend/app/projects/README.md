# Projects Module

## Status: Implemented

Project CRUD is fully working. You do not need to modify this module.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | POST | Create a new project with a script |
| `/api/projects` | GET | List all projects for the logged-in user |
| `/api/projects/{id}` | GET | Get a specific project (must be owner) |
| `/api/projects/{id}/scenes` | GET | Get all scenes for a project |
| `/api/projects/{id}/characters` | GET | Get all characters for a project |
| `/api/projects/{id}/settings` | GET | Get all settings/locations for a project |
| `/api/projects/{id}/storyboards` | GET | Get all storyboard images for a project |
| `/api/projects/{id}/movie` | GET | Get the final movie for a project |

All endpoints require authentication. Users can only access their own projects.

## Files

| File | What It Does |
|------|-------------|
| `service.py` | Business logic: `create_project()`, `list_projects()`, `get_project()`, `get_project_scenes()`, etc. |
| `router.py` | FastAPI endpoints that call service functions |

## How Phases Use Projects

Phase agents don't call project endpoints directly. Instead, they read/write to the database using SQLAlchemy models:

```python
from sqlalchemy import select
from app.models.project import Project
from app.models.scene import Scene

# Read the project
result = await db.execute(select(Project).where(Project.id == project_id))
project = result.scalar_one_or_none()

# Read scenes for a project
result = await db.execute(
    select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
)
scenes = result.scalars().all()
```

## Database Relationships

```
Project (1) --> (N) Scene --> (1) StoryboardImage
    |                  |--> (1) VideoPrompt
    |                  +--> (1) GeneratedVideo
    |
    |--> (N) Character
    |--> (N) Setting
    +--> (1) FinalMovie
```

## Testing

```bash
# Create a project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -b "session=YOUR_TOKEN" \
  -d '{"title":"Test Movie","scriptContent":"Your test script here..."}'

# List projects
curl http://localhost:8000/api/projects -b "session=YOUR_TOKEN"

# Get a specific project
curl http://localhost:8000/api/projects/1 -b "session=YOUR_TOKEN"

# Get scenes (populated after Phase 1 runs)
curl http://localhost:8000/api/projects/1/scenes -b "session=YOUR_TOKEN"
```
