# Developer Guide — Script-to-Movie

A complete guide for setting up, understanding, and working on this project. Written for people who are new to development and will be using **Claude Code** as their main tool.

---

## Table of Contents

1. [What This App Does](#what-this-app-does)
2. [How the Tech Stack Works](#how-the-tech-stack-works)
3. [Install Prerequisites](#install-prerequisites)
4. [Set Up the Project Locally](#set-up-the-project-locally)
5. [Project Structure](#project-structure)
6. [How the Pipeline Works](#how-the-pipeline-works)
7. [Working on a Phase](#working-on-a-phase)
8. [Using Claude Code](#using-claude-code)
9. [Common Tasks](#common-tasks)
10. [Database Guide](#database-guide)
11. [API Reference](#api-reference)
12. [Testing Your Work](#testing-your-work)
13. [Troubleshooting](#troubleshooting)
14. [Deploying to AWS](#deploying-to-aws)

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

| Service | What it does |
|---------|-------------|
| **Claude API (Anthropic)** | Parses scripts, generates prompts, analyzes scenes |
| **Kling AI** | Generates video clips from images + text prompts |
| **gTTS** | Converts dialogue text into spoken audio |
| **ffmpeg** | Merges audio + video, concatenates clips into final movie |

---

## Install Prerequisites

You need these installed on your machine before you can run the app. Ask Claude Code to run each command for you.

### 1. Python 3.11+

```bash
# macOS
brew install python@3.11

# Verify
python3.11 --version
```

### 2. Node.js 20+ and pnpm

```bash
# macOS
brew install node

# Install pnpm (the package manager this project uses)
npm install -g pnpm

# Verify
node --version
pnpm --version
```

### 3. MySQL

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

### 4. ffmpeg (required for Phase 3 video assembly)

```bash
# macOS
brew install ffmpeg

# Verify
ffmpeg -version
```

### 5. Git

```bash
# macOS (usually pre-installed)
git --version

# If not installed
brew install git
```

---

## Set Up the Project Locally

### Step 1: Clone the repo

```bash
git clone YOUR_REPO_URL script-to-movie
cd script-to-movie
```

### Step 2: Create the MySQL database

```bash
mysql -u root -e "CREATE DATABASE script_to_movie;"
```

### Step 3: Set up the backend

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

### Step 4: Fill in your `.env` file

Open `script_to_movie/backend/.env` and fill in the values. Here's what each one means:

```bash
# Database — connects to your local MySQL
# Format: mysql+aiomysql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
DATABASE_URL=mysql+aiomysql://root:@localhost:3306/script_to_movie
# Note: if your MySQL root has no password, leave it as root:@
# If you set a password, use root:yourpassword@

# JWT — used to sign authentication tokens
# Generate a random one by running: openssl rand -hex 32
JWT_SECRET=paste-a-long-random-string-here

# Claude API — required for script parsing and prompt generation
# Get your key at: https://console.anthropic.com → API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Kling AI — required for Phase 3 video generation
# Get your keys from the Kling AI dashboard
KLING_API_KEY=your-key
KLING_SECRET_KEY=your-secret

# AWS S3 — for storing images and videos
# Leave blank for now; the app falls back to local storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=

# App settings
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

**Minimum to get started:** You need `DATABASE_URL`, `JWT_SECRET`, and `ANTHROPIC_API_KEY`. Everything else can be filled in later as you work on specific phases.

### Step 5: Run database migrations

This creates all the tables in your MySQL database:

```bash
# Make sure you're in script_to_movie/backend with venv activated
alembic upgrade head
```

### Step 6: Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

`--reload` means the server restarts automatically when you change code. You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Open http://localhost:8000/docs in your browser — you'll see the interactive API documentation (Swagger UI). This is where you can test every endpoint.

### Step 7: Set up and start the frontend

Open a **new terminal** (keep the backend running in the first one):

```bash
cd script-to-movie/script_to_movie

# Install frontend dependencies
pnpm install

# Start the development server
pnpm dev
```

Open http://localhost:5173 in your browser — you should see the app.

### You're running!

You now have:
- Backend API at http://localhost:8000 (Swagger docs at http://localhost:8000/docs)
- Frontend at http://localhost:5173
- MySQL database with all tables created

---

## Project Structure

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
│   └── _core/
│       ├── index.ts                ← Server entry point
│       ├── trpc.ts                 ← tRPC setup
│       └── ...
│
├── client/                         ← React frontend
│   └── src/
│       ├── App.tsx                 ← Root component
│       ├── pages/                  ← Page components
│       ├── components/             ← Reusable UI components
│       ├── hooks/                  ← Custom React hooks
│       └── _core/                  ← API client, utilities
│
├── shared/                         ← Types shared between frontend and server
├── package.json                    ← Frontend/server dependencies
├── vite.config.ts                  ← Vite build configuration
├── AGENT_ARCHITECTURE.md           ← How the agent system works
├── AGENT_INTEGRATION_GUIDE.md      ← How frontend talks to backend
├── AWS_SETUP_GUIDE.md              ← Deploying to AWS
└── todo.md                         ← What's been built and what's left
```

### What can I modify?

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

## How the Pipeline Works

### The Agent Pattern

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

### How phases communicate

Phases **never import code from each other**. They communicate through the database only:

```
Phase 1 writes Scene records → Phase 2 reads Scene records
Phase 2 writes StoryboardImage records → Phase 3 reads StoryboardImage records
Phase 3 writes FinalMovie record → Frontend reads FinalMovie record
```

### The database tables

```
users ──────────────────────────────────────────────────────
projects ──┬── scenes ──┬── storyboardImages
            │            ├── videoPrompts
            │            └── generatedVideos
            ├── characters
            ├── settings
            └── finalMovies
```

Each table is defined as a Python class in `app/models/`. When you see `Scene.projectId`, that means "the scenes table has a column called projectId that links to the projects table."

---

## Working on a Phase

### Before you start

1. Read your phase's `README.md` — it explains what your phase does, what inputs you receive, and what outputs you produce
2. Read your phase's `PLAN.md` — it has a task checklist
3. Read `backend/CLAUDE.md` — it has code examples for every shared module

### Phase directory structure

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

### Development workflow

1. **Read the existing code** — understand what's already built
2. **Start with the simplest agent** — get one working before building the next
3. **Test through the API** — use the Swagger docs at http://localhost:8000/docs or curl
4. **Check the database** — verify your agent wrote the correct data
5. **Move to the next agent** — build on what works

---

## Using Claude Code

Claude Code is your development partner. Here's how to use it effectively for this project.

### Setting up

```
"Set up the Script-to-Movie backend for local development"
"Create my .env file with the database URL for local MySQL"
"Run the database migrations"
"Start the backend server"
```

### Understanding the codebase

```
"Explain how the Scene model works"
"Show me how the LLM client is used in existing agents"
"What does the video_assembly.py file do?"
"How does Phase 1 pass data to Phase 2?"
```

### Writing code

```
"Implement the script_analysis agent for Phase 1"
"Write a function that generates TTS audio from scene dialogue"
"Add error handling to the video generation agent"
```

### Debugging

```
"The backend won't start — read the error and help me fix it"
"My agent returns an empty list of scenes — help me debug the database query"
"The alembic migration failed — what went wrong?"
```

### Testing

```
"Test the /api/phases/script-to-trailer/1/parse endpoint with curl"
"Check what data is in the scenes table for project 1"
"Run the full Phase 3 pipeline for project 1"
```

### Git

```
"Show me what files I changed"
"Commit my changes with a descriptive message"
"Push my branch to the remote"
```

### Tips

- **Be specific.** "Fix the bug" is vague. "The video_assembly function fails when a scene has no dialogue — fix the None check on line 120" is clear.
- **Point to files.** "Look at agents/video_assembly.py and fix the download timeout" saves time.
- **Ask it to explain.** If you don't understand code someone else wrote, ask Claude Code to explain it before modifying it.
- **Let it read first.** Claude Code should read a file before editing it. If it suggests changes without reading, ask it to read the file first.

---

## Common Tasks

### Start the development servers

```bash
# Terminal 1: Backend
cd script_to_movie/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd script_to_movie
pnpm dev
```

### Create a test user

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "password123", "name": "Test User"}'
```

### Log in and save the session cookie

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "password123"}' \
  -c cookies.txt

# Now use -b cookies.txt with all other requests
```

### Create a project

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "title": "My Test Movie",
    "scriptContent": "FADE IN:\n\nINT. COFFEE SHOP - MORNING\n\nALICE sits alone at a table.\n\nALICE\nI have been waiting for hours.\n\nBOB enters, out of breath.\n\nBOB\nSorry I am late. Traffic was terrible.\n\nFADE OUT."
  }'
```

### Check what's in the database

```bash
# Connect to MySQL
mysql -u root script_to_movie

# Useful queries
SELECT id, title, status, progress FROM projects;
SELECT id, projectId, sceneNumber, title FROM scenes ORDER BY projectId, `order`;
SELECT id, sceneId, status FROM generatedVideos;
SELECT id, projectId, status, movieUrl FROM finalMovies;
```

### Reset a project (start over)

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

### View API documentation

Open http://localhost:8000/docs in your browser. This interactive page lets you:
- See every available endpoint
- Try requests directly from the browser
- View request/response schemas

---

## Database Guide

### How to read a model file

Take `app/models/scene.py` as an example:

```python
class Scene(Base):
    __tablename__ = "scenes"                    # ← The actual MySQL table name

    id: Mapped[int] = mapped_column(primary_key=True)  # ← Auto-incrementing ID
    projectId: Mapped[int] = mapped_column(ForeignKey("projects.id"))  # ← Links to projects table
    sceneNumber: Mapped[int]                    # ← 1, 2, 3...
    title: Mapped[str]                          # ← "Opening Scene"
    description: Mapped[str]                    # ← Visual description
    dialogue: Mapped[str | None]                # ← Character lines (can be empty)
    duration: Mapped[int | None]                # ← Seconds
    order: Mapped[int]                          # ← Sort order for assembly

    # Relationships — lets you access related data
    project: Mapped["Project"] = relationship(back_populates="scenes")
    generated_videos: Mapped[List["GeneratedVideo"]] = relationship(...)
```

### Common database operations

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

### All 9 tables

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

## API Reference

### Authentication

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create a new user account |
| POST | `/api/auth/login` | Log in, receive session cookie |
| POST | `/api/auth/logout` | Log out, clear session |
| GET | `/api/auth/me` | Get current user info |

### Projects

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

### Phase 1: Script to Trailer

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/phases/script-to-trailer/{id}/parse` | Parse script into scenes |
| POST | `/api/phases/script-to-trailer/{id}/generate-trailer` | Generate trailer video |
| GET | `/api/phases/script-to-trailer/{id}/status` | Check Phase 1 progress |

### Phase 2: Trailer to Storyboard

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/phases/trailer-to-storyboard/{id}/generate` | Generate storyboard |
| GET | `/api/phases/trailer-to-storyboard/{id}/status` | Check Phase 2 progress |

### Phase 3: Storyboard to Movie

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/phases/storyboard-to-movie/{id}/prompts` | Generate video prompts |
| POST | `/api/phases/storyboard-to-movie/{id}/generate` | Generate video clips |
| POST | `/api/phases/storyboard-to-movie/{id}/assemble` | Assemble final movie |
| GET | `/api/phases/storyboard-to-movie/{id}/status` | Check Phase 3 progress |

### Full Pipeline

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/workflow/{id}/start` | Run all 3 phases automatically |
| GET | `/api/workflow/{id}/status` | Check overall pipeline progress |

All endpoints (except auth) require authentication. Pass `-b cookies.txt` with curl or include the session cookie in your requests.

---

## Testing Your Work

### Test a single endpoint

```bash
# Example: run Phase 3 video assembly for project 1
curl -X POST http://localhost:8000/api/phases/storyboard-to-movie/1/assemble \
  -b cookies.txt
```

### Check the response

A successful response looks like:

```json
{
  "status": "success",
  "message": "Assembled 5 clips into final movie",
  "clips_assembled": 5,
  "total_duration": 40,
  "movie_url": "media/projects/1/final_movie.mp4"
}
```

An error response looks like:

```json
{
  "status": "error",
  "message": "No completed videos found — run video generation first"
}
```

### Verify data in the database

After running an agent, check that it wrote the correct data:

```bash
mysql -u root script_to_movie -e "SELECT id, status, movieUrl FROM finalMovies WHERE projectId = 1;"
```

### Test the full pipeline

1. Create a project with a script (see [Common Tasks](#common-tasks))
2. Run Phase 1: `curl -X POST .../script-to-trailer/1/parse -b cookies.txt`
3. Check scenes were created: `mysql ... -e "SELECT * FROM scenes WHERE projectId = 1;"`
4. Run Phase 2: `curl -X POST .../trailer-to-storyboard/1/generate -b cookies.txt`
5. Check storyboards: `mysql ... -e "SELECT * FROM storyboardImages WHERE projectId = 1;"`
6. Run Phase 3 steps in order: prompts → generate → assemble
7. Check final movie: `mysql ... -e "SELECT * FROM finalMovies WHERE projectId = 1;"`

---

## Troubleshooting

### Backend won't start

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

### Frontend won't start

**"pnpm: command not found"**
- Install it: `npm install -g pnpm`

**"Cannot find module"**
- Install dependencies: `pnpm install`

### API returns 401 Unauthorized

- You need to log in first and include the session cookie
- Register: `curl -X POST .../api/auth/register -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"password123","name":"Test"}'`
- Log in: `curl -X POST .../api/auth/login -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"password123"}' -c cookies.txt`
- Use `-b cookies.txt` with all other requests

### Alembic migration fails

**"Can't locate revision"**
- Your migration history may be out of sync. Ask Claude Code:
  "The alembic migration failed with this error: (paste error). Help me fix it."

### Agent returns "No scenes found"

- The previous phase hasn't run yet. Phases must run in order: 1 → 2 → 3
- Check what data exists: `mysql -u root script_to_movie -e "SELECT COUNT(*) FROM scenes WHERE projectId = 1;"`

### ffmpeg errors

**"ffmpeg: command not found"**
- Install it: `brew install ffmpeg`

**"ffmpeg error: ..."**
- The error message from ffmpeg is usually descriptive. Ask Claude Code to help interpret it.

### S3 upload fails

- If you haven't configured AWS credentials, this is expected. The app falls back to saving files in a local `media/` directory instead.
- To set up S3, see the [AWS Setup Guide](./AWS_SETUP_GUIDE.md)

---

## Deploying to AWS

When you're ready to put the app on the internet, follow the [AWS Setup Guide](./AWS_SETUP_GUIDE.md). It covers:

- Creating an AWS account
- Setting up S3 for file storage
- Setting up RDS for the MySQL database (same MySQL, hosted by AWS)
- Launching an EC2 server to run the app
- Configuring everything with step-by-step commands

The guide is written for beginners with no AWS experience. You can ask Claude Code to run every command in it.
