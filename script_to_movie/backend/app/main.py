from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.database import Base, engine
from app.auth.router import router as auth_router
from app.projects.router import router as projects_router
from app.phases.script_to_trailer.router import router as script_to_trailer_router
from app.phases.trailer_to_storyboard.router import router as trailer_to_storyboard_router
from app.phases.storyboard_to_movie.router import router as storyboard_to_movie_router
from app.workflow.router import router as workflow_router
from app.system.router import router as system_router

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Script to Movie API",
    description="Backend API for script to movie pipeline",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(script_to_trailer_router)
app.include_router(trailer_to_storyboard_router)
app.include_router(storyboard_to_movie_router)
app.include_router(workflow_router)
app.include_router(system_router)
