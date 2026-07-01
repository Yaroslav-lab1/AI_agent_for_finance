from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email.lower()))


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    return await db.scalar(select(User).where(User.username == username.lower()))


async def get_user_by_id(db: AsyncSession, user_id) -> User | None:
    return await db.get(User, user_id)


async def create_user(db: AsyncSession, email: str, username: str, display_name: str, password_hash: str) -> User:
    user = User(email=email.lower(), username=username.lower(), display_name=display_name, password_hash=password_hash)
    db.add(user)
    await db.flush()
    return user
