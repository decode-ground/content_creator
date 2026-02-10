# Pipeline Phases

## Overview

The Script-to-Movie pipeline has 3 sequential phases. Each phase is assigned to a different developer and lives in its own directory.

```
+--------------------+     +--------------------------+     +----------------------+
| script_to_trailer  | --> | trailer_to_storyboard    | --> | storyboard_to_movie  |
|                    |     |                          |     |                      |
| Parse script into  |     | Validate scene-to-frame  |     | Video prompts        |
| scenes with dialog |     | mapping                  |     | Image-to-video gen   |
| Character descs    |     | Regenerate poor/missing  |     | TTS audio from dialog|
| Setting descs      |     | frames with image gen API|     | Assemble final movie |
| Generate trailer   |     |                          |     |                      |
| Extract frames     |     |                          |     |                      |
+--------------------+     +--------------------------+     +----------------------+
```

## Phase Summary

| Phase | Developer | Input | Output | Status After |
|-------|-----------|-------|--------|-------------|
| **script_to_trailer** | Developer 1 | Raw script/plot | Scenes (with dialogue), Characters, Settings, Trailer video, Storyboard frames | `parsed`, 33% |
| **trailer_to_storyboard** | Developer 2 | Scenes, Characters, Settings, Storyboard frames | Validated/enhanced StoryboardImage records | `generating_storyboard`, 66% |
| **storyboard_to_movie** | Developer 3 | Scenes (with dialogue), StoryboardImages | VideoPrompts, GeneratedVideos, FinalMovie | `completed`, 100% |

## Shared: Base Agent (`base_agent.py`)

All agents inherit from `BaseAgent`. It provides:

- **`self.llm`** -- LLM client for calling Claude (text, structured, or JSON responses)
- **`safe_execute(db, project_id)`** -- wraps your `execute()` method with error handling

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
        return {"status": "success", "message": "Done"}
```

See the complete example at the bottom of `base_agent.py`.

## How Phases Communicate

Phases communicate **only through the database**. Never import code from another phase.

```
Phase 1 WRITES:                      Phase 2 READS:
  Scene records (with dialogue)  -->   Scene records
  Character records              -->   Character records
  Setting records                -->   Setting records
  StoryboardImage records        -->   StoryboardImage records

Phase 2 WRITES:                      Phase 3 READS:
  Updated StoryboardImage        -->   StoryboardImage records (imageUrl)
  records                              Scene records (description, dialogue)

Phase 3 WRITES:
  VideoPrompt records
  GeneratedVideo records
  FinalMovie record
  Project.status = "completed"
```

## Getting Started

Each phase has its own detailed documentation:

| Phase | Developer Guide | Task Checklist |
|-------|----------------|----------------|
| Phase 1 | [`script_to_trailer/README.md`](script_to_trailer/README.md) | [`script_to_trailer/PLAN.md`](script_to_trailer/PLAN.md) |
| Phase 2 | [`trailer_to_storyboard/README.md`](trailer_to_storyboard/README.md) | [`trailer_to_storyboard/PLAN.md`](trailer_to_storyboard/PLAN.md) |
| Phase 3 | [`storyboard_to_movie/README.md`](storyboard_to_movie/README.md) | [`storyboard_to_movie/PLAN.md`](storyboard_to_movie/PLAN.md) |

## Development Order

Phases can be developed in parallel, but testing requires data from earlier phases:

1. **Phase 1** can be developed and tested independently (only needs a project with `scriptContent`)
2. **Phase 2** needs Phase 1 data in the database (Scene, Character, Setting, StoryboardImage records)
3. **Phase 3** needs Phase 1 and 2 data (Scenes with dialogue + completed StoryboardImages)

If Phase 1 isn't ready, you can manually insert test records to develop Phase 2 or 3.
