from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from app.schemas.category import CategoryResponse


class TransactionCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    operation_type: str = Field(pattern="^(income|expense)$")
    category_id: UUID
    occurred_at: date
    comment: str | None = Field(default=None, max_length=500)


class TransactionUpdate(TransactionCreate):
    pass


class TransactionResponse(BaseModel):
    id: UUID
    amount: Decimal
    operation_type: str
    category: CategoryResponse
    occurred_at: date
    comment: str | None
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, amount: Decimal) -> str:
        return f"{amount:.2f}"


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
