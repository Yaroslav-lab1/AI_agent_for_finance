from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from app.schemas.category import CategoryResponse
from app.schemas.transaction import TransactionResponse


class TextImportRequest(BaseModel):
    text: str = Field(min_length=1)


class ImportJobResponse(BaseModel):
    id: UUID
    source_type: str
    status: str
    candidates_count: int
    error_message: str | None = None

    model_config = {"from_attributes": True}


class ImportCandidateResponse(BaseModel):
    id: UUID
    amount: Decimal
    operation_type: str
    category: CategoryResponse
    occurred_at: date
    comment: str | None
    confidence: Decimal
    duplicate_status: str
    duplicate_transaction_id: UUID | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount", "confidence")
    def serialize_decimal(self, value: Decimal) -> str:
        return f"{value:.2f}"


class ImportPreviewResponse(BaseModel):
    job: ImportJobResponse
    candidates: list[ImportCandidateResponse]


class CandidateUpdateRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    operation_type: str = Field(pattern="^(income|expense)$")
    category_id: UUID
    occurred_at: date
    comment: str | None = Field(default=None, max_length=500)


class ConfirmImportRequest(BaseModel):
    candidate_ids: list[UUID]
    reject_other_candidates: bool = True


class ConfirmImportResponse(BaseModel):
    created_transactions: list[TransactionResponse]
