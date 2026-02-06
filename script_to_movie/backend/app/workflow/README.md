# Workflow Module

## Role

Orchestrates the full pipeline execution, managing the sequence of phases and tracking progress.

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      WorkflowOrchestrator                   │
├─────────────────────────────────────────────────────────────┤
│  1. script_to_trailer   →  Parse script, select scenes     │
│  2. trailer_to_storyboard →  Generate storyboard images    │
│  3. storyboard_to_movie   →  Generate videos, assemble     │
└─────────────────────────────────────────────────────────────┘
```

## Endpoints to Implement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/workflow/{project_id}/start` | POST | Start full pipeline |
| `/api/workflow/{project_id}/status` | GET | Get current status and progress |
| `/api/workflow/{project_id}/pause` | POST | Pause execution |
| `/api/workflow/{project_id}/resume` | POST | Resume execution |

## Files to Implement

| File | Responsibility |
|------|----------------|
| `orchestrator.py` | Main workflow logic, phase sequencing |
| `service.py` | Database operations, status tracking |
| `router.py` | API endpoints |

## Design Decisions

### 1. Execution Model

How should long-running pipeline tasks be executed?

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **Synchronous** | Run in HTTP request thread | Simple, easy to debug | Blocks request, timeout risk |
| **FastAPI BackgroundTasks** | Built-in background execution | Simple, no extra infra | Single-server, no persistence |
| **Celery + Redis** | Distributed task queue | Scalable, persistent, retries | Complex setup |
| **ARQ** | Async Redis queue | Async-native, simpler than Celery | Still needs Redis |
| **Temporal** | Workflow orchestration platform | Durable, complex workflows | Significant complexity |

**Dependency to add** (choose one):
```toml
# Simple (single server):
# No extra dependencies, use FastAPI BackgroundTasks

# Production (distributed):
"celery>=5.3.0",
"redis>=5.0.0",

# Async alternative:
"arq>=0.25.0",
```

**Questions to answer:**
- Will you run multiple server instances?
- Do you need job persistence across restarts?
- How critical is retry/recovery for failed jobs?

### 2. Progress Tracking Granularity

How detailed should progress updates be?

| Granularity | Description | Trade-off |
|-------------|-------------|-----------|
| **Phase-level** | Update at phase boundaries (3 updates) | Simple but coarse |
| **Step-level** | Update at each agent completion | Better UX, more DB writes |
| **Item-level** | Update per image/video generated | Best UX, most DB writes |
| **Percentage-based** | Continuous 0-100% updates | Smooth UX, requires estimation |

**Suggested breakdown**:
```
0-5%:   Script upload received
5-15%:  Script analysis complete
15-25%: Character consistency complete
25-35%: Setting consistency complete
35-45%: Trailer scenes selected
45-70%: Storyboard images generating (per-image updates)
70-95%: Video clips generating (per-clip updates)
95-100%: Final assembly complete
```

**Questions to answer:**
- How often should the UI update?
- Should each image/video show individual progress?

### 3. Real-time Update Mechanism

How should progress be communicated to the frontend?

| Mechanism | Description | Trade-off |
|-----------|-------------|-----------|
| **Polling** | Frontend polls `/status` endpoint | Simple, works everywhere, more requests |
| **Server-Sent Events (SSE)** | Server pushes updates to client | Efficient, one-way, good browser support |
| **WebSocket** | Bidirectional real-time connection | Most flexible, more complex |
| **Long polling** | Request blocks until update available | Simpler than WebSocket, less efficient |

```toml
# For SSE:
"sse-starlette>=1.6.0",

# For WebSocket (built into FastAPI):
# No extra dependency needed
```

**Questions to answer:**
- Does the frontend need to send messages back?
- What's the expected concurrent user count?
- How frequently do updates occur?

### 4. Error Handling Strategy

What happens when a phase fails?

