from datetime import datetime
from pydantic import BaseModel


class VideoPromptResponse(BaseModel):
    id: int
    sceneId: int
    projectId: int
    prompt: str
    duration: int | None = None
    style: str | None = None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}


class GeneratedVideoResponse(BaseModel):
    id: int
    sceneId: int
    projectId: int
    videoUrl: str | None = None
    videoKey: str | None = None
    duration: int | None = None
    status: str
    errorMessage: str | None = None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}


class FinalMovieResponse(BaseModel):
    id: int
    projectId: int
    movieUrl: str | None = None
    movieKey: str | None = None
    duration: int | None = None
    status: str
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}


class WorkflowStatusResponse(BaseModel):
    projectId: int
    status: str
    progress: int
    currentStep: str | None = None
    error: str | None = None
