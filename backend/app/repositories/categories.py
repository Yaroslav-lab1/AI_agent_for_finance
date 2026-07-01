from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


DEFAULT_CATEGORIES = [
    ("products", "Продукты", "expense"),
    ("transport", "Транспорт", "expense"),
    ("restaurants", "Кафе и рестораны", "expense"),
    ("entertainment", "Развлечения", "expense"),
    ("health", "Здоровье", "expense"),
    ("transfers", "Переводы", None),
    ("salary", "Зарплата", "income"),
    ("other", "Другое", None),
]


async def list_categories(db: AsyncSession) -> list[Category]:
    return list((await db.scalars(select(Category).order_by(Category.name))).all())


async def get_category(db: AsyncSession, category_id) -> Category | None:
    return await db.get(Category, category_id)


async def get_category_by_slug(db: AsyncSession, slug: str) -> Category | None:
    return await db.scalar(select(Category).where(Category.slug == slug))


async def seed_categories(db: AsyncSession) -> None:
    existing = {category.slug for category in await list_categories(db)}
    for slug, name, hint in DEFAULT_CATEGORIES:
        if slug not in existing:
            db.add(Category(slug=slug, name=name, operation_type_hint=hint))
    await db.flush()
