from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FinalMovie(Base):
    __tablename__ = "finalMovies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    projectId: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    movieUrl: Mapped[str | None] = mapped_column(String(512), nullable=True)
    movieKey: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "assembling", "completed", "failed", name="movie_status"),
        nullable=False,
        default="pending",
    )
    createdAt: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updatedAt: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
