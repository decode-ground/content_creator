# Script-to-Movie: Project Overview

## What is Script-to-Movie?

Script-to-Movie is an AI-powered platform that transforms screenplays into generated trailer videos. Upload a script, and the system will analyze it, create consistent visual representations of characters and settings, select key moments for a trailer, generate storyboard frames and videos, and assemble them into a final trailer.

**Core Value**: Rapid visualization of screenplay concepts without manual production work.

---

## The Pipeline

The system processes scripts through three main phase groups:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: Script → Trailer                    │
├─────────────────────────────────────────────────────────────────┤
│  Script Upload → Script Analysis → Character/Setting Consistency│
│                 → Trailer Scene Selection                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 2: Trailer → Storyboard                   │
├─────────────────────────────────────────────────────────────────┤
│  Storyboard Prompts → Image Generation                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 3: Storyboard → Movie                     │
├─────────────────────────────────────────────────────────────────┤
│  Video Prompts → Video Generation → Final Assembly              │
└─────────────────────────────────────────────────────────────────┘
```

### Phase Group Responsibilities

| Phase Group | Input | Output | Agents |
|-------------|-------|--------|--------|
| **script_to_trailer** | Raw screenplay | Selected trailer scenes + consistent character/setting descriptions | ScriptAnalysis, CharacterConsistency, SettingConsistency, TrailerSelection |
| **trailer_to_storyboard** | Trailer scenes + descriptions | Storyboard images with prompts | StoryboardPrompt + image generation |
| **storyboard_to_movie** | Storyboard frames | Final trailer video | VideoPrompt, VideoGeneration, VideoAssembly |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Claude API (Anthropic Python SDK) |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async) |
| **Database** | MySQL with Alembic migrations |
| **Frontend** | React 19, Tailwind CSS 4, React Query |
| **File Storage** | S3 (images and videos) |
| **Auth** | JWT (python-jose) + bcrypt (passlib) |

---

## Project Structure

```
script_to_movie/
├── backend/                              # Python FastAPI backend
│   ├── pyproject.toml                    # Dependencies
│   ├── alembic.ini                       # Migration config
│   ├── alembic/                          # DB migrations
│   │
│   └── app/
│       ├── main.py                       # FastAPI entry point
│       ├── config.py                     # Environment settings
│       │
│       ├── core/                         # Shared infrastructure
│       │   ├── database.py               # SQLAlchemy async engine
│       │   ├── security.py               # JWT, bcrypt
│       │   ├── dependencies.py           # get_db, get_current_user
│       │   ├── llm.py                    # Anthropic client
│       │   └── storage.py                # S3 client
│       │
│       ├── models/                       # SQLAlchemy models
│       │   ├── user.py
│       │   ├── project.py
│       │   ├── scene.py
│       │   ├── character.py
│       │   ├── setting.py
│       │   ├── storyboard.py
│       │   ├── video.py
│       │   └── final_movie.py
│       │
│       ├── schemas/                      # Pydantic request/response
│       │
│       ├── auth/                         # Authentication module
│       │   ├── router.py                 # /api/auth/*
│       │   └── service.py
│       │
│       ├── projects/                     # Project CRUD module
│       │   ├── router.py                 # /api/projects/*
│       │   └── service.py
│       │
│       ├── phases/                       # Pipeline phase modules
│       │   ├── base_agent.py
│       │   │
│       │   ├── script_to_trailer/        # Phase 1
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   ├── prompts.py
│       │   │   └── agents/
│       │   │
│       │   ├── trailer_to_storyboard/    # Phase 2
│       │   │   ├── router.py
│       │   │   ├── service.py
│       │   │   ├── prompts.py
│       │   │   ├── image_generator.py
│       │   │   └── agents/
│       │   │
│       │   └── storyboard_to_movie/      # Phase 3
│       │       ├── router.py
│       │       ├── service.py
│       │       ├── prompts.py
│       │       ├── video_generator.py
│       │       └── agents/
│       │
│       ├── workflow/                     # Pipeline orchestration
│       │   ├── router.py
│       │   ├── orchestrator.py
│       │   └── service.py
│       │
│       └── system/                       # Health checks
│           └── router.py
│
├── client/                               # React frontend
│   └── src/
│       ├── lib/api.ts                    # REST API client
│       ├── _core/hooks/                  # React hooks
│       ├── pages/                        # Page components
│       └── components/                   # UI components
│
└── drizzle/                              # Legacy schema (reference only)
```

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- pnpm

### Environment Variables

Create `.env` in the `backend/` directory:

```env
# Database
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/script_to_movie

# JWT
JWT_SECRET=your-secret-key-change-in-production

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# AWS S3 (optional for local dev)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=
```

### Running Locally

**1. Start the database:**
```bash
# Using Docker
docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=password -e MYSQL_DATABASE=script_to_movie -p 3306:3306 mysql:8

