# Agent Integration Guide

## How the Frontend Talks to Agents

The frontend communicates with agents through REST API endpoints. Each phase has its own set of endpoints that trigger agent execution.

### Triggering a Phase

```
User clicks "Parse Script" button
    |
    v
Frontend calls POST /api/phases/script-to-trailer/{project_id}/analyze
    |
    v
Backend router calls service.run_script_analysis(db, project_id)
    |
    v
Service creates ScriptAnalysisAgent and calls agent.safe_execute(db, project_id)
    |
    v
Agent reads from DB, calls Claude, writes results to DB
    |
    v
Response returned to frontend with status and summary
```

### Checking Progress

```
Frontend polls GET /api/workflow/{project_id}/status
    |
    v
Returns: { projectId, status, progress, currentStep, error }
```

## API Endpoints by Phase

### Phase 1: Script to Trailer

```bash
# Step 1: Parse the script into scenes
POST /api/phases/script-to-trailer/{project_id}/analyze

# Step 2: Generate character visual descriptions
POST /api/phases/script-to-trailer/{project_id}/characters

# Step 3: Generate setting visual descriptions
POST /api/phases/script-to-trailer/{project_id}/settings

# Step 4: Generate trailer video and extract frames
POST /api/phases/script-to-trailer/{project_id}/trailer

# Verify results
GET /api/projects/{project_id}/scenes
GET /api/projects/{project_id}/characters
GET /api/projects/{project_id}/settings
GET /api/projects/{project_id}/storyboards
```

### Phase 2: Trailer to Storyboard

```bash
# Validate and regenerate storyboard frames
POST /api/phases/trailer-to-storyboard/{project_id}/generate

# Check progress
GET /api/phases/trailer-to-storyboard/{project_id}/status

# Verify results
GET /api/projects/{project_id}/storyboards
```

### Phase 3: Storyboard to Movie

```bash
# Step 1: Generate video prompts
POST /api/phases/storyboard-to-movie/{project_id}/prompts

# Step 2: Generate video clips
POST /api/phases/storyboard-to-movie/{project_id}/generate

# Step 3: Assemble final movie (TTS + combine + concat)
POST /api/phases/storyboard-to-movie/{project_id}/assemble

# Check progress
GET /api/phases/storyboard-to-movie/{project_id}/status

# Get the final movie
GET /api/projects/{project_id}/movie
```

### Full Pipeline (All Phases)

```bash
# Run all 3 phases automatically
POST /api/workflow/{project_id}/start

# Check overall progress
GET /api/workflow/{project_id}/status
```

## Frontend Progress Tracking

The frontend can poll the workflow status endpoint to show progress:

```typescript
// Poll every 2 seconds until complete
const checkProgress = async (projectId: number) => {
  const response = await fetch(`/api/workflow/${projectId}/status`);
  const data = await response.json();
  // data.progress is 0-100
  // data.status is "pending", "parsed", "generating_storyboard", "completed", "failed"
  return data;
};
```

### Progress Breakdown

| Progress Range | What's Happening |
|---------------|-----------------|
| 0-33% | Phase 1: Parsing script, generating descriptions, creating trailer |
| 33-66% | Phase 2: Validating/regenerating storyboard frames |
| 66-100% | Phase 3: Generating videos, TTS audio, assembling movie |

## Response Format

All agent endpoints return a JSON response:

```json
{
  "status": "success",
  "message": "Script analysis complete",
  "scenes_created": 12
}
```

On error:

```json
{
  "status": "error",
  "message": "Failed to parse script: ..."
}
```

## Authentication

All endpoints require authentication. The frontend sends a session cookie:

```typescript
// Cookie is set automatically after login
const response = await fetch('/api/phases/script-to-trailer/1/analyze', {
  method: 'POST',
  credentials: 'include',  // sends the session cookie
});
```
