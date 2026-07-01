from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.categories import list_categories
from app.schemas.category import CategoryResponse


router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[CategoryResponse])
async def list_categories_endpoint(db: AsyncSession = Depends(get_db)):
    return await list_categories(db)
