"""
SQLAlchemy ORM model for inventory_changes table.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InventoryChangeModel(Base):
    __tablename__ = "inventory_changes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    product_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    data_hash: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("product_id", "data_hash", name="uq_product_data_hash"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "data_hash": self.data_hash,
            "data": self.data,
            "source": self.source,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
