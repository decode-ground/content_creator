# Agent Architecture

## Overview

The Script-to-Movie platform uses a multi-agent system where specialized AI agents work together in a pipeline to transform screenplays into complete movies. Each agent handles one specific task and follows the same read-process-write pattern.

## The Agent Pattern

Every agent inherits from `BaseAgent` (defined in `app/phases/base_agent.py`):

```python
from app.phases.base_agent import BaseAgent
from sqlalchemy.ext.asyncio import AsyncSession

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my_agent"

    async def execute(self, db: AsyncSession, project_id: int) -> dict:
        # 1. READ from the database
        # 2. PROCESS (call LLM, external API, etc.)
        # 3. WRITE results back to the database
        # 4. RETURN a summary dict
        return {"status": "success", "message": "Done", "items_created": 5}
```

### Key Features of BaseAgent

- **`self.llm`** -- An instance of `LLMClient` for calling Claude. Supports:
  - `self.llm.invoke()` -- simple text response
  - `self.llm.invoke_structured()` -- returns a Pydantic model instance
  - `self.llm.invoke_json()` -- returns a dict
- **`safe_execute(db, project_id)`** -- wraps `execute()` with error handling and logging. If an exception occurs, returns `{"status": "error", "message": ...}` instead of crashing.

## Agent Pipeline

```
User uploads script/plot
         |
         v
+-----------------------------------------+
| Phase 1: Script to Trailer              |
|                                         |
|  ScriptAnalysisAgent                    |
|    Parse script into scenes with dialog |
|         |                               |
|  CharacterConsistencyAgent              |
|    Generate character visual descriptions|
|         |                               |
|  SettingConsistencyAgent                |
|    Generate setting visual descriptions |
|         |                               |
|  TrailerGenerationAgent                 |
|    Generate trailer video, extract frames|
+-----------------------------------------+
         |
         v
+-----------------------------------------+
| Phase 2: Trailer to Storyboard         |
|                                         |
|  StoryboardPromptAgent                  |
|    Evaluate frames, generate better     |
|    image prompts if needed              |
|         |                               |
|  (Image generation API call)            |
|    Regenerate poor/missing frames       |
+-----------------------------------------+
         |
         v
+-----------------------------------------+
| Phase 3: Storyboard to Movie           |
|                                         |
|  VideoPromptAgent                       |
|    Create optimized video gen prompts   |
|         |                               |
|  VideoGenerationAgent                   |
|    Call image-to-video API per scene    |
|         |                               |
|  VideoAssemblyAgent                     |
|    TTS audio + combine + assemble movie |
+-----------------------------------------+
         |
         v
    Final Movie (MP4)
```

## How Agents Communicate

Agents **never** import code from each other. They communicate through the database:

1. Agent A writes records to the database (e.g., Scene records)
2. Agent B reads those records from the database
3. Agent B writes its own results

This means phases can be developed and tested independently.

## Workflow Orchestration

The `WorkflowOrchestrator` (in `app/workflow/orchestrator.py`) runs all three phases in sequence:

```python
async def run_full_pipeline(db, project_id):
    await script_to_trailer_service.run_phase(db, project_id)
    await trailer_to_storyboard_service.run_phase(db, project_id)
    await storyboard_to_movie_service.run_phase(db, project_id)
```

If any phase fails, the orchestrator marks the project as failed and stops.

## Structured LLM Output

Agents use Claude's structured output to get reliable, typed responses:

```python
from pydantic import BaseModel

class SceneAnalysis(BaseModel):
    title: str
    description: str
    dialogue: str
    characters: list[str]

# Returns a SceneAnalysis instance (not a string)
result = await self.llm.invoke_structured(
    messages=[{"role": "user", "content": "Extract scene details from: ..."}],
    output_schema=SceneAnalysis,
    system="Extract structured scene data.",
)
# result.title, result.description, etc.
```

## Error Handling

- Each agent's `safe_execute()` catches exceptions and returns an error dict
- The workflow orchestrator checks each phase result and stops on failure
- Project status is updated to reflect the current state (e.g., "parsed", "generating_storyboard", "completed", "failed")

## Adding a New Agent

1. Create a new file in your phase's `agents/` directory
2. Inherit from `BaseAgent`
3. Implement `name` property and `execute()` method
4. Follow the read-process-write pattern
5. Call `agent.safe_execute(db, project_id)` from your service
