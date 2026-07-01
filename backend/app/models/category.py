from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk


class Category(Base):
    __tablename__ = "categories"

    id = uuid_pk()
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    operation_type_hint: Mapped[str | None] = mapped_column(String(16), nullable=True)

    transactions = relationship("Transaction", back_populates="category")
