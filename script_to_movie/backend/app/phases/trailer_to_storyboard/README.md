# Phase 2: Trailer to Storyboard

## Role

Generates storyboard images for the selected trailer scenes. Transforms text descriptions into visual frames.

## Pipeline Position

```
[Script to Trailer] → [THIS PHASE] → [Storyboard to Movie]
```

## Input

- Selected trailer scenes (from Phase 1)
- Character visual descriptions
- Setting visual descriptions

## Output

- Storyboard images for each trailer scene
- Image prompts used for generation

## Endpoints to Implement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/phases/trailer-to-storyboard/{project_id}/generate` | POST | Generate storyboard frames |
| `/api/phases/trailer-to-storyboard/{project_id}/status` | GET | Check generation status |

## Files to Implement

| File | Responsibility |
|------|----------------|
| `agents/storyboard_prompt.py` | Generate optimized image prompts |
| `image_generator.py` | Call image generation API, upload to S3 |
| `service.py` | Orchestrate prompt generation and image creation |
| `router.py` | API endpoints |

## Design Decisions

### 1. Image Generation API

Which API should power image generation?

| API | Pros | Cons | Cost |
|-----|------|------|------|
| **DALL-E 3** | High quality, excellent prompt following, safe outputs | Rate limits, less artistic control | ~$0.04-0.12/image |
| **Midjourney** (via proxy) | Best artistic quality, distinctive style | No official API, requires Discord bot or proxy | ~$0.02-0.05/image |
| **Stable Diffusion XL** (Replicate) | Cost-effective, customizable, many models | Variable quality, requires prompt tuning | ~$0.002-0.01/image |
| **Ideogram** | Good text rendering, stylistic control | Newer API, less tested at scale | ~$0.02-0.08/image |
| **Leonardo.ai** | Cinematic presets, fine-tuned models | API availability varies | ~$0.01-0.03/image |
| **Flux** (via Replicate/fal.ai) | High quality, fast, good prompt adherence | Newer model | ~$0.003-0.02/image |

**Dependency to add** (choose one):
```toml
"openai>=1.0.0",        # For DALL-E 3
"replicate>=0.15.0",    # For Replicate-hosted models
"httpx>=0.26.0",        # For direct API calls to any service
```

**Questions to answer:**
- What's your budget per trailer?
- How important is artistic quality vs. speed?
- Do you need consistent style across all images?

### 2. Image Consistency Strategy

How do you maintain visual consistency for characters across multiple images?

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **Prompt engineering only** | Detailed character descriptions in every prompt | Simple but characters may drift between images |
| **Seed locking** | Use same random seed for style consistency | Limited control, same seed ≠ same character |
| **Reference images (img2img)** | Use previous images as style/character reference | More consistent but requires API support |
| **IP-Adapter / ControlNet** | Use face/pose reference images | Best consistency but complex setup |
| **Fine-tuned model** | Train LoRA on character reference images | Most consistent but expensive and slow |
| **Character sheets** | Generate character reference sheet first, use in prompts | Good balance, adds extra step |

**Questions to answer:**
- How critical is character consistency for your use case?
- Are you willing to add preprocessing steps?
- Does your chosen API support image-to-image or reference features?

### 3. Prompt Construction Strategy

How should scene descriptions become image prompts?

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **Template-based** | Fixed structure: "[scene], [character], [setting], [style]" | Predictable results but rigid |
| **LLM-generated** | Claude writes optimized prompts for chosen API | Flexible, API-optimized but variable |
| **Hybrid** | Template structure with LLM-filled creative details | Good balance of control and creativity |

**Prompt components to consider:**
- Scene action/composition
- Character appearance and position
- Setting/environment details
- Lighting and mood
- Camera angle (wide shot, close-up, etc.)
- Art style guidance (cinematic, photorealistic, etc.)
- Negative prompts (what to avoid)

### 4. Image Specifications

| Specification | Options | Recommendation |
|---------------|---------|----------------|
| **Aspect ratio** | 1:1, 16:9, 2.35:1 (cinemascope) | 16:9 for video compatibility |
| **Resolution** | 1024x576, 1280x720, 1920x1080 | Match target video resolution |
| **Format** | PNG (lossless), JPEG (smaller) | PNG for quality, JPEG for storage |
| **Images per scene** | 1 (key moment) or 2-3 (sequence) | 1 for speed, more for storyboard detail |

### 5. Error Handling Strategy

What happens when image generation fails?

| Scenario | Strategy |
|----------|----------|
| **API timeout** | Retry with exponential backoff (3 attempts) |
| **Content filter rejection** | Modify prompt (remove flagged terms), retry |
| **Rate limit hit** | Queue and delay, or fallback to secondary API |
| **Low quality result** | Optional: use LLM to evaluate, regenerate if poor |
| **Partial failure** | Save successful images, mark failed scenes for retry |

**Questions to answer:**
- Should users be able to regenerate individual images?
- Do you need a fallback API if primary fails?
- How do you handle content moderation rejections?

### 6. Background Processing

Image generation takes 10-60 seconds per image. Choose an approach:

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **Sequential in request** | Generate one by one, return when done | Simple but long HTTP timeout risk |
| **Parallel generation** | Generate all images concurrently | Faster but may hit rate limits |
| **Background job** | Queue generation, poll for status | Best UX but more infrastructure |
| **WebSocket/SSE updates** | Real-time progress streaming | Best UX, more complex frontend |

**Questions to answer:**
- How many images per trailer (affects total time)?
- What's acceptable wait time for users?
- Do you need real-time progress updates?

## Implementation Steps

1. **Set up image generation client** in `image_generator.py`:
   ```python
   from openai import AsyncOpenAI

   client = AsyncOpenAI()

   async def generate_image(prompt: str) -> bytes:
       response = await client.images.generate(
           model="dall-e-3",
           prompt=prompt,
           size="1024x1024",
           response_format="url"
       )
       # Download and return image bytes
   ```

2. **Implement storyboard prompt agent**:
   - Combine scene description + character visuals + setting visuals
   - Optimize for image generation (cinematic style, composition, lighting)

3. **Implement service.py**:
   - Generate prompts for each trailer scene
   - Call image generator
   - Upload to S3 via `app/core/storage.py`
   - Save StoryboardImage records

4. **Update project status**: `parsed` → `generating_storyboard`

## Reference

See original implementation: `script_to_movie/server/imageGenerator.ts`
