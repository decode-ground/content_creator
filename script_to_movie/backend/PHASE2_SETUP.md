# Phase 2 Development Setup Summary

## ✅ Completed Setup Tasks

### 1. Dependencies Installed
All Python dependencies from `pyproject.toml` have been installed:
- FastAPI, SQLAlchemy, Alembic
- Anthropic (Claude API)
- boto3 (AWS S3)
- aiomysql (database driver)
- All other required packages

### 2. Environment Template Created
Created `.env.example` with all required environment variables.

### 3. Base Agent Implemented
Implemented `app/phases/base_agent.py` with:
- Abstract `BaseAgent` class
- `reason()` - Chain-of-thought LLM calls
- `reason_structured()` - Structured output with Pydantic validation
- `reason_json()` - JSON output without schema
- Full type hints and documentation

All Phase 2 agents can now inherit from this base class.

---

## 🔴 Remaining Setup Tasks (Required Before Development)

### 1. Database Setup

**Action Required:**
```bash
# 1. Install and start MySQL (if not already running)
brew install mysql  # macOS
brew services start mysql

# 2. Create database
mysql -u root -p
CREATE DATABASE script_to_movie CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# 3. Copy and configure .env file
cd script_to_movie/backend
cp .env.example .env
# Edit .env with your database credentials
# Update DATABASE_URL if needed

# 4. Create and run migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**Database Tables That Will Be Created:**
- users
- projects
- scenes
- characters
- settings
- storyboardImages
- videoClips
- scriptVersions

### 2. Environment Configuration

**Edit `.env` file and add:**

```env
# Required for all phases
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Required for Phase 2 (image storage)
AWS_ACCESS_KEY_ID=your-actual-key
AWS_SECRET_ACCESS_KEY=your-actual-secret
S3_BUCKET=your-bucket-name

# For Phase 2 when you choose an image generation API:
# Option 1: OpenAI DALL-E 3
# OPENAI_API_KEY=sk-your-openai-key

# Option 2: Replicate
# REPLICATE_API_TOKEN=r8_your-replicate-token
```

### 3. Install Image Generation Library (When Ready)

When you decide on an image generation API, add the dependency:

```bash
# For DALL-E 3 (OpenAI)
pip install openai>=1.0.0

# For Replicate (Stable Diffusion XL, Flux, etc)
pip install replicate>=0.15.0

# For custom API calls
pip install httpx>=0.26.0  # Already installed
```

---

## 📋 Phase 2 Implementation Checklist

### Infrastructure (Ready to Use)
- ✅ LLM Client (`app/core/llm.py`)
- ✅ S3 Storage Client (`app/core/storage.py`)
- ✅ Base Agent Class (`app/phases/base_agent.py`)
- ✅ Database Models (StoryboardImage, Scene, Character, Setting)
- ✅ Pydantic Schemas (`app/schemas/storyboard.py`)
- ✅ Database Dependencies (`app/core/dependencies.py`)

### Phase 2 Files (Need Implementation)
- ❌ `prompts.py` - Prompt templates for image generation
- ❌ `agents/storyboard_prompt.py` - StoryboardPromptAgent class
- ❌ `image_generator.py` - Image generation API client
- ❌ `service.py` - Orchestration logic
- ❌ `router.py` - API endpoints (partial stub exists)

---

## 🎯 Next Steps for Phase 2 Development

### Step 1: Complete Environment Setup
1. Set up MySQL and create database
2. Configure `.env` with all API keys
3. Run database migrations
4. Test database connection

### Step 2: Make Key Design Decisions
Review `app/phases/trailer_to_storyboard/README.md` and decide on:

1. **Image Generation API** (DALL-E 3 vs Replicate vs others)
2. **Consistency Strategy** (how to maintain character/setting consistency)
3. **Image Specifications** (resolution, aspect ratio, format)
4. **Error Handling** (retry logic, fallback strategies)
5. **Background Processing** (sync vs async, progress updates)

### Step 3: Implement Phase 2 Components

**Recommended Order:**
1. `prompts.py` - Define prompt templates
2. `image_generator.py` - Implement image API client
3. `agents/storyboard_prompt.py` - Implement prompt generation agent
4. `service.py` - Orchestrate the full flow
5. `router.py` - Complete API endpoints

### Step 4: Testing
1. Unit tests for StoryboardPromptAgent
2. Integration tests for image generation
3. End-to-end test with sample project

---

## 📚 Key Documentation

- **Phase 2 Requirements:** `app/phases/trailer_to_storyboard/README.md`
- **Agent Architecture:** `script_to_movie/AGENT_ARCHITECTURE.md`
- **Database Models:** `app/models/storyboard.py`, `app/models/scene.py`
- **LLM Client Usage:** `app/core/README.md`
- **Storage Client Usage:** `app/core/README.md`

---

## 🚀 Quick Start Commands

```bash
# Navigate to backend
cd script_to_movie/backend

# Install dependencies (already done)
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Set up database
mysql -u root -p -e "CREATE DATABASE script_to_movie"
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# API documentation will be at:
# http://localhost:8000/api/docs
```

---

## 💡 Tips

1. **Test infrastructure first:** Before implementing Phase 2 logic, test that LLM client, S3 storage, and database all work.

2. **Start simple:** Implement a basic version first (e.g., one image per scene, simple prompts) then iterate.

3. **Use existing patterns:** Reference Phase 1 implementations for code patterns and structure.

4. **Incremental testing:** Test each component (prompts → agent → image gen → service) individually before integration.

5. **Monitor costs:** Image generation can be expensive. Start with a small test project.

---

## ❓ Questions or Issues?

- Database connection issues? Check `DATABASE_URL` in `.env`
- Import errors? Ensure you're in the `backend/` directory
- API key issues? Verify keys in `.env` and restart the server
- Migration issues? Try `alembic downgrade base` then `alembic upgrade head`
