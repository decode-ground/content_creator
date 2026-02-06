from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.scene import Scene


class VideoPrompt(Base):
    __tablename__ = "videoPrompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sceneId: Mapped[int] = mapped_column(Integer, ForeignKey("scenes.id"), nullable=False)
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    style: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    scene: Mapped["Scene"] = relationship(back_populates="video_prompts")


class GeneratedVideo(Base):
    __tablename__ = "generatedVideos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sceneId: Mapped[int] = mapped_column(Integer, ForeignKey("scenes.id"), nullable=False)
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    videoUrl: Mapped[str | None] = mapped_column(String(512), nullable=True)
    videoKey: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "generating", "completed", "failed", name="video_status"),
        nullable=False,
        default="pending",
    )
    errorMessage: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    scene: Mapped["Scene"] = relationship(back_populates="generated_videos")
