from datetime import datetime
from pydantic import BaseModel


class SettingBase(BaseModel):
    name: str
    description: str
    visualDescription: str | None = None


class SettingCreate(SettingBase):
    projectId: int


class SettingResponse(SettingBase):
    id: int
    projectId: int
    imageUrl: str | None
    imageKey: str | None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
