# System Module

## Role

Provides health checks and system status endpoints for monitoring and deployment.

## Endpoints to Implement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system/health` | GET | Basic health check |

## Implementation

Simple implementation for `router.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for load balancers and monitoring.
    """
    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0",
    }
```

## Optional Enhancements

1. **Detailed health check** - Check all external services:
   - Database connection
   - Redis connection (if using)
   - S3 accessibility
   - LLM API availability

2. **Metrics endpoint** - For Prometheus/Grafana:
   - Request counts
   - Response times
   - Queue sizes

3. **Version info** - Include git commit hash, build time
