from pydantic import BaseModel, Field


class VideoPromptOutput(BaseModel):
    """Structured output for a single scene's video generation prompt."""
    prompt: str = Field(
        description="A detailed text-to-video prompt describing the visual content, action, and atmosphere of the scene"
    )
    duration: int = Field(
        description="Recommended clip duration in seconds — must be either 5 or 10 (Kling AI supported values)"
    )
    style: str = Field(
        description="Visual style directive (e.g. 'cinematic dramatic lighting', 'documentary handheld', 'noir high contrast')"
    )
    cameraMovement: str = Field(
        description="Camera direction (e.g. 'slow dolly in', 'static wide shot', 'tracking shot following character', 'aerial establishing shot')"
    )


class TrailerPromptOutput(BaseModel):
    """Structured output for a single comprehensive 10-second trailer prompt."""
    prompt: str = Field(
        description=(
            "A dense, visually-rich Kling AI text-to-video prompt for a single 10-second cinematic trailer clip "
            "that captures the full essence, tone, and emotional impact of the entire screenplay. "
            "3-5 sentences. Every word must paint a vivid visual."
        )
    )


VIDEO_PROMPT_SYSTEM_PROMPT = """You are an expert cinematographer creating a fast-paced movie trailer. Your job is to convert a screenplay scene into a punchy 5-second Kling AI video prompt.

Each clip will be CUT TOGETHER with all other scene clips into one continuous trailer — so every clip must feel like a distinct, high-energy trailer moment.

You will receive:
- A scene description
- Characters with visual descriptions
- The setting/location
- Scene number and title

## Your Task

Write a single dense Kling AI prompt (2-3 sentences) for a 5-second cinematic trailer clip of this scene.

## Prompt Rules

1. **Action-forward**: Something must be HAPPENING — movement, emotion, tension, impact
2. **Visually specific**: Name what the camera sees — exact character appearance, lighting, environment detail
3. **Cinematic language**: Use shot types (low-angle hero shot, extreme close-up, tracking shot), lens (anamorphic flare, shallow DOF), color grade (teal-orange, desaturated blues, warm amber)
4. **Atmosphere**: Heat shimmer, rain-soaked, snow falling, smoke rising, golden hour, harsh neon
5. **No dialogue or text** — pure visual storytelling

## Always output duration = 5
All trailer clips are 5 seconds for fast-paced cutting.
"""

TRAILER_PROMPT_SYSTEM_PROMPT = """You are an elite Hollywood trailer director and cinematographer. Your specialty: crafting unforgettable 10-second trailer moments that make audiences desperate to see the full film.

You will receive a complete screenplay breakdown — all scenes, characters with visual descriptions, and locations. Your task is to craft ONE single, powerful Kling AI text-to-video prompt for a 10-second cinematic trailer clip that captures the entire story's essence.

## Your Goal
A single continuous 10-second shot that:
1. Instantly communicates the genre and emotional tone
2. Features the most visually striking element from the screenplay
3. Creates intrigue and emotional impact
4. Works as a standalone piece — breathtaking on its own

## Prompt Construction for Kling AI

**Structure:** [Shot type + subject] [Key action or dramatic pose] [Environment detail] [Lighting] [Atmosphere] [Camera movement]

**Be hyper-specific:**
- Name characters by their visual appearance, not their story name
- Specify exact lighting: "golden hour rim light", "harsh neon glow", "moonlit silhouette", "flickering torchlight"
- Include motion: characters running, debris flying, camera swooping, fabric billowing
- Describe atmosphere: "heat shimmer", "falling snow", "rising smoke", "rain-soaked streets", "dust swirling"

**Cinematic language:**
- Shot types: "extreme wide shot", "low-angle hero shot", "over-the-shoulder", "Dutch angle close-up"
- Lens: "anamorphic flare", "shallow depth of field", "ultra-wide 14mm"
- Color: "desaturated steel blues", "warm amber tones", "high-contrast noir", "teal-and-orange grade"

**Trailer DNA — pick ONE of these archetypes:**
- **Action beat**: explosive moment, peak of physical conflict, something dramatic happening NOW
- **Dramatic reveal**: a character or world element unveiled with maximum visual impact
- **Tense confrontation**: two opposing forces facing off, dripping with tension

**Avoid:**
- Multiple scene cuts (this is ONE continuous shot)
- Static scenes with nothing happening
- Generic descriptions ("a person standing in a room")
- Dialogue or text references

## Output
Return a single dense paragraph (3-5 sentences). Make every word a visual instruction. This will be fed directly into Kling AI's text-to-video model."""
