from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.users import create_user, get_user_by_email, get_user_by_username
from app.schemas.auth import UserUpdateRequest


async def register(db: AsyncSession, email: str, username: str, display_name: str, password: str):
    if await get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if await get_user_by_username(db, username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    user = await create_user(db, email, username, display_name, hash_password(password))
    await db.commit()
    return user


async def login(db: AsyncSession, email: str, password: str) -> str:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return create_access_token(user.id)


async def update_profile(db: AsyncSession, user: User, payload: UserUpdateRequest) -> User:
    has_changes = any(
        value is not None
        for value in (payload.email, payload.username, payload.display_name, payload.new_password)
    )
    if has_changes:
        if not payload.current_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is required")
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    if payload.email is not None and payload.email.lower() != user.email:
        existing = await get_user_by_email(db, str(payload.email))
        if existing and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user.email = str(payload.email).lower()

    if payload.username is not None and payload.username != user.username:
        existing = await get_user_by_username(db, payload.username)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
        user.username = payload.username

    if payload.display_name is not None:
        user.display_name = payload.display_name

    if payload.new_password:
        user.password_hash = hash_password(payload.new_password)

    await db.commit()
    await db.refresh(user)
    return user
