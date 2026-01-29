# Script-to-Movie: Project Overview

## What is Script-to-Movie?

Script-to-Movie is an AI-powered platform that transforms screenplays into generated trailer videos. Upload a script, and the system will analyze it, create consistent visual representations of characters and settings, select key moments for a trailer, generate storyboard frames and videos, and assemble them into a final trailer.

**Core Value**: Rapid visualization of screenplay concepts without manual production work.

---

## The Pipeline

The system processes scripts through a multi-stage pipeline, with each stage handled by a specialized AI agent:

```
                    ┌─────────────────┐
                    │  Script Upload  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Script Analysis │
                    └────────┬────────┘
                             ↓
              ┌──────────────┴──────────────┐
              ↓                             ↓
    ┌─────────────────┐           ┌─────────────────┐
    │   Character     │           │    Setting      │
    │   Consistency   │           │   Consistency   │
    └────────┬────────┘           └────────┬────────┘
              └──────────────┬──────────────┘
                             ↓
                    ┌─────────────────┐
                    │ Trailer Scene   │
                    │   Selection     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  Storyboard     │
                    │    Frames       │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  Video Prompts  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Video Generation│
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Final Assembly  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  Trailer Video  │
                    └─────────────────┘
```

---

## Pipeline Stages

### 1. Script Analysis
**Purpose**: Parse the screenplay and understand its structure.

**What it does**:
- Extracts all scenes with descriptions
- Identifies characters and their traits
- Identifies settings/locations
- Determines narrative arc and themes
- Estimates duration

**Output**: Structured data (scenes, characters, settings, themes, narrative summary)

---

### 2. Character Consistency
**Purpose**: Create consistent visual descriptions for each character.

**What it does**:
- Generates detailed visual descriptions for each character
- Ensures the same character looks consistent across all scenes
- Defines appearance, clothing, distinguishing features

**Output**: Character profiles with visual descriptions

---

### 3. Setting Consistency
**Purpose**: Create consistent visual descriptions for each location.

**What it does**:
- Generates detailed visual descriptions for each setting
- Ensures locations maintain visual consistency
- Defines lighting, atmosphere, key visual elements

**Output**: Setting profiles with visual descriptions

---

### 4. Trailer Scene Selection
**Purpose**: Identify the most impactful moments for a trailer.

**What it does**:
- Analyzes the full story arc
- Selects 3-5 key scenes that represent the story
- Considers: opening hook, turning points, emotional peaks, climactic moments
- Balances variety (different settings, characters, moods)

**Output**: List of trailer-worthy scenes with rationale

---

### 5. Storyboard Frames
**Purpose**: Create visual representations of each trailer scene.

**What it does**:
- Generates detailed image prompts for each selected scene
- Incorporates character and setting visual consistency
- Includes scene description, framing, composition
- Specifies cinematic style (lighting, mood, camera angle)

**Output**: Storyboard images with scene descriptions

---

### 6. Video Prompts
**Purpose**: Optimize prompts for video generation.

**What it does**:
- Transforms storyboard frames into video-ready prompts
- Adds motion and camera movement descriptions
- Specifies duration and pacing
- Includes audio/atmosphere guidance

**Output**: Detailed video generation prompts

---

### 7. Video Generation
**Purpose**: Create video clips for each trailer scene.

**What it does**:
- Sends prompts to video generation API
- Generates one video clip per trailer scene
- Manages generation queue and status

**Output**: Video clips stored in S3

---

### 8. Final Assembly
**Purpose**: Combine clips into a complete trailer.

**What it does**:
- Orders video clips according to narrative flow
- Adds transitions between scenes
- Manages pacing and rhythm
- Produces final rendered trailer

**Output**: Complete trailer video

---

## Agent Architecture

Each pipeline stage is handled by a specialized AI agent:

