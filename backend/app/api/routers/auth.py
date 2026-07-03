from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse, UserUpdateRequest
from app.services.auth_service import login, register, update_profile


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_endpoint(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await register(db, payload.email, payload.username, payload.display_name, payload.password)


@router.post("/login", response_model=TokenResponse)
async def login_endpoint(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return TokenResponse(access_token=await login(db, payload.email, payload.password))


@router.get("/me", response_model=UserResponse)
async def me_endpoint(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me_endpoint(
    payload: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_profile(db, current_user, payload)
