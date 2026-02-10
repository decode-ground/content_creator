from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.storyboard import StoryboardImage
    from app.models.video import VideoPrompt, GeneratedVideo


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    sceneNumber: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    setting: Mapped[str | None] = mapped_column(String(255), nullable=True)
    characters: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    dialogue: Mapped[str | None] = mapped_column(Text, nullable=True)  # spoken lines in the scene
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updatedAt: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="scenes")
    storyboard_images: Mapped[List["StoryboardImage"]] = relationship(
        back_populates="scene", lazy="selectin"
    )
    video_prompts: Mapped[List["VideoPrompt"]] = relationship(
        back_populates="scene", lazy="selectin"
    )
    generated_videos: Mapped[List["GeneratedVideo"]] = relationship(
        back_populates="scene", lazy="selectin"
    )
