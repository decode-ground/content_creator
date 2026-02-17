# Phase 2: Image Generator Tasks

## Overview

These are the tasks for implementing `image_generator.py` — the image generation interface for Phase 2 (Trailer to Storyboard).

**File:** `app/phases/trailer_to_storyboard/image_generator.py`

---

## Tasks

### Task 1: Create abstract ImageGenerator base class
- [ ] Define `ImageGenerator(ABC)` with abstract async method `generate(self, prompt: str, width: int = 1024, height: int = 576) -> bytes`
- [ ] Docstring explaining it returns raw image bytes
- [ ] Default dimensions are 16:9 (1024x576) for video compatibility

### Task 2: Create PlaceholderImageGenerator implementation
- [ ] `PlaceholderImageGenerator(ImageGenerator)` that raises `NotImplementedError("Connect a real image generation API here")`
- [ ] Allows the rest of the pipeline (service.py, agent) to be developed against a known interface before a real API is connected
- **Blocked by:** Task 1

### Task 3: Implement a real ImageGenerator (DALL-E 3, Flux, or other API)
- [ ] Create a concrete implementation that calls a real image generation API
- [ ] Must be async and return image bytes
- [ ] Must support width/height params (or map to closest supported size)
- [ ] Must target 16:9 aspect ratio (1024x576 or 1920x1080)
- [ ] Add any new dependencies to `pyproject.toml`
- [ ] Add any new API keys to `.env.example`
- **Blocked by:** Task 1

**API options:**
- **DALL-E 3**: `pip install openai` — `AsyncOpenAI().images.generate()`
- **Replicate (Flux/SDXL)**: `pip install replicate` — `replicate.async_run()`
- **Any HTTP API**: `pip install httpx` — async HTTP calls

### Task 4: Test image generator end-to-end
- [ ] Instantiate the real generator
- [ ] Call `generate()` with a test prompt (e.g. "Cinematic still frame of a detective in a dimly lit office, 16:9 aspect ratio")
- [ ] Verify it returns valid image bytes (PNG/JPEG)
- [ ] Verify image dimensions are approximately 16:9
- [ ] Handle API errors gracefully (rate limits, invalid keys, etc.)
- **Blocked by:** Task 3

---

## Requirements

- Every scene must have exactly one StoryboardImage (Phase 3 depends on this)
- Frames must be **16:9 aspect ratio** (1024x576 or 1920x1080) for video compatibility
- Character/setting `visualDescriptions` should be included in image prompts for visual consistency
