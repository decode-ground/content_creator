# Script-to-Movie

An AI-powered platform that transforms screenplays into full-length generated movies. A user pastes a script, and the system parses it into scenes, generates a storyboard, creates a video clip for every scene with dialogue audio, and assembles everything into a final MP4.

---

## Start Here

**If you are a developer joining this project, your first read is the Developer Guide.**

> [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md)

It covers the full product development cycle from local setup through AWS deployment and Decode Shorts integration, written for developers using Claude Code as their primary tool.

---

## Development Stages

This project is built in stages. Do not move to the next stage until the current one is fully working.

| Stage | Goal | Definition of Done |
|-------|------|--------------------|
| **Stage 1** | Build locally with mock videos | All 3 phases run end-to-end; no real video API calls needed |
| **Stage 2** | Integrate Kling AI and validate quality | Real clips generated; script accuracy, character consistency, and scene coverage all pass; pipeline is resilient and cost-aware |
| **Stage 2.5** | Staging environment | Full end-to-end test on AWS before real users touch it |
| **Stage 3** | Deploy to production | App is live on AWS and accessible to users |
| **Stage 4** | Integrate with Decode Shorts | Script-to-Movie features work as part of the Decode Shorts product |

---

## How the Pipeline Works

A user provides a screenplay. The system runs it through 3 phases:

```
Screenplay text
         |
         v
+----------------------------------------------------------+
|  PHASE 1: Script to Trailer                              |
|                                                          |
|  1. Parse script into scenes (with dialogue)             |
|  2. Generate detailed visual descriptions for every      |
|     character (hair, clothing, features, etc.)           |
|  3. Generate detailed visual descriptions for every      |
|     setting/location                                     |
|  4. Generate a trailer video using Kling AI              |
|  5. Extract one key frame from the trailer per scene     |
|                                                          |
|  Output: Scene, Character, Setting records               |
|          Trailer video, Storyboard frames                |
+----------------------------------------------------------+
         |
         v
+----------------------------------------------------------+
|  PHASE 2: Trailer to Storyboard                          |
|                                                          |
|  1. Validate that every scene has a trailer frame        |
|  2. Evaluate if each frame depicts its scene accurately  |
|  3. Regenerate poor or missing frames using image        |
|     generation with character + setting descriptions     |
|                                                          |
|  Output: Validated storyboard (1 quality frame/scene)    |
+----------------------------------------------------------+
         |
         v
+----------------------------------------------------------+
|  PHASE 3: Storyboard to Movie                            |
|                                                          |
|  1. Generate optimized video prompts per scene           |
|  2. Generate a video clip per scene (storyboard image    |
|     as visual reference, scene description as prompt)    |
|  3. Generate TTS audio from each scene's dialogue        |
|  4. Combine video + audio for each scene                 |
|  5. Assemble all clips into the final movie              |
|                                                          |
|  Output: Final movie (MP4, H.264, 1080p, 24fps)         |
+----------------------------------------------------------+
```

### Key design principles

- **Phases communicate only through the database.** Phase 2 reads what Phase 1 wrote. Phase 3 reads what Phase 2 wrote. No code is imported between phases.
- **Every scene must have a storyboard frame.** Phase 3 uses these as visual references for video generation.
- **Character visual descriptions must be detailed and consistent.** The same character should look the same across every scene.
- **During Stage 1, use mock videos.** The Kling AI integration is only switched on in Stage 2. See the Developer Guide for the `MOCK_VIDEO` flag pattern.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3.11+, FastAPI | REST API server |
| Database | MySQL + SQLAlchemy 2.0 (async) | Data storage |
| Migrations | Alembic | Database schema management |
| AI / LLM | Claude API (Anthropic) | Script parsing, prompt generation |
| Video generation | Kling AI | Image-to-video clips (Stage 2+) |
| Audio | gTTS | Text-to-speech dialogue audio |
| Video assembly | ffmpeg | Merges clips, adds audio, assembles movie |
| Auth | JWT + bcrypt | User authentication |
| Storage | AWS S3 | Images, videos, final movies (Stage 3+) |
| Frontend | React 19, TypeScript, Tailwind CSS 4 | User interface |
| API client | React Query | Frontend data fetching |

---

## Project Structure

```
content_creator/
├── script_to_movie/
│   ├── DEVELOPER_GUIDE.md              ← Full development lifecycle guide (start here)
│   ├── AWS_SETUP_GUIDE.md              ← AWS deployment (Stage 3)
│   ├── AGENT_ARCHITECTURE.md           ← How the agent system works
│   ├── AGENT_INTEGRATION_GUIDE.md      ← How frontend talks to backend
│   │
│   ├── backend/                        ← Python FastAPI backend
│   │   ├── CLAUDE.md                   ← Backend developer reference
│   │   ├── .env.example                ← Environment variable template
│   │   └── app/
│   │       ├── core/                   ← Shared infrastructure (do not modify)
│   │       ├── models/                 ← Database table definitions (do not modify)
│   │       ├── schemas/                ← API types (do not modify)
│   │       ├── auth/                   ← Auth endpoints (complete)
│   │       ├── projects/               ← Project CRUD endpoints (complete)
│   │       └── phases/                 ← The 3 pipeline phases (this is where you work)
│   │           ├── script_to_trailer/      ← Phase 1
│   │           ├── trailer_to_storyboard/  ← Phase 2
│   │           └── storyboard_to_movie/    ← Phase 3
│   │
│   ├── client/                         ← React frontend
│   └── server/                         ← Node.js tRPC server
```

