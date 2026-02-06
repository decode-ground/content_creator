from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    openId: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    passwordHash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    loginMethod: Mapped[str | None] = mapped_column(String(64), nullable=True)
    role: Mapped[str] = mapped_column(
        Enum("user", "admin", name="user_role"),
        nullable=False,
        default="user",
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
    lastSignedIn: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