| Agent | Responsibility |
|-------|----------------|
| **ScriptAnalysisAgent** | Parses screenplay structure, extracts scenes/characters/settings |
| **CharacterConsistencyAgent** | Creates and maintains consistent character visual descriptions |
| **SettingConsistencyAgent** | Creates and maintains consistent location visual descriptions |
| **TrailerSceneAgent** | Selects most impactful scenes for the trailer |
| **StoryboardPromptAgent** | Generates image prompts for storyboard visualization |
| **VideoPromptAgent** | Optimizes prompts for video generation |
| **VideoGenerationAgent** | Invokes video generation APIs and manages generation |
| **VideoAssemblyAgent** | Assembles final trailer from generated clips |

### How Agents Work

1. **Chain-of-Thought Reasoning**: Agents think step-by-step before producing output
2. **Structured Output**: Agents return JSON-validated responses
3. **Workflow Orchestration**: The WorkflowOrchestrator manages agent execution sequence
4. **Error Recovery**: Failed steps can be retried with refined prompts

---

## Data Flow

### What Gets Stored

| Stage | Database Storage | File Storage (S3) |
|-------|------------------|-------------------|
| Script Upload | Project record with raw script | - |
| Script Analysis | Scenes, characters, settings tables | - |
| Consistency | Updated character/setting descriptions | - |
| Trailer Selection | Marked trailer scenes | - |
| Storyboard | Storyboard image records | Storyboard images |
| Video Prompts | Video prompt records | - |
| Video Generation | Generated video records | Video clips |
| Assembly | Final movie record | Final trailer video |

### Database Schema (Key Tables)

- **projects**: Project metadata, script content, status, progress
- **scenes**: Individual scenes with descriptions, characters, settings
- **characters**: Character names and visual descriptions
- **settings**: Location names and visual descriptions
- **storyboardImages**: Generated storyboard images
- **videoPrompts**: Optimized video generation prompts
- **generatedVideos**: Video clips for each scene
- **finalMovies**: Assembled trailer videos

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Claude API (Anthropic) |
| **Backend** | Express.js, tRPC |
| **Database** | MySQL with Drizzle ORM |
| **Frontend** | React 19, Tailwind CSS 4 |
| **File Storage** | S3 (images and videos) |
| **Auth** | JWT with bcrypt password hashing |

---

## Project Structure

```
script_to_movie/
├── server/
│   ├── agents/           # AI agent implementations
│   │   ├── Agent.ts      # Base agent class
│   │   ├── ScriptAnalysisAgent.ts
│   │   ├── PromptOptimizer.ts
│   │   ├── WorkflowOrchestrator.ts
│   │   └── types.ts
│   ├── routers/          # tRPC API routes
│   ├── _core/            # Core utilities (LLM, auth, etc.)
│   └── db.ts             # Database queries
├── client/
│   └── src/              # React frontend
├── drizzle/
│   └── schema.ts         # Database schema
└── docs/                 # Documentation
```

---

## Getting Started

### Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...    # Claude API key
JWT_SECRET=your-secret          # For authentication
DATABASE_URL=mysql://...        # MySQL connection string
```

### Running the Project

```bash
# Install dependencies
pnpm install

# Run database migrations
pnpm db:push

# Start development server
pnpm dev
```

---

## Current Status

**Implemented**:
- Script Analysis Agent
- Prompt Optimizer
- Workflow Orchestrator
- Basic frontend with progress tracking
- Authentication system

**In Progress**:
- Character/Setting Consistency Agents
- Trailer Scene Selection
- Video generation integration

**Planned**:
- Storyboard generation
- Video assembly
- Advanced editing controls

---

## Related Documentation

- [AGENT_ARCHITECTURE.md](script_to_movie/AGENT_ARCHITECTURE.md) - Technical agent implementation details
- [AGENT_INTEGRATION_GUIDE.md](script_to_movie/AGENT_INTEGRATION_GUIDE.md) - Frontend integration patterns
- [todo.md](script_to_movie/todo.md) - Development roadmap
