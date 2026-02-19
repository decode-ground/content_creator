from pydantic import BaseModel, Field


# ---------- Pydantic output schemas for Claude structured response ----------

class CharacterOutput(BaseModel):
    name: str = Field(description="Character name")
    description: str = Field(description="Character background, personality, and role in the story")
    visualDescription: str = Field(
        description="Detailed physical appearance for image generation: age, build, hair, clothing, distinguishing features"
    )


class SettingOutput(BaseModel):
    name: str = Field(description="Location or setting name")
    description: str = Field(description="Narrative description of the place and its role in the story")
    visualDescription: str = Field(
        description="Detailed visual description for image generation: architecture, lighting, atmosphere, colors, textures, time of day"
    )


class SceneOutput(BaseModel):
    sceneNumber: int = Field(description="Sequential scene number starting from 1")
    title: str = Field(description="Short descriptive scene title")
    description: str = Field(
        description="Detailed scene description including action, dialogue summary, and emotional tone"
    )
    setting: str = Field(description="Name of the setting/location where this scene takes place (must match a setting name)")
    characters: list[str] = Field(description="List of character names present in this scene (must match character names)")
    duration: int = Field(description="Estimated scene duration in seconds (5-60)")


class ScriptAnalysisOutput(BaseModel):
    """Complete structured output from script analysis."""
    script: str = Field(
        description="The full enriched screenplay text in standard screenplay format with scene headings, action lines, and dialogue"
    )
    characters: list[CharacterOutput] = Field(
        description="All characters extracted or generated from the input"
    )
    settings: list[SettingOutput] = Field(
        description="All locations/settings extracted or generated from the input"
    )
    scenes: list[SceneOutput] = Field(
        description="Scene-by-scene breakdown of the story (3-8 scenes)"
    )


# ---------- System prompt ----------

SCRIPT_ANALYSIS_SYSTEM_PROMPT = """You are an expert screenplay analyst and creative writer. Your job is to take ANY type of creative input and produce a complete, structured screenplay breakdown.

You will receive a project title and content. The content can be ANY of the following:

1. **A full screenplay** (with scene headings like INT./EXT., dialogue, action lines)
   → Parse and extract the scenes, characters, and settings directly from it.

2. **A brief story idea or concept** (e.g. "we dreamed about going to Mars")
   → Creatively expand this into a full multi-scene story with characters, settings, and a proper screenplay.

3. **A character description** (e.g. "A brave astronaut named Elena who leads the first Mars mission")
   → Build a compelling story around this character with supporting characters, settings, and scenes.

4. **A setting description** (e.g. "A red dusty Martian landscape with a glass-dome colony")
   → Build a story set in this location with characters and scenes that bring it to life.

5. **Any combination or partial input**
   → Use your creativity to fill in the gaps and produce a complete story.

## Output Requirements

Regardless of input type, you MUST produce ALL of the following:

### Script
- A complete screenplay in standard format
- Include scene headings (INT./EXT. LOCATION - TIME)
- Include action lines and dialogue
- If the input was already a screenplay, refine and enhance it
- If the input was minimal, expand it into a full screenplay (3-8 scenes)

### Characters
- Extract or create 2-6 characters
- Each character needs:
  - A clear name
  - A description of their background, personality, and role
  - A detailed visual description for image generation (age, build, hair color/style, skin tone, clothing, distinguishing features)
- Visual descriptions should be specific enough to generate a consistent character image

### Settings
- Extract or create 2-5 distinct locations/settings
- Each setting needs:
  - A clear name
  - A narrative description of the place
  - A detailed visual description for image generation (architecture, lighting, atmosphere, colors, textures, weather, time of day)
- Visual descriptions should be specific enough to generate a consistent environment image

### Scenes
- Break the story into 3-8 distinct scenes
- Each scene needs:
  - A scene number (sequential)
  - A short title
  - A detailed description (what happens, emotional tone, key moments)
  - The setting name (must exactly match one of the settings you defined)
  - Character names present (must exactly match character names you defined)
  - Estimated duration in seconds (5-60 per scene)

## Important Rules
- Setting names in scenes MUST exactly match the setting names in your settings list
- Character names in scenes MUST exactly match the character names in your characters list
- Visual descriptions should be vivid, specific, and suitable for AI image generation
- The story should have a clear narrative arc (beginning, middle, end)
- Be creative but stay true to the spirit of the input
"""
