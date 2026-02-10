# Phase 1: Script to Trailer -- Task Plan

## Overview

You are building Phase 1 of the Script-to-Movie pipeline. Your job is to take a movie title and script/plot text and produce:
- A full screenplay broken into scenes (with dialogue)
- Detailed visual descriptions for every character
- Detailed visual descriptions for every setting/location
- A trailer video generated from the scene descriptions
- One storyboard frame extracted from the trailer for each scene

**When you're done, Phase 2 reads your output from the database to build the storyboard.**

---

## Current State of Your Directory

```
app/phases/script_to_trailer/
|-- __init__.py          <-- Empty
|-- router.py            <-- API endpoints (DONE - 4 endpoints wired up)
|-- service.py           <-- Service contract (DONE - method signatures with NotImplementedError)
|-- prompts.py           <-- YOU CREATE THIS (LLM prompt strings)
+-- agents/
    |-- __init__.py      <-- Empty
    |-- script_analysis.py        <-- YOU CREATE THIS
    |-- character_consistency.py  <-- YOU CREATE THIS
    |-- setting_consistency.py    <-- YOU CREATE THIS
    +-- trailer_selection.py      <-- RENAME to trailer_generation.py, then implement
```

### What's Already Done For You

- **`router.py`** has 4 working endpoints that call the service methods:
  - `POST /{project_id}/analyze` -- calls `run_script_analysis()`
  - `POST /{project_id}/characters` -- calls `run_character_consistency()`
  - `POST /{project_id}/settings` -- calls `run_setting_consistency()`
  - `POST /{project_id}/trailer` -- calls `run_trailer_generation()`

- **`service.py`** has method signatures that currently raise `NotImplementedError`. You replace the `raise` with actual agent calls.

---

## Tasks (in order)

### Task 1: Create `prompts.py`

- [ ] Write system prompt for script analysis (breaking a script into scenes)
- [ ] Write system prompt for character description generation
- [ ] Write system prompt for setting description generation
- [ ] Write system prompt for trailer video prompt generation

**Tips:**
- Store prompts as string constants (e.g., `SCRIPT_ANALYSIS_SYSTEM_PROMPT = "..."`)
- Be specific about what format you want the LLM to return
- For character descriptions, emphasize physical appearance details (hair, eyes, build, clothing)
- For setting descriptions, emphasize visual details (lighting, colors, atmosphere)

### Task 2: Create `agents/script_analysis.py`

- [ ] Create `ScriptAnalysisAgent` class that inherits from `BaseAgent`
- [ ] Define Pydantic output schema (e.g., `ScriptBreakdown` with list of scenes)
- [ ] Implement `execute()` method:
  - Read `project.scriptContent` from the database
  - Call `self.llm.invoke_structured()` to parse the script into scenes
  - Create `Scene` records in the database (with dialogue, description, characters, setting, duration, order)
  - Return a summary dict

**What to write to the database:**
```python
Scene(
    projectId=project_id,
    sceneNumber=1,
    title="The Dark Alley",
    description="A dimly lit alley...",       # Visual description
    dialogue="DETECTIVE: Stay behind me...",   # All spoken lines
    setting="Downtown Chicago - Dark Alley",
    characters=json.dumps(["Detective Harris", "Sarah"]),
    duration=45,    # Estimated seconds
    order=1,        # Scene sequence number
)
```

### Task 3: Create `agents/character_consistency.py`

- [ ] Create `CharacterConsistencyAgent` class that inherits from `BaseAgent`
- [ ] Implement `execute()` method:
  - Read all Scene records for this project
  - Extract unique character names from all scenes
  - Call `self.llm.invoke_structured()` to generate visual descriptions for each character
  - Create `Character` records in the database

**What to write to the database:**
```python
Character(
    projectId=project_id,
    name="Detective Harris",
    description="A weathered homicide detective in his late 40s...",
    visualDescription="Male, late 40s, short graying brown hair, square jaw..."
    # visualDescription must be detailed enough for image/video generation
)
```

### Task 4: Create `agents/setting_consistency.py`

- [ ] Create `SettingConsistencyAgent` class that inherits from `BaseAgent`
- [ ] Same pattern as character agent, but for settings/locations
- [ ] Create `Setting` records in the database

**What to write to the database:**
```python
Setting(
    projectId=project_id,
    name="Downtown Chicago - Dark Alley",
    description="A narrow alley between two brick buildings...",
    visualDescription="Narrow urban alley, wet red brick walls, dim yellow streetlight..."
)
```

### Task 5: Rename and create `agents/trailer_generation.py`

- [ ] Rename `trailer_selection.py` to `trailer_generation.py`
- [ ] Create `TrailerGenerationAgent` class that inherits from `BaseAgent`
- [ ] Implement `execute()` method:
  - Read all Scene records (with descriptions)
  - Build a combined prompt from all scene descriptions
  - Call a text-to-video API to generate a trailer video
  - Upload the trailer video to S3 using `storage_client`
  - Update `project.trailerUrl` and `project.trailerKey`
  - Extract one frame per scene from the trailer video (using ffmpeg or moviepy)
  - Upload each frame to S3
  - Create `StoryboardImage` records (one per scene)

**What to write to the database:**
```python
# Update project with trailer
project.trailerUrl = trailer_url
project.trailerKey = f"projects/{project_id}/trailer.mp4"

# Create one storyboard frame per scene
StoryboardImage(
    sceneId=scene.id,
    projectId=project_id,
    imageUrl=frame_url,
    imageKey=f"projects/{project_id}/frames/scene_{scene.sceneNumber}.png",
    prompt=f"Frame for scene {scene.sceneNumber}: {scene.description[:200]}",
    status="completed",
)
```

### Task 6: Wire up `service.py`

- [ ] Import your agents
- [ ] Implement `run_script_analysis()` -- create agent, call `agent.safe_execute(db, project_id)`
- [ ] Implement `run_character_consistency()` -- same pattern
- [ ] Implement `run_setting_consistency()` -- same pattern
- [ ] Implement `run_trailer_generation()` -- same pattern
- [ ] Implement `run_phase()` -- call all 4 methods in sequence, update project status to "parsed" and progress to 33

### Task 7: Test everything

- [ ] Start the server: `uvicorn app.main:app --reload`
- [ ] Register a user and create a project (see README.md for curl commands)
- [ ] Test `/analyze` endpoint -- verify scenes were created with dialogue
- [ ] Test `/characters` endpoint -- verify character records with visual descriptions
- [ ] Test `/settings` endpoint -- verify setting records with visual descriptions
- [ ] Test `/trailer` endpoint -- verify trailer video and storyboard frames
- [ ] Verify every scene has exactly one StoryboardImage

---

## Key Things to Get Right

1. **Dialogue must be preserved.** Phase 3 uses `Scene.dialogue` to generate spoken audio (TTS). If dialogue is missing, the movie will be silent.

2. **Character visualDescriptions must be very detailed.** Include: age, gender, hair color/style, eye color, build, height, clothing, distinguishing features. These descriptions are used by Phase 2 and 3 to generate consistent images/videos.

3. **Every scene needs one StoryboardImage.** Phase 3 cannot generate video for a scene without a visual reference frame.

4. **Scene order matters.** Set `Scene.order` correctly (1, 2, 3...) because the final movie assembles scenes in this order.

---

## Reference

- See `base_agent.py` for a complete example agent with the read-process-write pattern
- See your `README.md` for detailed code examples and API usage
- See `backend/CLAUDE.md` for how to use the database, LLM client, and S3 storage
