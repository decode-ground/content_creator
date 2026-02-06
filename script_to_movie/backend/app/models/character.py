from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    visualDescription: Mapped[str | None] = mapped_column(Text, nullable=True)
    imageUrl: Mapped[str | None] = mapped_column(String(512), nullable=True)
    imageKey: Mapped[str | None] = mapped_column(String(512), nullable=True)
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
    project: Mapped["Project"] = relationship(back_populates="characters")


from app.models.project import Project
