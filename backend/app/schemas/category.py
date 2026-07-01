from uuid import UUID

from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    operation_type_hint: str | None = None

    model_config = {"from_attributes": True}
