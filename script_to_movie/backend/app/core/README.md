# Core Module

## Role

Provides shared infrastructure used by all feature modules. **This module is already implemented.**

## Components

| File | Status | Description |
|------|--------|-------------|
| `database.py` | ✅ Done | SQLAlchemy async engine, session factory, Base class |
| `security.py` | ✅ Done | JWT creation/verification, password hashing (bcrypt) |
| `dependencies.py` | ✅ Done | FastAPI dependencies (`get_db`, `get_current_user`) |
| `llm.py` | ✅ Done | Anthropic Claude client with structured output support |
| `storage.py` | ✅ Done | S3 client for file uploads/downloads |

## Usage Examples

### Database Session

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

### Authentication

```python
from app.core.dependencies import get_current_user
from app.models.user import User

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return user
```

### LLM Calls

```python
from app.core.llm import llm_client
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    summary: str
    themes: list[str]

# Simple text response
response = await llm_client.invoke(
    messages=[{"role": "user", "content": "Analyze this script..."}],
    system="You are a screenplay analyst."
)

# Structured output (uses Claude tool use)
result = await llm_client.invoke_structured(
    messages=[{"role": "user", "content": script_content}],
    output_schema=AnalysisResult,
    system="Analyze the screenplay."
)
```

### S3 Storage

```python
from app.core.storage import storage_client

# Upload
url = await storage_client.upload(
    key="projects/123/image.jpg",
    data=image_bytes,
    content_type="image/jpeg"
)

# Download
data = await storage_client.download(key="projects/123/image.jpg")

# Presigned URL
url = storage_client.get_presigned_url(key="projects/123/video.mp4")
```

## Configuration

All settings come from environment variables via `app/config.py`:

```env
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/script_to_movie
JWT_SECRET=your-secret-key
ANTHROPIC_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=your-bucket
```
