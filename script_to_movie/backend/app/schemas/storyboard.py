from datetime import datetime
from pydantic import BaseModel


class StoryboardImageBase(BaseModel):
    imageUrl: str
    imageKey: str
    prompt: str | None = None
    status: str = "pending"


class StoryboardImageCreate(StoryboardImageBase):
    sceneId: int
    projectId: int


class StoryboardImageResponse(StoryboardImageBase):
    id: int
    sceneId: int
    projectId: int
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
