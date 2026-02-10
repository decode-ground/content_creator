# Script-to-Movie

An AI-powered platform that transforms screenplays into full-length generated movies. Upload a script, and the system analyzes it, creates consistent visual representations, generates video for each scene with dialogue audio, and assembles everything into a complete movie.

---

## Table of Contents

| Section | Description |
|---------|-------------|
| [How It Works](#how-it-works) | The 3-phase pipeline from script to movie |
| [Project Structure](#project-structure) | Where everything lives in the codebase |
| [Getting Started](#getting-started) | How to set up and run the project locally |
| [For Phase Developers](#for-phase-developers) | Guide for the 3 developers working on phases |
| [API Reference](#api-reference) | All available API endpoints |
| [Database Schema](#database-schema) | What data is stored and how |
| [Tech Stack](#tech-stack) | Technologies used |

---

## How It Works

A user provides a movie title and script/plot. The system processes it through 3 phases:

```
User Input: Movie title + script/plot
         |
         v
+----------------------------------------------------------+
|  PHASE 1: Script to Trailer                              |
|                                                          |
|  1. Parse script into a full screenplay with scenes      |
|     (including all dialogue for each scene)              |
|  2. Generate detailed visual descriptions for every      |
|     character (hair, clothing, features, etc.)           |
|  3. Generate detailed visual descriptions for every      |
|     setting/location                                     |
|  4. Generate a trailer video using a text-to-video API   |
|  5. Extract one key frame from the trailer per scene     |
|                                                          |
|  Output: Scene records, Character records, Setting       |
|          records, Trailer video, Storyboard frames       |
+----------------------------------------------------------+
         |
         v
+----------------------------------------------------------+
|  PHASE 2: Trailer to Storyboard                         |
|                                                          |
|  1. Validate that every scene has a corresponding        |
|     trailer frame                                        |
|  2. Evaluate if each frame depicts its scene well        |
|  3. Regenerate poor/missing frames using an image        |
|     generation API with character + setting descriptions |
|                                                          |
|  Output: Validated storyboard (1 quality frame per scene)|
+----------------------------------------------------------+
         |
         v
+----------------------------------------------------------+
|  PHASE 3: Storyboard to Movie                           |
|                                                          |
|  1. Create optimized video generation prompts per scene  |
|  2. Generate a video clip per scene using image-to-video |
|     (storyboard image = visual reference, scene          |
|     description = text prompt)                           |
|  3. Generate TTS (text-to-speech) audio from each        |
|     scene's dialogue                                     |
|  4. Combine video + audio for each scene                 |
|  5. Assemble all scene clips into the final full movie   |
|                                                          |
|  Output: Final movie (MP4, H.264, 1080p, 24fps)         |
+----------------------------------------------------------+
```

### Important Design Principles

- **Phases communicate only through the database.** Phase 2 reads what Phase 1 wrote. Phase 3 reads what Phase 2 wrote. No code imports between phases.
- **Every scene must have dialogue** (if there are spoken parts). Phase 3 uses `Scene.dialogue` to generate TTS audio.
- **Every scene must have exactly one storyboard frame.** Phase 3 uses these as visual references for video generation.
- **Character visual descriptions must be detailed and consistent** across all phases. The same character should look the same in every generated image and video.

---

## Project Structure

```
script_to_movie/
|
+-- backend/                          <-- Python FastAPI backend
|   |-- CLAUDE.md                     <-- START HERE (backend developer guide)
|   |-- .env.example                  <-- Environment variable template
|   |-- pyproject.toml                <-- Python dependencies
|   |-- alembic.ini                   <-- Database migration config
|   |-- alembic/                      <-- Database migration files
|   |
|   +-- app/
|       |-- main.py                   <-- FastAPI entry point
|       |-- config.py                 <-- Environment settings
|       |
|       |-- core/                     <-- Shared infrastructure (DO NOT MODIFY)
|       |   |-- database.py           <-- Database connection + sessions
|       |   |-- security.py           <-- JWT tokens + password hashing
|       |   |-- dependencies.py       <-- Auth middleware (get_current_user)
|       |   |-- llm.py                <-- Claude AI client
|       |   +-- storage.py            <-- S3 file storage client
|       |
|       |-- models/                   <-- Database table definitions (DO NOT MODIFY)
|       |-- schemas/                  <-- API request/response types (DO NOT MODIFY)
|       |-- auth/                     <-- Login/register endpoints (DONE)
|       |-- projects/                 <-- Project CRUD endpoints (DONE)
|       |-- system/                   <-- Health check endpoint (DONE)
|       |
|       |-- phases/                   <-- THE 3 PIPELINE PHASES
|       |   |-- base_agent.py         <-- Base class all agents inherit from
|       |   |-- script_to_trailer/    <-- Phase 1 (Developer 1)
|       |   |-- trailer_to_storyboard/<-- Phase 2 (Developer 2)
|       |   +-- storyboard_to_movie/  <-- Phase 3 (Developer 3)
|       |
|       +-- workflow/                 <-- Pipeline orchestration (runs all 3 phases)
|
+-- client/                           <-- React frontend
|   +-- src/
|       |-- lib/api.ts                <-- REST API client
|       |-- pages/                    <-- Page components
|       +-- components/               <-- UI components
|
+-- drizzle/                          <-- Legacy schema (reference only, do not use)
```

### Key Documentation Files

| File | What It Covers |
|------|---------------|
| [`backend/CLAUDE.md`](script_to_movie/backend/CLAUDE.md) | Backend developer guide: setup, architecture, code examples |
| [`backend/app/phases/script_to_trailer/README.md`](script_to_movie/backend/app/phases/script_to_trailer/README.md) | Phase 1 developer guide |
| [`backend/app/phases/script_to_trailer/PLAN.md`](script_to_movie/backend/app/phases/script_to_trailer/PLAN.md) | Phase 1 task checklist |
| [`backend/app/phases/trailer_to_storyboard/README.md`](script_to_movie/backend/app/phases/trailer_to_storyboard/README.md) | Phase 2 developer guide |
| [`backend/app/phases/trailer_to_storyboard/PLAN.md`](script_to_movie/backend/app/phases/trailer_to_storyboard/PLAN.md) | Phase 2 task checklist |
| [`backend/app/phases/storyboard_to_movie/README.md`](script_to_movie/backend/app/phases/storyboard_to_movie/README.md) | Phase 3 developer guide |
| [`backend/app/phases/storyboard_to_movie/PLAN.md`](script_to_movie/backend/app/phases/storyboard_to_movie/PLAN.md) | Phase 3 task checklist |
| [`backend/app/core/README.md`](script_to_movie/backend/app/core/README.md) | Core infrastructure reference |

---

## Getting Started

### Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- MySQL 8.0 or newer
- pnpm (for the frontend)

### 1. Start the Database

```bash
# Option A: Using Docker (recommended)
docker run -d --name mysql \
  -e MYSQL_ROOT_PASSWORD=password \
  -e MYSQL_DATABASE=script_to_movie \
  -p 3306:3306 mysql:8

# Option B: Using existing MySQL
mysql -u root -p -e "CREATE DATABASE script_to_movie;"
```

### 2. Set Up the Backend

```bash
cd script_to_movie/backend

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Create your .env file
cp .env.example .env
# Edit .env with your API keys (at minimum: DATABASE_URL, JWT_SECRET, ANTHROPIC_API_KEY)

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

### 3. Start the Frontend

```bash
cd script_to_movie

# Install dependencies
pnpm install

# Start dev server (proxies API requests to the backend)
pnpm dev
```

### 4. Verify Everything Works

- Frontend: http://localhost:5173
- API docs (interactive): http://localhost:8000/docs
- Health check: http://localhost:8000/api/system/health

---

## For Phase Developers

Each phase is assigned to one developer. You only modify files in your phase directory.

### Your Workflow

1. **Read your phase's README.md** in `backend/app/phases/<your-phase>/README.md` -- this is your complete developer guide
2. **Read your phase's PLAN.md** in `backend/app/phases/<your-phase>/PLAN.md` -- this is your task checklist
3. **Read `backend/CLAUDE.md`** -- this explains the shared infrastructure you'll use
4. **Switch to your feature branch**:
   - Phase 1: `git checkout phase-1/script-to-trailer`
   - Phase 2: `git checkout phase-2/trailer-to-storyboard`
   - Phase 3: `git checkout phase-3/storyboard-to-movie`
5. **Implement your agents** following the order in your README
6. **Test with curl commands** listed in your README

### What You CAN Modify

Only files inside your phase directory:
- `backend/app/phases/script_to_trailer/` (Phase 1 developer)
- `backend/app/phases/trailer_to_storyboard/` (Phase 2 developer)
- `backend/app/phases/storyboard_to_movie/` (Phase 3 developer)

### What You CANNOT Modify

Everything else is shared infrastructure:
- `app/core/` -- database, auth, LLM client, storage
- `app/models/` -- database table definitions
- `app/schemas/` -- API types
- `app/auth/` -- authentication endpoints
- `app/projects/` -- project endpoints
- `app/phases/base_agent.py` -- base class for agents

---

## API Reference

### Authentication (implemented)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/me` | Get current logged-in user |
| POST | `/api/auth/register` | Create a new account |
| POST | `/api/auth/login` | Log in with email/password |
| POST | `/api/auth/logout` | Log out (clears session cookie) |

### Projects (implemented)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects` | Create a new project with a script |
| GET | `/api/projects` | List your projects |
| GET | `/api/projects/{id}` | Get a specific project |
| GET | `/api/projects/{id}/scenes` | Get all scenes for a project |
| GET | `/api/projects/{id}/characters` | Get all characters |
| GET | `/api/projects/{id}/settings` | Get all settings/locations |
| GET | `/api/projects/{id}/storyboards` | Get storyboard frames |
| GET | `/api/projects/{id}/movie` | Get the final movie |

### Phase 1: Script to Trailer (to be implemented)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/phases/script-to-trailer/{id}/analyze` | Parse script into scenes |
| POST | `/api/phases/script-to-trailer/{id}/characters` | Generate character descriptions |
| POST | `/api/phases/script-to-trailer/{id}/settings` | Generate setting descriptions |
| POST | `/api/phases/script-to-trailer/{id}/trailer` | Generate trailer + extract frames |

### Phase 2: Trailer to Storyboard (to be implemented)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/phases/trailer-to-storyboard/{id}/generate` | Validate/regenerate storyboard |
| GET | `/api/phases/trailer-to-storyboard/{id}/status` | Check generation status |

### Phase 3: Storyboard to Movie (to be implemented)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/phases/storyboard-to-movie/{id}/prompts` | Generate video prompts |
| POST | `/api/phases/storyboard-to-movie/{id}/generate` | Generate video clips |
| POST | `/api/phases/storyboard-to-movie/{id}/assemble` | Assemble final movie |
| GET | `/api/phases/storyboard-to-movie/{id}/status` | Check generation status |

### Workflow (to be implemented)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workflow/{id}/start` | Run all 3 phases automatically |
| GET | `/api/workflow/{id}/status` | Check pipeline progress |
| POST | `/api/workflow/{id}/pause` | Pause the pipeline |
| POST | `/api/workflow/{id}/resume` | Resume the pipeline |

### System (implemented)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/system/health` | Health check |

---

## Database Schema

```
users
  |-- id, email, name, passwordHash, role, openId
  |
  +-- projects (one user has many projects)
        |-- id, userId, title, description, scriptContent
        |-- status, progress, trailerUrl, trailerKey
        |
        +-- scenes (one project has many scenes)
        |     |-- id, projectId, sceneNumber, title
        |     |-- description, dialogue, setting
        |     |-- characters (JSON), duration, order
        |     |
        |     +-- storyboardImages (one scene has one frame)
        |     |     |-- id, sceneId, projectId, imageUrl, imageKey, prompt, status
        |     |
        |     +-- videoPrompts (one scene has one video prompt)
        |     |     |-- id, sceneId, projectId, prompt, duration, style
        |     |
        |     +-- generatedVideos (one scene has one video clip)
        |           |-- id, sceneId, projectId, videoUrl, videoKey, duration, status
        |
        +-- characters (one project has many characters)
        |     |-- id, projectId, name, description, visualDescription
        |
        +-- settings (one project has many settings/locations)
        |     |-- id, projectId, name, description, visualDescription
        |
        +-- finalMovies (one project has one final movie)
              |-- id, projectId, movieUrl, movieKey, duration, status
```

### How Data Flows Between Phases

```
Phase 1 WRITES:                      Phase 2 READS:
  Scene records (with dialogue)  -->   Scene records
  Character records              -->   Character records (visualDescription)
  Setting records                -->   Setting records (visualDescription)
  StoryboardImage records        -->   StoryboardImage records
  Project.trailerUrl

Phase 2 WRITES:                      Phase 3 READS:
  Updated StoryboardImage        -->   StoryboardImage records (imageUrl)
  records (validated/regenerated)      Scene records (description, dialogue)

Phase 3 WRITES:
  VideoPrompt records
  GeneratedVideo records
  FinalMovie record
  Project.status = "completed"
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3.11+, FastAPI | REST API server |
| Database | MySQL + SQLAlchemy 2.0 (async) | Data storage |
| Migrations | Alembic | Database schema changes |
| AI/LLM | Claude API (Anthropic Python SDK) | Script analysis, prompt generation |
| Auth | JWT (python-jose) + bcrypt (passlib) | User authentication |
| Storage | AWS S3 | Images, videos, final movies |
| Frontend | React 19, TypeScript, Tailwind CSS 4 | User interface |
| API Client | React Query | Frontend data fetching |
