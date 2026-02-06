from datetime import datetime
from pydantic import BaseModel


class SceneBase(BaseModel):
    sceneNumber: int
    title: str
    description: str
    setting: str | None = None
    characters: str | None = None  # JSON array as string
    duration: int | None = None
    order: int


class SceneCreate(SceneBase):
    projectId: int


class SceneResponse(SceneBase):
    id: int
    projectId: int
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
