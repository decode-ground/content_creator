# Developer Guide — Script-to-Movie

A complete guide for setting up, understanding, and working on this project. Written for people who are new to development and will be using **Claude Code** as their main tool.

This guide follows the full product development cycle in three stages:

| Stage | Goal | Definition of Done |
|-------|------|--------------------|
| **Stage 1** | Build the app locally with mock videos | All phases run end-to-end; the pipeline is complete; no real video API calls needed |
| **Stage 2** | Integrate the video generation API and validate quality | Real video clips are generated; output meets quality bar for script accuracy, character consistency, and scene coverage; pipeline is resilient, cost-aware, and shows meaningful errors to users |
| **Stage 2.5** | Staging environment | Full end-to-end test in a cloud environment before real users touch it |
| **Stage 3** | Deploy to production on AWS | The app runs in the cloud and is accessible to users |
| **Stage 4** | Integrate with Decode Shorts | Script-to-Movie features are connected to the Decode Shorts app and work as part of the broader product |

Do not move to the next stage until the current one is fully working.

---

## Table of Contents

1. [What This App Does](#what-this-app-does)
2. [How the Tech Stack Works](#how-the-tech-stack-works)
3. [Stage 1 — Build Locally with Mock Videos](#stage-1--build-locally-with-mock-videos)
   - [Install Prerequisites](#install-prerequisites)
   - [Set Up the Project](#set-up-the-project)
   - [Project Structure](#project-structure)
   - [How the Pipeline Works](#how-the-pipeline-works)
   - [Working on a Phase](#working-on-a-phase)
   - [What "Mock Videos" Means](#what-mock-videos-means)
   - [Stage 1 Completion Checklist](#stage-1-completion-checklist)
4. [Stage 2 — API Integration and Quality Validation](#stage-2--api-integration-and-quality-validation)
   - [Enable Real Video Generation](#enable-real-video-generation)
   - [Quality Criteria](#quality-criteria)
   - [Prompt Engineering Guide](#prompt-engineering-guide)
   - [Error Handling and Resilience](#error-handling-and-resilience)
   - [Cost and Rate Limit Awareness](#cost-and-rate-limit-awareness)
   - [User-Facing Error States](#user-facing-error-states)
   - [Stage 2 Completion Checklist](#stage-2-completion-checklist)
5. [Stage 2.5 — Staging Environment](#stage-25--staging-environment)
6. [Stage 3 — Deploy to Production](#stage-3--deploy-to-production)
7. [Stage 4 — Integrate with Decode Shorts](#stage-4--integrate-with-decode-shorts)
8. [Reference](#reference)
   - [Using Claude Code](#using-claude-code)
   - [Common Tasks](#common-tasks)
   - [Database Guide](#database-guide)
   - [API Reference](#api-reference)
   - [Troubleshooting](#troubleshooting)

---

## What This App Does

Script-to-Movie takes a screenplay (plain text) and turns it into a generated movie using AI. It runs through three phases:

```
Screenplay text
    ↓
Phase 1: Parse the script → extract scenes, characters, settings → generate trailer video
    ↓
Phase 2: Take trailer frames → validate and enhance them into a quality storyboard
    ↓
Phase 3: Turn storyboard images into video clips → add voice audio → assemble final movie
    ↓
Completed MP4 movie
```

The frontend is a React web app where users paste their script and watch the pipeline run. The backend is a Python API that runs the AI pipeline.

---

## How the Tech Stack Works

If you're new to development, here's what each technology does:

### Backend (the brain)

| Technology | What it does | Think of it as |
|-----------|-------------|----------------|
| **Python** | The programming language for the backend | The language everyone speaks |
| **FastAPI** | Web framework — turns Python functions into API endpoints | The waiter that takes orders from the frontend |
| **SQLAlchemy** | Talks to the database using Python code instead of SQL | A translator between Python and MySQL |
| **Alembic** | Manages database schema changes (migrations) | A version control system for your database tables |
| **MySQL** | The database — stores all project data | A spreadsheet with linked tables |
| **boto3** | AWS SDK — uploads files to S3 | The courier that delivers files to cloud storage |

### Frontend (the face)

| Technology | What it does | Think of it as |
|-----------|-------------|----------------|
| **React** | UI framework — builds the web interface | The painter that draws what users see |
| **TypeScript** | JavaScript with type safety | JavaScript but it catches your mistakes |
| **Tailwind CSS** | Styling with utility classes | Pre-made design building blocks |
| **React Query** | Handles API calls and caching | A smart assistant that fetches data and remembers it |
| **tRPC** | Type-safe API communication | A direct phone line between frontend and server |
| **Vite** | Build tool — bundles the frontend for the browser | The compiler that packages everything up |

### AI Services (the magic)

| Service | What it does | Stage introduced |
|---------|-------------|-----------------|
| **Claude API (Anthropic)** | Parses scripts, generates prompts, analyzes scenes | Stage 1 |
| **gTTS** | Converts dialogue text into spoken audio | Stage 1 |
| **ffmpeg** | Merges audio + video, concatenates clips into final movie | Stage 1 |
| **Kling AI** | Generates video clips from images + text prompts | Stage 2 |

---

## Stage 1 — Build Locally with Mock Videos

**Goal:** Get the entire pipeline running end-to-end on your local machine. Every phase should be wired up, every endpoint should respond, and a test project should complete all three phases — but instead of calling the Kling AI video generation API, you return mock/placeholder video files.

This lets you build and test the full pipeline logic, database writes, and UI without spending API credits or waiting for real video generation.

---

### Install Prerequisites

You need these installed on your machine before you can run the app.

#### 1. Python 3.11+

```bash
# macOS
brew install python@3.11

# Verify
python3.11 --version
```

#### 2. Node.js 20+ and pnpm

```bash
# macOS
brew install node

# Install pnpm (the package manager this project uses)
npm install -g pnpm

# Verify
node --version
pnpm --version
```

#### 3. MySQL

```bash
# macOS
brew install mysql
brew services start mysql

# Verify it's running
mysql -u root -e "SELECT 1"
```

If `mysql` asks for a password and you haven't set one, try:

```bash
mysql -u root --password="" -e "SELECT 1"
```

#### 4. ffmpeg (required for Phase 3 video assembly)

```bash
# macOS
brew install ffmpeg

# Verify
ffmpeg -version
```

#### 5. Git

```bash
# macOS (usually pre-installed)
git --version

# If not installed
brew install git
```

---

### Set Up the Project

#### Step 1: Clone the repo

```bash
git clone YOUR_REPO_URL script-to-movie
cd script-to-movie
```

#### Step 2: Create the MySQL database

```bash
mysql -u root -e "CREATE DATABASE script_to_movie;"
```

#### Step 3: Set up the backend

```bash
cd script_to_movie/backend

# Create a virtual environment (an isolated Python installation for this project)
python3.11 -m venv .venv

# Activate it (you'll need to do this every time you open a new terminal)
source .venv/bin/activate

# Install all Python dependencies
pip install -e ".[dev]"

# Create your .env file from the example
cp .env.example .env
```

#### Step 4: Fill in your `.env` file

Open `script_to_movie/backend/.env`. For Stage 1 you only need three values:

```bash
# Database — connects to your local MySQL
DATABASE_URL=mysql+aiomysql://root:@localhost:3306/script_to_movie
# If your MySQL root has a password: root:yourpassword@

# JWT — used to sign authentication tokens
# Generate one: openssl rand -hex 32
JWT_SECRET=paste-a-long-random-string-here

# Claude API — required for script parsing and prompt generation
# Get your key at: https://console.anthropic.com → API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Leave these blank for now — they are Stage 2 (Kling) and Stage 3 (AWS)
KLING_API_KEY=
KLING_SECRET_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=

# App settings
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

**Minimum to get started:** `DATABASE_URL`, `JWT_SECRET`, and `ANTHROPIC_API_KEY`. Leave everything else blank until Stage 2.

#### Step 5: Run database migrations

This creates all the tables in your MySQL database:

```bash
# Make sure you're in script_to_movie/backend with venv activated
alembic upgrade head
```

#### Step 6: Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

`--reload` means the server restarts automatically when you change code. You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Open http://localhost:8000/docs — this is the interactive API documentation where you can test every endpoint.

#### Step 7: Set up and start the frontend

Open a **new terminal** (keep the backend running in the first one):

```bash
cd script-to-movie/script_to_movie

# Install frontend dependencies
pnpm install

# Start the development server
pnpm dev
```

Open http://localhost:5173 — you should see the app.

#### You're running

- Backend API: http://localhost:8000 (Swagger docs: http://localhost:8000/docs)
- Frontend: http://localhost:5173
- MySQL database with all tables created

---

### Project Structure

```
script_to_movie/
├── backend/                        ← Python backend (FastAPI)
│   ├── .env                        ← Your local config (API keys, database URL)
│   ├── .env.example                ← Template for .env
│   ├── alembic/                    ← Database migration files
│   ├── alembic.ini                 ← Migration config
│   ├── CLAUDE.md                   ← Backend developer reference
│   └── app/
│       ├── main.py                 ← App entry point (registers all routes)
│       ├── config.py               ← Reads .env into a Settings object
│       ├── core/                   ← Shared infrastructure (DO NOT MODIFY)
│       │   ├── database.py         ←   Database connection + session management
│       │   ├── security.py         ←   JWT token creation + password hashing
│       │   ├── dependencies.py     ←   FastAPI auth dependency (get_current_user)
│       │   ├── llm.py              ←   Claude API client wrapper
│       │   └── storage.py          ←   S3 upload/download client
│       ├── models/                 ← Database table definitions (DO NOT MODIFY)
│       │   ├── project.py          ←   projects table
│       │   ├── scene.py            ←   scenes table
│       │   ├── character.py        ←   characters table
│       │   ├── setting.py          ←   settings table
│       │   ├── storyboard.py       ←   storyboardImages table
│       │   ├── video.py            ←   videoPrompts + generatedVideos tables
│       │   ├── final_movie.py      ←   finalMovies table
│       │   └── user.py             ←   users table
│       ├── schemas/                ← API request/response shapes (DO NOT MODIFY)
│       ├── auth/                   ← Login/register endpoints (DO NOT MODIFY)
│       ├── projects/               ← Project CRUD endpoints (DO NOT MODIFY)
│       └── phases/                 ← THE PIPELINE — this is where you work
│           ├── base_agent.py       ←   Base class all agents inherit from
│           ├── script_to_trailer/      ← Phase 1
│           ├── trailer_to_storyboard/  ← Phase 2
│           └── storyboard_to_movie/    ← Phase 3
│
├── server/                         ← Node.js/Express backend (tRPC server)
├── client/                         ← React frontend
├── shared/                         ← Types shared between frontend and server
├── AGENT_ARCHITECTURE.md           ← How the agent system works
├── AGENT_INTEGRATION_GUIDE.md      ← How frontend talks to backend
├── AWS_SETUP_GUIDE.md              ← Deploying to AWS (Stage 3)
└── todo.md                         ← What's been built and what's left
│
├── README.md                       ← (repo root) Project overview and quick start
└── DEVELOPER_GUIDE.md              ← (repo root) Full development lifecycle guide
```

#### What can I modify?

| Directory | Can I modify it? |
|-----------|-----------------|
| `app/core/` | No — shared infrastructure, fully built |
| `app/models/` | No — database tables, shared by all phases |
| `app/schemas/` | No — API shapes, shared by all phases |
| `app/auth/` | No — auth system, fully built |
| `app/projects/` | No — project CRUD, fully built |
| `app/phases/base_agent.py` | No — base class, shared |
| `app/phases/script_to_trailer/` | Yes — if you're the Phase 1 developer |
| `app/phases/trailer_to_storyboard/` | Yes — if you're the Phase 2 developer |
| `app/phases/storyboard_to_movie/` | Yes — if you're the Phase 3 developer |

---

### How the Pipeline Works

#### The Agent Pattern

Every piece of work in the pipeline is done by an **agent**. An agent is a Python class that:

1. **Reads** data from the database
2. **Processes** it (calls an AI API, runs ffmpeg, etc.)
3. **Writes** the results back to the database
4. **Returns** a summary dict

```python
from app.phases.base_agent import BaseAgent

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my_agent"

    async def execute(self, db: AsyncSession, project_id: int) -> dict:
        # 1. Read from database
        result = await db.execute(
            select(Scene).where(Scene.projectId == project_id)
        )
        scenes = list(result.scalars().all())

        # 2. Process (example: call Claude API)
        response = await self.llm.invoke(
            messages=[{"role": "user", "content": "Analyze this scene..."}],
            system="You are a screenplay analyst.",
        )

        # 3. Write results back
        project.status = "analyzed"
        await db.commit()

        # 4. Return summary
        return {"status": "success", "message": "Analyzed 5 scenes"}
```

#### How phases communicate

Phases **never import code from each other**. They communicate through the database only:

```
Phase 1 writes Scene records → Phase 2 reads Scene records
Phase 2 writes StoryboardImage records → Phase 3 reads StoryboardImage records
Phase 3 writes FinalMovie record → Frontend reads FinalMovie record
```

#### The database tables

```
users ──────────────────────────────────────────────────────
projects ──┬── scenes ──┬── storyboardImages
            │            ├── videoPrompts
            │            └── generatedVideos
            ├── characters
            ├── settings
            └── finalMovies
```

---

### Working on a Phase

#### Before you start

1. Read your phase's `README.md` — it explains what your phase does, what inputs you receive, and what outputs you produce
2. Read your phase's `PLAN.md` — it has a task checklist
3. Read `backend/CLAUDE.md` — it has code examples for every shared module

#### Phase directory structure

Each phase follows the same layout:

```
phases/your_phase/
├── README.md           ← What this phase does (read first)
├── PLAN.md             ← Task checklist
├── __init__.py         ← Empty file (Python needs this)
├── prompts.py          ← LLM prompt strings
├── service.py          ← Wires agents together, called by the API
├── router.py           ← API endpoints (already created)
└── agents/             ← Your agents go here
    ├── __init__.py
    └── your_agent.py
```

#### Development workflow

1. **Read the existing code** — understand what's already built
2. **Start with the simplest agent** — get one working before building the next
3. **Test through the API** — use the Swagger docs at http://localhost:8000/docs or curl
4. **Check the database** — verify your agent wrote the correct data
5. **Move to the next agent** — build on what works

---

### What "Mock Videos" Means

During Stage 1, the video generation agent (Phase 3) should **not** call the Kling AI API. Instead, it should return a placeholder so the rest of the pipeline — database writes, audio generation, ffmpeg assembly, frontend display — can be fully built and tested.

#### How to implement a mock

In your Phase 3 video generation agent, add a `MOCK_VIDEO` flag:

```python
# agents/video_generator.py

MOCK_VIDEO = True  # Set to False in Stage 2

MOCK_VIDEO_URL = "https://www.w3schools.com/html/mov_bbb.mp4"
# Or use a local file: "media/mock/placeholder.mp4"

async def execute(self, db: AsyncSession, project_id: int) -> dict:
    scenes = await self._get_scenes(db, project_id)

    for scene in scenes:
        if MOCK_VIDEO:
            video_url = MOCK_VIDEO_URL
        else:
            video_url = await self._call_kling_api(scene)  # Stage 2

        # Write to database either way — same code path
        video = GeneratedVideo(
            sceneId=scene.id,
            projectId=project_id,
            videoUrl=video_url,
            status="completed",
        )
        db.add(video)

    await db.commit()
    return {"status": "success", "videos_generated": len(scenes)}
```

This means your ffmpeg assembly, audio merging, and frontend video player are all tested with real data flow — just with a placeholder clip instead of a real generated one.

#### What to verify in Stage 1 with mocks

- Every scene gets a `GeneratedVideo` record in the database
- The `video_assembly` agent correctly fetches those records and assembles them
- The final MP4 file is written to disk (or the `media/` folder)
- The `FinalMovie` record is created with the correct `movieUrl`
- The frontend correctly displays the pipeline progress and final video

---

### Stage 1 Completion Checklist

Before moving to Stage 2, verify every item below works:

**Setup**
- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:5173
- [ ] Database migrations ran successfully
- [ ] You can register a user, log in, and the session cookie works

**Phase 1**
- [ ] POST `/api/phases/script-to-trailer/{id}/parse` succeeds
- [ ] `scenes`, `characters`, and `settings` rows are written to the database for the correct project
- [ ] POST `/api/phases/script-to-trailer/{id}/generate-trailer` succeeds
- [ ] A storyboard image record is created for the trailer frame

**Phase 2**
- [ ] POST `/api/phases/trailer-to-storyboard/{id}/generate` succeeds
- [ ] `storyboardImages` rows are written with image URLs

**Phase 3 (with mock videos)**
- [ ] POST `/api/phases/storyboard-to-movie/{id}/prompts` succeeds
- [ ] `videoPrompts` rows are written for each scene
- [ ] POST `/api/phases/storyboard-to-movie/{id}/generate` returns mock video URLs for every scene
- [ ] `generatedVideos` rows are written with `status = "completed"`
- [ ] POST `/api/phases/storyboard-to-movie/{id}/assemble` runs ffmpeg and creates a final MP4
- [ ] `finalMovies` row is written with the correct `movieUrl`
- [ ] The MP4 file exists on disk

**End-to-end**
- [ ] POST `/api/workflow/{id}/start` runs all three phases automatically
- [ ] Frontend shows real-time pipeline progress
- [ ] Frontend displays the final video

Once every item is checked, move to Stage 2.

---

## Stage 2 — API Integration and Quality Validation

**Goal:** Replace mock videos with real Kling AI generations, then validate that the output meets the quality bar for this project. This is also where you tune your prompts.

---

### Enable Real Video Generation

#### Step 1: Get Kling AI credentials

Get your API key and secret key from the Kling AI dashboard and add them to your `.env`:

```bash
KLING_API_KEY=your-key
KLING_SECRET_KEY=your-secret
```

#### Step 2: Flip the mock flag

In your Phase 3 video generation agent, set:

```python
MOCK_VIDEO = False
```

This routes the same code path through `_call_kling_api()` instead of returning the placeholder URL.

#### Step 3: Run a test project end-to-end

Use the short test script from the Common Tasks section and run the full pipeline:

```bash
curl -X POST http://localhost:8000/api/workflow/1/start -b cookies.txt
```

Watch the logs. When the pipeline completes, open the output video.

---

### Quality Criteria

For this project, generated video output must meet three standards. Review each generated video against all three before considering Stage 2 complete.

#### 1. Script Accuracy

Every generated clip should visually reflect what the script describes for that scene.

Check for:
- Does the setting match? (indoor/outdoor, time of day, location type)
- Do the described actions actually happen in the clip?
- Is the mood or tone consistent with the scene's dialogue and direction?

If clips are consistently off from the script, the problem is usually in **Phase 1 parsing** (the scene `description` field is too vague) or in the **Phase 3 video prompt** (the prompt passed to Kling doesn't include enough specificity).

#### 2. Character Consistency

The same character should look visually consistent across all scenes.

Check for:
- Does the character's appearance (hair, clothing, face) stay the same across clips?
- Are there jarring visual discontinuities between scenes featuring the same character?

Character consistency depends on how well the `visualDescription` field is written in the `characters` table, and how that description is embedded in each scene's video prompt. If consistency is poor, strengthen the character description injection in your Phase 3 prompt generation agent.

#### 3. Scene Coverage

There must be a generated video for **every scene** in the script. No scene should be missing or skipped.

Check for:
```bash
# Count scenes vs generated videos for a project
mysql -u root script_to_movie -e "
  SELECT
    (SELECT COUNT(*) FROM scenes WHERE projectId = 1) AS total_scenes,
    (SELECT COUNT(*) FROM generatedVideos WHERE projectId = 1 AND status = 'completed') AS completed_videos;
"
```

The two numbers must match. If any scene is missing a video, the assembly step will produce a gap or fail. Debug the generation loop in your Phase 3 agent to ensure it iterates every scene.

---

### Prompt Engineering Guide

Prompts live in each phase's `prompts.py`. Iterate on these to improve quality.

#### General principles

- **Be concrete.** Replace vague words like "a dramatic scene" with specific visual descriptions: "a dimly lit warehouse at night, a single overhead lamp, long shadows on concrete floors."
- **Embed character descriptions.** Every video prompt should include the visual description of all characters appearing in that scene. Do not rely on Kling to remember characters across clips.
- **Specify camera style.** Add cinematic direction: "medium shot," "slow dolly forward," "handheld," "wide establishing shot." This improves visual coherence across clips.
- **Control duration.** Short scenes (dialogue exchanges) work well at 3–5 seconds. Action or establishing scenes can go 6–10 seconds.

#### Improving Phase 1 scene descriptions

The `description` field on each `Scene` is the foundation for everything downstream. If it is thin, everything downstream suffers.

In your Phase 1 parsing prompt (`script_to_trailer/prompts.py`), instruct Claude to write scene descriptions that include:
- Location and time of day
- All characters present and what they are doing
- Lighting and atmosphere
- The emotional tone

Example of a weak description:
> "Alice and Bob argue in the kitchen."

Example of a strong description:
> "Alice stands at the kitchen counter, arms crossed, facing away from Bob. Bob stands in the doorway, hands raised in a pleading gesture. Morning light streams through the window behind Alice, casting her in silhouette. The atmosphere is tense and unresolved."

#### Improving Phase 3 video prompts

In your Phase 3 prompt generation agent, construct each video prompt by combining:

1. The scene's `description` (from Phase 1)
2. The visual descriptions of all characters in the scene (from the `characters` table)
3. The setting's visual description (from the `settings` table)
4. A consistent cinematic style instruction applied to every prompt

```python
video_prompt = f"""
{scene.description}

Characters present: {character_descriptions}
Setting: {setting.visualDescription}

Cinematic style: film grain, warm color grade, natural lighting, shallow depth of field.
"""
```

#### Iteration workflow

1. Run the full pipeline on a short test script (3–5 scenes)
2. Review the output video against the three quality criteria above
3. Identify which criterion fails most often
4. Edit the relevant `prompts.py` file
5. Reset the project and run again (see Common Tasks — Reset a project)
6. Repeat until all three criteria pass consistently

---

### Error Handling and Resilience

Video generation APIs fail. They time out, return partial results, and occasionally drop requests. Before Stage 2 is complete, your pipeline must handle these failures gracefully — a single bad clip should never silently break the whole pipeline or leave a project stuck with no way to recover.

#### What to implement

**Per-scene retry logic**

In your Phase 3 video generation agent, wrap each Kling API call in a retry loop. On failure, wait and try again before marking the scene as failed:

```python
import asyncio

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

for attempt in range(MAX_RETRIES):
    try:
        video_url = await self._call_kling_api(scene)
        break  # success — exit retry loop
    except Exception as e:
        if attempt == MAX_RETRIES - 1:
            # All retries exhausted — mark scene as failed, continue to next scene
            video.status = "failed"
            video.errorMessage = str(e)
        else:
            await asyncio.sleep(RETRY_DELAY_SECONDS)
```

**Never fail the whole pipeline for one scene**

If a scene's video fails after all retries, log the error and continue to the next scene. The assembly step should handle missing clips gracefully (skip them or use a placeholder) rather than crashing.

**Persist error state in the database**

Failed scenes should be recorded with `status = "failed"` and an `errorMessage` in the `generatedVideos` table. This lets users and developers see exactly what failed without digging through logs.

**Make failures resumable**

The generation loop should skip scenes that already have a `status = "completed"` video. This way, if a pipeline run is interrupted halfway through, you can re-trigger generation and it picks up from where it left off instead of re-generating (and re-paying for) clips that already succeeded.

```python
# Skip scenes that already have a completed video
existing = await db.execute(
    select(GeneratedVideo).where(
        GeneratedVideo.sceneId == scene.id,
        GeneratedVideo.status == "completed"
    )
)
if existing.scalar_one_or_none():
    continue  # already done, skip
```

---

### Cost and Rate Limit Awareness

Kling AI charges per second of video generated. A single long script can trigger dozens of API calls in one pipeline run, and costs can add up quickly if you're not paying attention.

#### Know your per-run cost

Before running against a full script, estimate the cost:

```
Number of scenes × average clip duration (seconds) × Kling price per second = estimated cost per run
```

Always run Stage 2 testing against **short scripts (3–5 scenes)** first. Only scale to longer scripts once the pipeline is stable and prompts are tuned.

#### Respect Kling's rate limits

Kling AI enforces rate limits on concurrent requests. If you fire all scene generations in parallel, you will likely hit these limits and get errors. Generate clips **sequentially** (one at a time) or with a small concurrency limit (2–3 at most) to stay within the API's limits:

```python
# Sequential — safest during development
for scene in scenes:
    await generate_video_for_scene(scene)

# Or with limited concurrency using a semaphore
semaphore = asyncio.Semaphore(2)
async def generate_with_limit(scene):
    async with semaphore:
        await generate_video_for_scene(scene)

await asyncio.gather(*[generate_with_limit(s) for s in scenes])
```

#### Don't re-generate what already exists

Combined with the resumable pipeline from the error handling section above, this ensures you never pay twice for the same clip. Always check the database before calling the API.

---

### User-Facing Error States

During Stage 2 testing you will have access to server logs. Real users won't. Before moving to Stage 2.5, every failure scenario needs to produce a message in the UI that tells the user what went wrong and what they can do about it.

#### What users need to see

| Failure | Bad UX | Good UX |
|---------|--------|---------|
| Pipeline times out | Spinner runs forever | "Generation is taking longer than expected. You can refresh to check progress." |
| One scene fails to generate | Silent — video has a gap | "2 of 8 scenes failed to generate. You can retry failed scenes or continue with the completed clips." |
| Kling API is down | 500 error page | "Video generation is temporarily unavailable. Your project has been saved — try again in a few minutes." |
| Script is too short to parse | Silent failure | "Your script needs at least one complete scene to generate a movie. Check that it follows standard screenplay format." |

#### Where to implement this

- **Backend:** Every phase endpoint should return structured error responses with a human-readable `message` field, not just HTTP 500. Catch exceptions at the service layer, not just at the agent layer.
- **Frontend:** The pipeline progress UI should read the `status` and `message` fields from the API and display them. Don't show raw error objects or stack traces to users.

---

### Stage 2 Completion Checklist

**API integration**
- [ ] `KLING_API_KEY` and `KLING_SECRET_KEY` are set in `.env`
- [ ] `MOCK_VIDEO = False` — real clips are being generated
- [ ] Every scene has a completed `generatedVideos` record (scene count = video count)

**Quality**
- [ ] Reviewed 3+ test projects — clips are visually accurate to the script
- [ ] Characters look consistent across scenes within the same project
- [ ] Final assembled MP4 plays without gaps, errors, or missing scenes
- [ ] Prompts have been iterated until output quality is satisfactory

**Resilience**
- [ ] Failed API calls retry automatically (at least 3 attempts per scene)
- [ ] A single failed scene does not crash the entire pipeline
- [ ] Failed scenes are recorded with `status = "failed"` and an error message in the database
- [ ] Re-triggering generation skips scenes that already completed — no duplicate charges

**Cost and rate limits**
- [ ] Generation is sequential or rate-limited — no parallel bursts that exceed Kling's limits
- [ ] Per-run cost is understood and acceptable for typical script lengths

**User experience**
- [ ] Every failure state shows a human-readable message in the frontend
- [ ] The pipeline progress UI reflects real status from the database — no eternal spinners
- [ ] Users can see which specific scenes failed, if any

Once every item is checked, move to Stage 2.5.

---

## Stage 2.5 — Staging Environment

**Goal:** Run the complete app in a cloud environment — not on your laptop — before any real users touch it. This catches configuration issues, permission problems, and environment differences that only show up outside of local development.

A staging environment is a copy of production with real infrastructure (S3, RDS, EC2) but used only for testing. It is not visible to real users.

#### Why this step exists

Things that work locally often break in cloud environments:
- File paths that work on your Mac fail on a Linux server
- Environment variables you set in `.env` are missing on EC2
- S3 bucket permissions are wrong and uploads silently fail
- The database connection string works locally but fails with RDS's SSL requirements
- ffmpeg is not installed on the server

Catching these in staging costs nothing. Catching them in production costs users.

#### What to do

1. **Follow the AWS Setup Guide** (`script_to_movie/AWS_SETUP_GUIDE.md`) to provision a staging environment. Use the same steps as production but with a separate set of AWS resources (a different S3 bucket, RDS instance, and EC2 instance, all named with a `-staging` suffix).

2. **Deploy the app to staging** exactly as you will deploy to production.

3. **Run the full pipeline on staging** with a short test script — register a user, create a project, run all three phases, and verify the final video is accessible.

4. **Test every failure scenario** from the Stage 2 checklist in the staging environment. Confirm the user-facing error messages appear correctly.

5. **Check costs and logs** — make sure S3 uploads are working, logs are being written, and there are no silent failures.

#### Staging completion checklist

- [ ] Staging environment provisioned on AWS (separate from production resources)
- [ ] App deployed and running on the staging EC2 instance
- [ ] Full pipeline runs end-to-end on staging — final video is accessible via S3 URL
- [ ] All environment variables confirmed correct on the server
- [ ] Error states tested — failures show correct messages in the UI
- [ ] No silent failures in logs

Once every item is checked, move to Stage 3.

---

## Stage 3 — Deploy to Production

**Goal:** Put the production app on the internet so it is accessible to real users.

When you're ready, follow the [AWS Setup Guide](./script_to_movie/AWS_SETUP_GUIDE.md). It covers:

- Creating an AWS account
- Setting up S3 for file storage (replaces the local `media/` folder)
- Setting up RDS for the MySQL database (same MySQL, hosted by AWS)
- Launching an EC2 server to run the app
- Configuring environment variables on the server
- Step-by-step commands for every task

The guide is written for beginners with no AWS experience. You can ask Claude Code to run every command in it.

#### Before deploying to production, confirm

- [ ] Stage 1 complete — full pipeline works locally with mock videos
- [ ] Stage 2 complete — real video generation works, quality validated, pipeline is resilient
- [ ] Stage 2.5 complete — full end-to-end test passed in staging environment
- [ ] All `.env` values are documented and ready to be set on the production server
- [ ] The app runs cleanly from a fresh clone (no undocumented setup steps)
- [ ] Staging and production use separate AWS resources — no shared state between them

Once every item is checked, move to Stage 4.

---

## Stage 4 — Integrate with Decode Shorts

**Goal:** Connect the Script-to-Movie pipeline to the existing Decode Shorts app so the two products work together as part of a unified experience.

This stage cannot be fully planned until both products are stable and deployed. The specifics will depend on how Decode Shorts is built and where the natural integration points are. The tasks below are a starting framework — update this section with the actual integration plan once both apps are running.

#### What to figure out first

Before writing any integration code, get answers to these questions:

1. **Where do users enter the flow?** Does Script-to-Movie appear as a feature inside Decode Shorts, or does Decode Shorts surface content created by Script-to-Movie?
2. **How do the two apps share users?** Are user accounts shared (single sign-on / shared database), or are they separate? Shared accounts are the right long-term answer, but require a migration plan if accounts currently live in separate databases.
3. **How does content move between the apps?** Does Script-to-Movie produce a final video that gets imported into Decode Shorts? Or does Decode Shorts trigger the Script-to-Movie pipeline directly via API?
4. **Where does each app run?** Are they on the same server, or separate servers that need to talk to each other over HTTP?

#### Likely integration points

Based on what Script-to-Movie produces, the most likely integration pattern is:

```
Decode Shorts
    ↓ (user initiates "create from script" feature)
Script-to-Movie API
    ↓ (runs pipeline, produces final MP4)
Decode Shorts
    ↓ (imports the MP4 as a new piece of content)
User sees finished video inside Decode Shorts
```

This would require:
- A Decode Shorts → Script-to-Movie API call to start a pipeline run
- A way for Script-to-Movie to notify Decode Shorts when the video is ready (webhook or polling)
- A shared S3 bucket or a file handoff mechanism so Decode Shorts can access the final video

#### Integration checklist (to be completed once both apps are stable)

- [ ] Answered the four questions above — integration approach is defined
- [ ] User account strategy decided (shared accounts vs. separate)
- [ ] API contract between the two apps documented — what calls what, with what parameters
- [ ] Script-to-Movie pipeline can be triggered from Decode Shorts without requiring a user to visit the Script-to-Movie UI
- [ ] Final video produced by Script-to-Movie is accessible to Decode Shorts (shared S3, API endpoint, or direct URL)
- [ ] Error states are surfaced correctly in Decode Shorts if the pipeline fails
- [ ] End-to-end test: user initiates flow in Decode Shorts, pipeline runs, video appears in Decode Shorts without manual steps
- [ ] Both apps deployed and integration tested in staging before going live

---

---

## Reference

### Using Claude Code

Claude Code is your development partner. Here's how to use it effectively for this project.

#### Setting up

```
"Set up the Script-to-Movie backend for local development"
"Create my .env file with the database URL for local MySQL"
"Run the database migrations"
"Start the backend server"
```

#### Understanding the codebase

```
"Explain how the Scene model works"
"Show me how the LLM client is used in existing agents"
"What does the video_assembly.py file do?"
"How does Phase 1 pass data to Phase 2?"
```

#### Writing code

```
"Implement the script_analysis agent for Phase 1"
"Write the mock video logic for Phase 3 with a MOCK_VIDEO flag"
"Add error handling to the video generation agent"
```

#### Debugging

```
"The backend won't start — read the error and help me fix it"
"My agent returns an empty list of scenes — help me debug the database query"
"The alembic migration failed — what went wrong?"
```

#### Prompt engineering

```
"Review my Phase 1 scene description prompt and suggest improvements for visual specificity"
"The generated clips don't match the script — help me improve the Phase 3 video prompt"
"Show me how character descriptions are being passed into the video prompts"
```

#### Testing

```
"Test the /api/phases/script-to-trailer/1/parse endpoint with curl"
"Check what data is in the scenes table for project 1"
"Compare the number of scenes vs generated videos for project 1"
```

#### Tips

- **Be specific.** "Fix the bug" is vague. "The video_assembly function fails when a scene has no dialogue — fix the None check on line 120" is clear.
- **Point to files.** "Look at agents/video_assembly.py and fix the download timeout" saves time.
- **Ask it to explain.** If you don't understand code someone else wrote, ask Claude Code to explain it before modifying it.
- **Let it read first.** Claude Code should read a file before editing it. If it suggests changes without reading, ask it to read the file first.

---

### Common Tasks

#### Start the development servers

```bash
# Terminal 1: Backend
cd script_to_movie/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd script_to_movie
pnpm dev
```

#### Create a test user

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "password123", "name": "Test User"}'
```

#### Log in and save the session cookie

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "password123"}' \
  -c cookies.txt

# Now use -b cookies.txt with all other requests
```

#### Create a project with a test script

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "title": "My Test Movie",
    "scriptContent": "FADE IN:\n\nINT. COFFEE SHOP - MORNING\n\nALICE sits alone at a table.\n\nALICE\nI have been waiting for hours.\n\nBOB enters, out of breath.\n\nBOB\nSorry I am late. Traffic was terrible.\n\nFADE OUT."
  }'
```

#### Check what's in the database

```bash
# Connect to MySQL
mysql -u root script_to_movie

# Useful queries
SELECT id, title, status, progress FROM projects;
SELECT id, projectId, sceneNumber, title FROM scenes ORDER BY projectId, `order`;
SELECT id, sceneId, status FROM generatedVideos;
SELECT id, projectId, status, movieUrl FROM finalMovies;
```

#### Check scene vs video coverage (Stage 2 QA)

```bash
mysql -u root script_to_movie -e "
  SELECT
    p.id,
    p.title,
    (SELECT COUNT(*) FROM scenes WHERE projectId = p.id) AS scenes,
    (SELECT COUNT(*) FROM generatedVideos WHERE projectId = p.id AND status = 'completed') AS videos
  FROM projects p;
"
```

#### Reset a project (start over)

```bash
mysql -u root script_to_movie -e "
  DELETE FROM finalMovies WHERE projectId = 1;
  DELETE FROM generatedVideos WHERE projectId = 1;
  DELETE FROM videoPrompts WHERE projectId = 1;
  DELETE FROM storyboardImages WHERE projectId = 1;
  DELETE FROM scenes WHERE projectId = 1;
  UPDATE projects SET status = 'draft', progress = 0 WHERE id = 1;
"
```

#### View API documentation

Open http://localhost:8000/docs. This interactive page lets you see every endpoint, try requests from the browser, and view request/response schemas.

---

### Database Guide

#### How to read a model file

```python
class Scene(Base):
    __tablename__ = "scenes"                    # ← The actual MySQL table name

    id: Mapped[int] = mapped_column(primary_key=True)
    projectId: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    sceneNumber: Mapped[int]                    # ← 1, 2, 3...
    title: Mapped[str]                          # ← "Opening Scene"
    description: Mapped[str]                    # ← Visual description
    dialogue: Mapped[str | None]                # ← Character lines (can be empty)
    duration: Mapped[int | None]                # ← Seconds
    order: Mapped[int]                          # ← Sort order for assembly

    project: Mapped["Project"] = relationship(back_populates="scenes")
    generated_videos: Mapped[List["GeneratedVideo"]] = relationship(...)
```

#### Common database operations

```python
from sqlalchemy import select
from app.models.scene import Scene

# Get all scenes for a project, in order
result = await db.execute(
    select(Scene).where(Scene.projectId == project_id).order_by(Scene.order)
)
scenes = list(result.scalars().all())

# Get a single project
result = await db.execute(select(Project).where(Project.id == project_id))
project = result.scalar_one_or_none()

# Create a new record
scene = Scene(projectId=1, sceneNumber=1, title="Opening", description="...", order=0)
db.add(scene)
await db.commit()

# Update a record
project.status = "completed"
project.progress = 100
await db.commit()
```

#### All 9 tables

| Table | Model File | Key Columns | Created By |
|-------|-----------|-------------|------------|
| `users` | `user.py` | email, name, passwordHash | Auth system |
| `projects` | `project.py` | title, scriptContent, status, progress | User via API |
| `scenes` | `scene.py` | projectId, title, description, dialogue, order | Phase 1 |
| `characters` | `character.py` | projectId, name, visualDescription | Phase 1 |
| `settings` | `setting.py` | projectId, name, visualDescription | Phase 1 |
| `storyboardImages` | `storyboard.py` | sceneId, imageUrl, status | Phase 1/2 |
| `videoPrompts` | `video.py` | sceneId, prompt, duration, style | Phase 3 |
| `generatedVideos` | `video.py` | sceneId, videoUrl, duration, status | Phase 3 |
| `finalMovies` | `final_movie.py` | projectId, movieUrl, duration, status | Phase 3 |

---

### API Reference

#### Authentication

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create a new user account |
| POST | `/api/auth/login` | Log in, receive session cookie |
| POST | `/api/auth/logout` | Log out, clear session |
| GET | `/api/auth/me` | Get current user info |

#### Projects

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/projects` | Create a new project |
| GET | `/api/projects` | List all your projects |
| GET | `/api/projects/{id}` | Get a specific project |
| GET | `/api/projects/{id}/scenes` | Get scenes for a project |
| GET | `/api/projects/{id}/characters` | Get characters |
| GET | `/api/projects/{id}/settings` | Get settings |
| GET | `/api/projects/{id}/storyboards` | Get storyboard images |
| GET | `/api/projects/{id}/movie` | Get the final movie |

#### Phase 1: Script to Trailer

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/phases/script-to-trailer/{id}/parse` | Parse script into scenes |
| POST | `/api/phases/script-to-trailer/{id}/generate-trailer` | Generate trailer video |
| GET | `/api/phases/script-to-trailer/{id}/status` | Check Phase 1 progress |

#### Phase 2: Trailer to Storyboard

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/phases/trailer-to-storyboard/{id}/generate` | Generate storyboard |
| GET | `/api/phases/trailer-to-storyboard/{id}/status` | Check Phase 2 progress |

#### Phase 3: Storyboard to Movie

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/phases/storyboard-to-movie/{id}/prompts` | Generate video prompts |
| POST | `/api/phases/storyboard-to-movie/{id}/generate` | Generate video clips |
| POST | `/api/phases/storyboard-to-movie/{id}/assemble` | Assemble final movie |
| GET | `/api/phases/storyboard-to-movie/{id}/status` | Check Phase 3 progress |

#### Full Pipeline

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/workflow/{id}/start` | Run all 3 phases automatically |
| GET | `/api/workflow/{id}/status` | Check overall pipeline progress |

All endpoints (except auth) require authentication. Pass `-b cookies.txt` with curl or include the session cookie in your requests.

---

### Troubleshooting

#### Backend won't start

**"ModuleNotFoundError: No module named 'app'"**
- Make sure you're in the `script_to_movie/backend/` directory
- Make sure your virtual environment is activated: `source .venv/bin/activate`
- Reinstall: `pip install -e ".[dev]"`

**"Can't connect to MySQL server"**
- Check MySQL is running: `brew services list` (look for `mysql`)
- Start it: `brew services start mysql`
- Verify connection: `mysql -u root -e "SELECT 1"`

**"Target database is not up to date"**
- Run migrations: `alembic upgrade head`

#### Frontend won't start

**"pnpm: command not found"**
- Install it: `npm install -g pnpm`

**"Cannot find module"**
- Install dependencies: `pnpm install`

#### API returns 401 Unauthorized

- You need to log in first and include the session cookie
- Register: `curl -X POST .../api/auth/register -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"password123","name":"Test"}'`
- Log in: `curl -X POST .../api/auth/login -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"password123"}' -c cookies.txt`
- Use `-b cookies.txt` with all other requests

#### Alembic migration fails

**"Can't locate revision"**
- Your migration history may be out of sync. Ask Claude Code:
  "The alembic migration failed with this error: (paste error). Help me fix it."

#### Agent returns "No scenes found"

- The previous phase hasn't run yet. Phases must run in order: 1 → 2 → 3
- Check what data exists: `mysql -u root script_to_movie -e "SELECT COUNT(*) FROM scenes WHERE projectId = 1;"`

#### ffmpeg errors

**"ffmpeg: command not found"**
- Install it: `brew install ffmpeg`

**"ffmpeg error: ..."**
- The error message from ffmpeg is usually descriptive. Ask Claude Code to help interpret it.

#### Kling API errors (Stage 2)

**"401 Unauthorized"**
- Double-check `KLING_API_KEY` and `KLING_SECRET_KEY` in your `.env`

**"Videos are generating but clips look wrong"**
- This is a prompt quality issue. See [Prompt Engineering Guide](#prompt-engineering-guide)

**"Some scenes are missing videos"**
- Check scene coverage with the SQL query in Common Tasks
- Review the generation loop in your Phase 3 agent for any early exits or error swallowing

#### S3 upload fails (Stage 3)

- If you haven't configured AWS credentials, this is expected during Stages 1 and 2. The app falls back to saving files in a local `media/` directory.
- To set up S3, follow the [AWS Setup Guide](./script_to_movie/AWS_SETUP_GUIDE.md)
