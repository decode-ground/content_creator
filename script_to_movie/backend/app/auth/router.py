from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.models.user import User
from app.schemas.user import AuthResponse, UserCreate, UserLogin, UserResponse
from app.auth import service

settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> UserResponse | None:
    if not user:
        return None
    return UserResponse.model_validate(user)


@router.post("/register")
async def register(
    body: UserCreate,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    user, token = await service.register_user(db, body.email, body.password, body.name)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.jwt_expiration_days * 24 * 60 * 60,
    )
    return AuthResponse(
        user=UserResponse.model_validate(user),
        message="Registration successful",
    )


@router.post("/login")
async def login(
    body: UserLogin,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    user, token = await service.login_user(db, body.email, body.password)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.jwt_expiration_days * 24 * 60 * 60,
    )
    return AuthResponse(
        user=UserResponse.model_validate(user),
        message="Login successful",
    )


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key="session")
    return {"message": "Logged out"}
