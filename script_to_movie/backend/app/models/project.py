from datetime import datetime

from sqlalchemy import String, Text, Enum, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scriptContent: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "parsing",
            "parsed",
            "generating_storyboard",
            "generating_videos",
            "assembling",
            "completed",
            "failed",
            name="project_status",
        ),
        nullable=False,
        default="draft",
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
    scenes: Mapped[list["Scene"]] = relationship(back_populates="project", lazy="selectin")
    characters: Mapped[list["Character"]] = relationship(back_populates="project", lazy="selectin")
    settings: Mapped[list["Setting"]] = relationship(back_populates="project", lazy="selectin")


from app.models.scene import Scene
from app.models.character import Character
from app.models.setting import Setting
