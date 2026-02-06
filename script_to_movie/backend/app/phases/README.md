# Pipeline Phases

## Overview

The Script-to-Movie pipeline is divided into three sequential phases:

```
┌──────────────────┐     ┌────────────────────────┐     ┌────────────────────┐
│ script_to_trailer│ ──→ │ trailer_to_storyboard  │ ──→ │ storyboard_to_movie│
│                  │     │                        │     │                    │
│ • Parse script   │     │ • Generate prompts     │     │ • Video prompts    │
│ • Extract scenes │     │ • Create images        │     │ • Generate clips   │
│ • Characters     │     │                        │     │ • Assemble movie   │
│ • Settings       │     │                        │     │                    │
│ • Select trailer │     │                        │     │                    │
└──────────────────┘     └────────────────────────┘     └────────────────────┘
```

## Phase Summary

| Phase | Input | Output | Key Tech Decisions |
|-------|-------|--------|-------------------|
| **script_to_trailer** | Raw screenplay | Scenes, characters, settings, trailer selection | LLM prompts |
| **trailer_to_storyboard** | Trailer scenes + descriptions | Storyboard images | Image generation API |
| **storyboard_to_movie** | Storyboard images | Final trailer video | Video generation API, FFmpeg |

## Shared Components

### Base Agent (`base_agent.py`)

Implement a base class for all agents:

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.core.llm import llm_client

class BaseAgent(ABC):
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    @abstractmethod
    async def execute(self, input_data: dict) -> BaseModel:
        pass

    async def reason(self, messages: list[dict]) -> str:
        return await llm_client.invoke(
            messages=messages,
            system=self.system_prompt
        )
```

## Development Order

Recommended implementation order:

1. **script_to_trailer** - Can be developed and tested with just Claude API
2. **trailer_to_storyboard** - Requires image generation API choice
3. **storyboard_to_movie** - Most complex, requires video API + FFmpeg
4. **workflow** - Ties everything together

Each phase can be developed and tested independently before integration.
