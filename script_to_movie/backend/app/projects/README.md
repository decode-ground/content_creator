# Projects Module

## Role

Manages CRUD operations for video production projects and their related entities (scenes, characters, settings, storyboards, movies).

## Endpoints to Implement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | POST | Create new project |
| `/api/projects` | GET | List user's projects |
| `/api/projects/{id}` | GET | Get project details |
| `/api/projects/{id}/scenes` | GET | Get project scenes |
| `/api/projects/{id}/characters` | GET | Get project characters |
| `/api/projects/{id}/settings` | GET | Get project settings |
| `/api/projects/{id}/storyboards` | GET | Get storyboard images |
| `/api/projects/{id}/movie` | GET | Get final movie |

## Available Infrastructure

- `app/models/` - All SQLAlchemy models (Project, Scene, Character, Setting, etc.)
- `app/schemas/project.py` - Pydantic schemas
- `app/core/dependencies.py` - `get_db`, `get_current_user`

## Key Decisions

1. **Authorization**: Ensure users can only access their own projects.
2. **Pagination**: Add pagination for list endpoints if needed.
3. **Deletion**: Implement soft delete or cascade delete for projects.

## Implementation Steps

1. **Implement `service.py`**:
   ```python
   async def create_project(db: AsyncSession, user_id: int, data: ProjectCreate) -> Project
   async def get_projects(db: AsyncSession, user_id: int) -> list[Project]
   async def get_project(db: AsyncSession, project_id: int, user_id: int) -> Project | None
   async def get_scenes(db: AsyncSession, project_id: int) -> list[Scene]
   # ... etc
   ```

2. **Implement `router.py`** endpoints:
   - All endpoints should be protected (require authentication)
   - Validate project ownership before returning data
   - Return appropriate Pydantic response models

3. **Test CRUD operations**:
   - Create project with script content
   - Verify scenes/characters/settings are populated after analysis
   - Check storyboards and movie endpoints

## Database Models

```
Project (1) ──→ (N) Scene ──→ (N) StoryboardImage
    │                  └──→ (N) VideoPrompt
    │                  └──→ (N) GeneratedVideo
    ├──→ (N) Character
    ├──→ (N) Setting
    └──→ (1) FinalMovie
```

## Reference

See original implementation: `script_to_movie/server/routers/projects.ts`
