from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt
from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.verify(password, password_hash)


def create_jwt_token(user_id: int, open_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiration_days)
    payload = {"sub": str(user_id), "openId": open_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ValueError("Email already registered")

    user = User(
        openId=str(uuid4()),
        email=data.email,
        name=data.name,
        passwordHash=hash_password(data.password),
        loginMethod="email",
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, data: UserLogin) -> User:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not user.passwordHash or not verify_password(data.password, user.passwordHash):
        raise ValueError("Invalid email or password")

    user.lastSignedIn = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(db: AsyncSession, token: str) -> User | None:
    payload = decode_jwt_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()
