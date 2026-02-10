from datetime import datetime
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    scriptContent: str


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    scriptContent: str | None = None


class ProjectResponse(BaseModel):
    id: int
    userId: int
    title: str
    description: str | None
    scriptContent: str
    status: str
    progress: int
    errorMessage: str | None
    trailerUrl: str | None = None
    trailerKey: str | None = None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    progress: int
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
