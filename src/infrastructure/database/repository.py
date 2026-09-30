"""
PostgreSQL implementation of ChangeRepository.

Uses SQLAlchemy async session. ON CONFLICT DO NOTHING ensures idempotency.
"""
import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.ports import ChangeRepository
from src.domain.entities.inventory_change import InventoryChange
from src.infrastructure.database.models import InventoryChangeModel


class PostgresChangeRepository(ChangeRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_existing_hashes(self, product_id: str) -> set[str]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(InventoryChangeModel.data_hash).where(
                    InventoryChangeModel.product_id == product_id
                )
            )
            return {row[0] for row in result.all()}

    async def save(self, change: InventoryChange) -> None:
        async with self._session_factory() as session:
            stmt = pg_insert(InventoryChangeModel).values(
                id=str(uuid.uuid4()),
                product_id=change.product_id,
                data_hash=change.data_hash,
                data=change.data,
                source=change.source,
                changed_at=change.changed_at,
            ).on_conflict_do_nothing(constraint="uq_product_data_hash")
            await session.execute(stmt)
            await session.commit()

    async def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(InventoryChangeModel)
                .order_by(InventoryChangeModel.created_at.desc())
                .limit(limit)
            )
            return [row.to_dict() for row in result.scalars().all()]