| Strategy | Description | Trade-off |
|----------|-------------|-----------|
| **Fail fast** | Stop entire pipeline on first error | Simple, clear failure state |
| **Skip and continue** | Mark failed item, continue pipeline | Partial results, complex state |
| **Retry with backoff** | Automatic retry before failing | More resilient, longer execution |
| **Checkpoint and resume** | Save state, allow manual retry from failure | Best UX, complex implementation |

**Error state storage**:
- `project.status` = `'failed'`
- `project.errorMessage` = detailed error
- `project.failedAt` = which phase/step failed
- `project.retryCount` = number of retry attempts

**Questions to answer:**
- Should users be able to retry from the failed step?
- How many automatic retries before giving up?
- Should partial results be preserved?

### 5. Workflow Types

What pipeline variations should be supported?

| Type | Description | Use Case |
|------|-------------|----------|
| `full_pipeline` | All three phases | Standard flow |
| `script_analysis_only` | Phase 1 only | Preview/testing |
| `storyboard_only` | Phases 1 + 2 | Static storyboard output |
| `video_only` | Phase 3 only | Resume from existing storyboard |
| `regenerate_scene` | Single scene regeneration | Fix specific issues |

**Questions to answer:**
- Which workflow types do you need for v1?
- Should users choose the workflow type?

### 6. Concurrency & Rate Limiting

How do you handle multiple simultaneous workflows?

| Concern | Options |
|---------|---------|
| **Per-user limits** | Max 1-3 concurrent projects per user |
| **Global limits** | Max N total concurrent workflows |
| **API rate limits** | Queue requests to stay under API limits |
| **Priority queues** | Paid users get priority processing |

**Questions to answer:**
- How many concurrent workflows can your APIs handle?
- Should free/paid users have different limits?

### 7. Cancellation & Pause

Should users be able to stop or pause workflows?

| Feature | Implementation Complexity |
|---------|--------------------------|
| **Cancel** | Medium - stop current task, clean up |
| **Pause/Resume** | High - checkpoint state, resume later |
| **Skip step** | Medium - mark complete, move to next |

**Questions to answer:**
- Is cancellation required for v1?
- Should cancelled workflows be restartable?

### 8. Idempotency & Deduplication

How do you handle duplicate workflow requests?

| Strategy | Description |
|----------|-------------|
| **Reject duplicates** | Return error if workflow already running |
| **Return existing** | Return current workflow status |
| **Allow parallel** | Multiple workflows on same project (complex) |
| **Idempotency keys** | Client provides key to prevent duplicates |

**Questions to answer:**
- What happens if a user clicks "Start" twice?
- Should the same project allow multiple workflows?

## Implementation Steps

1. **Implement orchestrator.py**:
   ```python
   class WorkflowOrchestrator:
       async def execute(self, project_id: int, workflow_type: str):
           try:
               await self.run_phase1(project_id)  # script_to_trailer
               await self.run_phase2(project_id)  # trailer_to_storyboard
               await self.run_phase3(project_id)  # storyboard_to_movie
               await self.mark_completed(project_id)
           except Exception as e:
               await self.mark_failed(project_id, str(e))
   ```

2. **Implement service.py**:
   ```python
   async def start_workflow(db: AsyncSession, project_id: int, workflow_type: str)
   async def get_status(db: AsyncSession, project_id: int) -> WorkflowStatus
   async def update_progress(db: AsyncSession, project_id: int, progress: int)
   ```

3. **Set up background task execution**:
   - Option A: FastAPI BackgroundTasks (simple, single-server)
   - Option B: Celery + Redis (scalable, distributed)
   - Option C: ARQ (async-native, simpler than Celery)

4. **Implement router.py** endpoints with appropriate async handling.

## Workflow Types

| Type | Description |
|------|-------------|
| `full_pipeline` | Run all phases |
| `storyboard_only` | Skip video generation |
| `video_only` | Start from existing storyboards |

## Reference

See original implementation: `script_to_movie/server/agents/WorkflowOrchestrator.ts`
