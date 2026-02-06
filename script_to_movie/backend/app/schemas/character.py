from datetime import datetime
from pydantic import BaseModel


class CharacterBase(BaseModel):
    name: str
    description: str
    visualDescription: str | None = None


class CharacterCreate(CharacterBase):
    projectId: int


class CharacterResponse(CharacterBase):
    id: int
    projectId: int
    imageUrl: str | None
    imageKey: str | None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
