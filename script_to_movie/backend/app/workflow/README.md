# Workflow Module

## Status: Partially Implemented

The orchestrator and status endpoint work. Start/pause/resume are stubs (raise `NotImplementedError`) until all 3 phases are implemented.

## What This Module Does

Runs all 3 pipeline phases in sequence on a project:

```
Phase 1: Script to Trailer       --> status "parsed", progress 33%
Phase 2: Trailer to Storyboard   --> status "generating_storyboard", progress 66%
Phase 3: Storyboard to Movie     --> status "completed", progress 100%
```

If any phase fails, the project is marked as `"failed"`.

## Endpoints

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/workflow/{project_id}/start` | POST | Stub | Start the full pipeline |
| `/api/workflow/{project_id}/status` | GET | Working | Get current status and progress |
| `/api/workflow/{project_id}/pause` | POST | Stub | Pause execution |
| `/api/workflow/{project_id}/resume` | POST | Stub | Resume execution |

## Files

| File | What It Does |
|------|-------------|
| `orchestrator.py` | Calls `run_phase()` for each phase in sequence |
| `service.py` | `get_workflow_status()` reads project status from DB |
| `router.py` | FastAPI endpoints |

## How the Orchestrator Works

```python
# orchestrator.py (simplified)
async def run_full_pipeline(db, project_id):
    await script_to_trailer_service.run_phase(db, project_id)
    await trailer_to_storyboard_service.run_phase(db, project_id)
    await storyboard_to_movie_service.run_phase(db, project_id)
```

## Design Decisions (for future work)

### Background Execution

Currently the pipeline runs synchronously in the HTTP request. For production, consider:

| Approach | Pros | Cons |
|----------|------|------|
| FastAPI BackgroundTasks | Simple, no extra infra | Single-server only |
| Celery + Redis | Scalable, persistent, retries | Complex setup |
| ARQ | Async-native, simpler than Celery | Still needs Redis |

### Progress Updates

The frontend can poll `GET /api/workflow/{project_id}/status` to track progress. For real-time updates, consider Server-Sent Events (SSE) or WebSockets.

### Error Recovery

Currently: fail fast (stop on first error, mark project as failed). Future options include retry with backoff or checkpoint-and-resume.