# Or use existing MySQL and create database
mysql -u root -p -e "CREATE DATABASE script_to_movie;"
```

**2. Set up the backend:**
```bash
cd script_to_movie/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run migrations (if needed)
alembic upgrade head

# Start the backend
uvicorn app.main:app --reload --port 8000
```

**3. Start the frontend:**
```bash
cd script_to_movie

# Install dependencies
pnpm install

# Start dev server (proxies /api to backend)
pnpm dev
```

**4. Access the app:**
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/api/docs
- OpenAPI spec: http://localhost:8000/api/openapi.json

---

## API Endpoints

### Auth
- `GET /api/auth/me` - Current user
- `POST /api/auth/register` - Register
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project
- `GET /api/projects/{id}/scenes` - Get scenes
- `GET /api/projects/{id}/characters` - Get characters
- `GET /api/projects/{id}/settings` - Get settings
- `GET /api/projects/{id}/storyboards` - Get storyboards
- `GET /api/projects/{id}/movie` - Get final movie

### Phase: Script → Trailer
- `POST /api/phases/script-to-trailer/{project_id}/analyze`
- `POST /api/phases/script-to-trailer/{project_id}/characters`
- `POST /api/phases/script-to-trailer/{project_id}/settings`
- `POST /api/phases/script-to-trailer/{project_id}/select-scenes`

### Phase: Trailer → Storyboard
- `POST /api/phases/trailer-to-storyboard/{project_id}/generate`
- `GET /api/phases/trailer-to-storyboard/{project_id}/status`

### Phase: Storyboard → Movie
- `POST /api/phases/storyboard-to-movie/{project_id}/prompts`
- `POST /api/phases/storyboard-to-movie/{project_id}/generate`
- `POST /api/phases/storyboard-to-movie/{project_id}/assemble`
- `GET /api/phases/storyboard-to-movie/{project_id}/status`

### Workflow
- `POST /api/workflow/{project_id}/start` - Start full pipeline
- `GET /api/workflow/{project_id}/status` - Get status
- `POST /api/workflow/{project_id}/pause` - Pause
- `POST /api/workflow/{project_id}/resume` - Resume

### System
- `GET /api/system/health` - Health check

---

## Database Schema

| Table | Purpose |
|-------|---------|
| **users** | User accounts and authentication |
| **projects** | Project metadata, script content, status, progress |
| **scenes** | Individual scenes with descriptions, characters, settings |
| **characters** | Character names and visual descriptions |
| **settings** | Location names and visual descriptions |
| **storyboardImages** | Generated storyboard images |
| **videoPrompts** | Optimized video generation prompts |
| **generatedVideos** | Video clips for each scene |
| **finalMovies** | Assembled trailer videos |

---

## Development Status

### Implemented
- Backend structure (FastAPI, SQLAlchemy, Pydantic)
- Core infrastructure (auth, database, LLM client, S3)
- SQLAlchemy models matching existing schema
- Frontend API client (REST + React Query)
- Basic frontend with project management

### TODO: Implement
- Auth endpoints (register, login, logout, me)
- Project CRUD endpoints
- Phase 1 agents: Script Analysis, Character/Setting Consistency, Trailer Selection
- Phase 2 agents: Storyboard Prompt, Image Generation
- Phase 3 agents: Video Prompt, Video Generation, Video Assembly
- Workflow orchestration
- Alembic migrations for schema changes

---

## Agent Architecture

Each pipeline stage is handled by a specialized AI agent:

| Agent | Phase | Responsibility |
|-------|-------|----------------|
| **ScriptAnalysisAgent** | 1 | Parses screenplay structure, extracts scenes/characters/settings |
| **CharacterConsistencyAgent** | 1 | Creates consistent character visual descriptions |
| **SettingConsistencyAgent** | 1 | Creates consistent location visual descriptions |
| **TrailerSelectionAgent** | 1 | Selects most impactful scenes for trailer |
| **StoryboardPromptAgent** | 2 | Generates image prompts for storyboard |
| **VideoPromptAgent** | 3 | Optimizes prompts for video generation |
| **VideoGenerationAgent** | 3 | Invokes video generation APIs |
| **VideoAssemblyAgent** | 3 | Assembles final trailer from clips |

### How Agents Work

1. **Chain-of-Thought Reasoning**: Agents think step-by-step before producing output
2. **Structured Output**: Agents return Pydantic-validated responses via Claude tool use
3. **Workflow Orchestration**: The orchestrator manages agent execution sequence
4. **Error Recovery**: Failed steps can be retried with refined prompts

---

## Related Documentation

- [AGENT_ARCHITECTURE.md](script_to_movie/AGENT_ARCHITECTURE.md) - Technical agent implementation details
- [AGENT_INTEGRATION_GUIDE.md](script_to_movie/AGENT_INTEGRATION_GUIDE.md) - Frontend integration patterns