### Key documentation

| File | What it covers |
|------|---------------|
| [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) | Full development lifecycle — setup, stages, quality criteria, deployment, Decode Shorts integration |
| [`script_to_movie/backend/CLAUDE.md`](script_to_movie/backend/CLAUDE.md) | Backend developer reference: architecture, code examples, shared modules |
| [`script_to_movie/AWS_SETUP_GUIDE.md`](script_to_movie/AWS_SETUP_GUIDE.md) | AWS setup for Stage 3 deployment |
| `backend/app/phases/*/README.md` | Per-phase developer guide (what inputs you receive, what outputs you produce) |
| `backend/app/phases/*/PLAN.md` | Per-phase task checklist |

---

## Quick Setup (Local)

Full setup instructions with explanations are in the Developer Guide. For experienced developers, the short version:

```bash
# 1. Database
mysql -u root -e "CREATE DATABASE script_to_movie;"

# 2. Backend
cd script_to_movie/backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # fill in DATABASE_URL, JWT_SECRET, ANTHROPIC_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd script_to_movie
pnpm install && pnpm dev
```

- Frontend: http://localhost:5173
- API + interactive docs: http://localhost:8000/docs

**Minimum `.env` for Stage 1:** `DATABASE_URL`, `JWT_SECRET`, `ANTHROPIC_API_KEY`
**Add for Stage 2:** `KLING_API_KEY`, `KLING_SECRET_KEY`
**Add for Stage 3:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`

---

## Database Schema

```
users
  └── projects
        ├── scenes
        │     ├── storyboardImages   (1 per scene — Phase 1/2 writes, Phase 3 reads)
        │     ├── videoPrompts       (1 per scene — Phase 3 writes)
        │     └── generatedVideos    (1 per scene — Phase 3 writes)
        ├── characters               (Phase 1 writes — visual descriptions used by all phases)
        ├── settings                 (Phase 1 writes — visual descriptions used by all phases)
        └── finalMovies              (Phase 3 writes — the assembled output)
```

### Data flow between phases

```
Phase 1 WRITES                    Phase 2 READS
  Scene records               →     Scene records
  Character records           →     Character records (visualDescription)
  Setting records             →     Setting records (visualDescription)
  StoryboardImage records     →     StoryboardImage records

Phase 2 WRITES                    Phase 3 READS
  Updated StoryboardImages    →     StoryboardImage records (imageUrl)
                                    Scene records (description, dialogue)

Phase 3 WRITES
  VideoPrompt records
  GeneratedVideo records
  FinalMovie record
```

---

## API Reference

Full docs are available at http://localhost:8000/docs when the backend is running.

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Log in |
| POST | `/api/auth/logout` | Log out |
| GET | `/api/auth/me` | Get current user |

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects` | Create a new project |
| GET | `/api/projects` | List your projects |
| GET | `/api/projects/{id}` | Get a project |
| GET | `/api/projects/{id}/scenes` | Get scenes |
| GET | `/api/projects/{id}/characters` | Get characters |
| GET | `/api/projects/{id}/settings` | Get settings |
| GET | `/api/projects/{id}/storyboards` | Get storyboard frames |
| GET | `/api/projects/{id}/movie` | Get final movie |

### Phase 1 — Script to Trailer

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/phases/script-to-trailer/{id}/parse` | Parse script into scenes |
| POST | `/api/phases/script-to-trailer/{id}/generate-trailer` | Generate trailer + frames |
| GET | `/api/phases/script-to-trailer/{id}/status` | Check progress |

### Phase 2 — Trailer to Storyboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/phases/trailer-to-storyboard/{id}/generate` | Validate/regenerate storyboard |
| GET | `/api/phases/trailer-to-storyboard/{id}/status` | Check progress |

### Phase 3 — Storyboard to Movie

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/phases/storyboard-to-movie/{id}/prompts` | Generate video prompts |
| POST | `/api/phases/storyboard-to-movie/{id}/generate` | Generate video clips |
| POST | `/api/phases/storyboard-to-movie/{id}/assemble` | Assemble final movie |
| GET | `/api/phases/storyboard-to-movie/{id}/status` | Check progress |

### Full Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workflow/{id}/start` | Run all 3 phases |
| GET | `/api/workflow/{id}/status` | Check overall progress |
