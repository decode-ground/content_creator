# Phase 1: Script to Trailer

## Role

Analyzes raw screenplays and extracts structured data for trailer production. This is the first phase of the pipeline.

## Pipeline Position

```
[Script Upload] → [THIS PHASE] → [Trailer to Storyboard] → [Storyboard to Movie]
```

## Input

- Raw screenplay text (from `project.scriptContent`)

## Output

- Parsed scenes with descriptions
- Character profiles with visual descriptions
- Setting profiles with visual descriptions
- Selected trailer scenes (3-5 key moments)

## Endpoints to Implement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/phases/script-to-trailer/{project_id}/analyze` | POST | Parse script, extract scenes |
| `/api/phases/script-to-trailer/{project_id}/characters` | POST | Generate character consistency descriptions |
| `/api/phases/script-to-trailer/{project_id}/settings` | POST | Generate setting consistency descriptions |
| `/api/phases/script-to-trailer/{project_id}/select-scenes` | POST | Select key scenes for trailer |

## Agents to Implement

| Agent | File | Responsibility |
|-------|------|----------------|
| ScriptAnalysisAgent | `agents/script_analysis.py` | Parse screenplay structure, extract scenes |
| CharacterConsistencyAgent | `agents/character_consistency.py` | Generate consistent visual descriptions for characters |
| SettingConsistencyAgent | `agents/setting_consistency.py` | Generate consistent visual descriptions for locations |
| TrailerSelectionAgent | `agents/trailer_selection.py` | Select most impactful scenes for trailer |

## Available Infrastructure

- `app/core/llm.py` - Claude client with `invoke()`, `invoke_structured()`, `invoke_json()`
- `app/models/` - Scene, Character, Setting models
- `prompts.py` - Define your LLM prompts here

## Design Decisions

### 1. LLM Prompting Strategy

How should the script be processed by Claude?

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **Single large prompt** | Send entire script in one API call | Simple implementation but may hit token limits for long scripts |
| **Chunked processing** | Process script in sections, merge results | Handles long scripts but requires merge logic for scenes spanning chunks |
| **Multi-pass refinement** | Initial extraction → refinement pass | Higher quality output but more API calls and cost |

**Questions to answer:**
- What's the maximum script length you need to support?
- Is accuracy or cost more important?

### 2. Screenplay Format Support

What input formats should be accepted?

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **Strict format only** | Only accept .fountain or .fdx files | Simpler parsing, reliable structure, but may reject valid scripts |
| **Flexible parsing** | Accept plain text, detect structure via LLM | More accessible to users but less reliable extraction |
| **Format conversion** | Convert all inputs to standard format first | Consistent processing but adds conversion complexity |

**Questions to answer:**
- What format will users typically provide?
- How much preprocessing are you willing to do?

### 3. Character/Setting Consistency Approach

How should visual descriptions maintain consistency across scenes?

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **Per-scene descriptions** | Generate fresh description for each scene | May have inconsistencies between scenes |
| **Global reference sheet** | Create master description, reference everywhere | Consistent visuals but less scene-specific adaptation |
| **Hybrid approach** | Master description + scene-specific variations | Best quality but more complex prompt engineering |

**Questions to answer:**
- How important is visual consistency for your use case?
- Will you use the same image generation model for all scenes?

### 4. Trailer Scene Selection Criteria

What makes a scene "trailer-worthy"?

| Criterion | Description |
|-----------|-------------|
| **Action balance** | Mix of action and dialogue scenes |
| **Character introductions** | Include hero/villain first appearances |
| **Plot coverage** | Key story beats without spoilers |
| **Visual variety** | Different locations, times of day, moods |
| **Emotional arc** | Build tension across selected scenes |
| **Duration targets** | Total trailer length (30s, 60s, 90s) |

**Questions to answer:**
- How many scenes should be selected? (typically 5-10)
- Should users be able to override AI selections?
- What's the target trailer duration?

### 5. Visual Description Format

How should character/setting descriptions be structured for image generation?

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **Freeform text** | Natural language descriptions | Flexible but inconsistent |
| **Structured JSON** | Fixed fields (hair, clothing, etc.) | Consistent but may miss nuances |
| **Template-based** | "A [age] [gender] with [hair] wearing [clothing]..." | Balance of structure and flexibility |

**Questions to answer:**
- What image generation API will Phase 2 use? (format should match)
- Should descriptions include style guidance (lighting, mood)?

## Implementation Steps

1. **Define Pydantic schemas** for agent outputs:
   ```python
   class ScriptAnalysisResult(BaseModel):
       title: str
       scenes: list[SceneData]
       characters: list[CharacterData]
       settings: list[SettingData]
   ```

2. **Implement agents** using the LLM client:
   ```python
   from app.core.llm import llm_client

   async def analyze_script(script_content: str) -> ScriptAnalysisResult:
       return await llm_client.invoke_structured(
           messages=[{"role": "user", "content": script_content}],
           output_schema=ScriptAnalysisResult,
           system=SCRIPT_ANALYSIS_PROMPT
       )
   ```

3. **Implement service.py** to orchestrate agents and save to database.

4. **Implement router.py** endpoints.

5. **Update project status** after each step:
   - `draft` → `parsing` → `parsed`

## Reference

See original implementations:
- `script_to_movie/server/scriptAnalyzer.ts`
- `script_to_movie/server/agents/ScriptAnalysisAgent.ts`
