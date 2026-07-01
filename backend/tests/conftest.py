import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["ENVIRONMENT"] = "test"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["LLM_MODEL"] = "mock-transaction-extractor"

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import AgentAuditLog, Category, ImportCandidate, ImportJob, Transaction, User
from app.repositories.categories import get_category_by_slug, seed_categories


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        await seed_categories(session)
        await session.commit()
        yield session
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client


async def auth_headers(client: AsyncClient, email: str = "user@example.com") -> dict[str, str]:
    username = email.split("@")[0].replace(".", "_").replace("-", "_")
    await client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "display_name": username.title(), "password": "strong-password"},
    )
    response = await client.post("/api/auth/login", json={"email": email, "password": "strong-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def category_id(db_session: AsyncSession, slug: str = "products") -> str:
    category = await get_category_by_slug(db_session, slug)
    assert category is not None
    return str(category.id)
