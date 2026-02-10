# Phase 2: Trailer to Storyboard -- Task Plan

## Overview

You are building Phase 2 of the Script-to-Movie pipeline. Your job is to take the scenes, character/setting descriptions, and trailer frames from Phase 1, and produce a validated storyboard where every scene has a quality frame that depicts it well.

**You read Phase 1's output from the database. When you're done, Phase 3 reads your output to generate videos.**

---

## Current State of Your Directory

```
app/phases/trailer_to_storyboard/
|-- __init__.py           <-- Empty
|-- router.py             <-- API endpoints (DONE - 2 endpoints wired up)
|-- service.py            <-- Service contract (DONE - method signatures with NotImplementedError)
|-- prompts.py            <-- YOU CREATE THIS (LLM prompt strings)
|-- image_generator.py    <-- YOU CREATE THIS (image generation API interface)
+-- agents/
    |-- __init__.py       <-- Empty
    +-- storyboard_prompt.py  <-- YOU CREATE THIS
```

### What's Already Done For You

- **`router.py`** has 2 working endpoints:
  - `POST /{project_id}/generate` -- calls `run_generate_storyboards()`
  - `GET /{project_id}/status` -- calls `get_generation_status()`

- **`service.py`** has method signatures that currently raise `NotImplementedError`. You replace the `raise` with actual implementation.

---

## Tasks (in order)

### Task 1: Create `prompts.py`

- [ ] Write system prompt for evaluating if a trailer frame depicts its scene well
- [ ] Write system prompt for generating optimized image prompts when frames need regeneration
- [ ] Include instructions for incorporating character and setting visual descriptions into image prompts

**Tips:**
- When evaluating frames, ask the LLM to check: Does the frame show the right setting? Are the right characters present? Does it match the scene's mood/action?
- When generating image prompts, always include the character and setting `visualDescription` fields for consistency

### Task 2: Create `image_generator.py`

- [ ] Create abstract `ImageGenerator` base class with `generate(prompt, width, height) -> bytes`
- [ ] Create `PlaceholderImageGenerator` that raises `NotImplementedError`
- [ ] (Later) Implement a real generator using your chosen API

**Image generation API options:**
- DALL-E 3: `pip install openai` -- use `AsyncOpenAI().images.generate()`
- Replicate (Flux/SDXL): `pip install replicate` -- use `replicate.async_run()`
- Any HTTP API: `pip install httpx` -- make async HTTP calls

**Image specs:** 16:9 aspect ratio (1024x576 or 1920x1080) for video compatibility

### Task 3: Create `agents/storyboard_prompt.py`

- [ ] Create `StoryboardPromptAgent` class that inherits from `BaseAgent`
- [ ] Implement `execute()` method:
  - Read all Scene records for this project (ordered by `Scene.order`)
  - Read all Character and Setting records
  - Read all existing StoryboardImage records
  - For each scene, check if it has a StoryboardImage
  - For scenes with missing frames, generate an optimized image prompt using Claude
  - For scenes with existing frames, optionally evaluate quality and regenerate if poor
  - Return a list of scenes that need new frames with their prompts

**How to build a good image prompt:**
```python
# Combine scene description + character looks + setting details
prompt = f"""
Scene: {scene.description}

Characters present:
{character_visual_descriptions}

Setting:
{setting_visual_description}

Style: Cinematic still frame, 16:9 aspect ratio, professional cinematography,
dramatic lighting, high production value
"""
```

### Task 4: Wire up `service.py`

- [ ] Import your agent and image generator
- [ ] Implement `run_generate_storyboards()`:
  - Run StoryboardPromptAgent to identify scenes needing frames + get prompts
  - For each scene needing a frame, call `image_generator.generate(prompt)`
  - Upload generated images to S3 using `storage_client`
  - Create or update StoryboardImage records in the database
  - Update project status to "generating_storyboard" and progress to 66
- [ ] Implement `get_generation_status()`:
  - Count total scenes vs. scenes with completed StoryboardImages
  - Return status dict

### Task 5: Test everything

- [ ] Make sure Phase 1 data exists in the database first (either run Phase 1 or insert test data manually)
- [ ] Test `POST /{project_id}/generate` -- verify StoryboardImage records are created/updated
- [ ] Test `GET /{project_id}/status` -- verify it shows correct counts
- [ ] Verify every scene has exactly one StoryboardImage with status "completed"

---

## Key Things to Get Right

1. **Every scene must have exactly one StoryboardImage.** Phase 3 uses these frames as visual references for video generation. If a scene has no frame, Phase 3 cannot generate video for it.

2. **Frames must visually depict their scenes.** A generic or unrelated frame will produce poor video output in Phase 3. The image should show the right setting, characters, and action.

3. **Always include character/setting visualDescriptions in image prompts.** This is how visual consistency is maintained across all generated content. If Detective Harris has "short graying brown hair and a dark gray trench coat" in Phase 1, he should look the same in every storyboard frame.

4. **16:9 aspect ratio** (1024x576 or 1920x1080) for video compatibility.

---

## Reference

- See `base_agent.py` for a complete example agent with the read-process-write pattern
- See your `README.md` for detailed code examples, database queries, and S3 upload patterns
- See `backend/CLAUDE.md` for how to use the database, LLM client, and S3 storage
