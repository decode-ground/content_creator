from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.core.database import get_db
from app.schemas.user import AuthResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "session"


@router.get("/me", response_model=UserResponse | None)
async def me(
    db: Annotated[AsyncSession, Depends(get_db)],
    session: Annotated[str | None, Cookie()] = None,
):
    if not session:
        return None
    user = await service.get_current_user(db, session)
    if not user:
        return None
    return user


@router.post("/register", response_model=AuthResponse)
async def register(
    data: UserCreate,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        user = await service.register_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = service.create_jwt_token(user.id, user.openId)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
        path="/",
    )
    return AuthResponse(user=UserResponse.model_validate(user), message="Registration successful")


@router.post("/login", response_model=AuthResponse)
async def login(
    data: UserLogin,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        user = await service.login_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    token = service.create_jwt_token(user.id, user.openId)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
        path="/",
    )
    return AuthResponse(user=UserResponse.model_validate(user), message="Login successful")


@router.post("/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return None
