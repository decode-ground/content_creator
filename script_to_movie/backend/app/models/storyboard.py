from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.scene import Scene


class StoryboardImage(Base):
    __tablename__ = "storyboardImages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sceneId: Mapped[int] = mapped_column(Integer, ForeignKey("scenes.id"), nullable=False)
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    imageUrl: Mapped[str] = mapped_column(String(512), nullable=False)
    imageKey: Mapped[str] = mapped_column(String(512), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
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
    scene: Mapped["Scene"] = relationship(back_populates="storyboard_images")
