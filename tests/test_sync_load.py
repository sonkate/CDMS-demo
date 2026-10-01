import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.ports import ChangeRepository, InventoryPort
from src.application.use_cases.sync_inventory import SyncInventory
from src.domain.entities.inventory_change import InventoryChange
from src.infrastructure.database.models import Base, InventoryChangeModel
from src.infrastructure.database.repository import PostgresChangeRepository


class StaticInventory(InventoryPort):
    def __init__(self, products: list[dict]) -> None:
        self._products = products

    async def fetch_all(self) -> list[dict]:
        return [dict(product) for product in self._products]


class InMemoryUniqueRepository(ChangeRepository):
    def __init__(self) -> None:
        self._changes: dict[tuple[str, str], InventoryChange] = {}
        self._lock = asyncio.Lock()

    async def get_existing_hashes(self, product_id: str) -> set[str]:
        await asyncio.sleep(0)
        return {
            data_hash
            for stored_product_id, data_hash in self._changes
            if stored_product_id == product_id
        }

    async def save(self, change: InventoryChange) -> None:
        await asyncio.sleep(0)
        async with self._lock:
            self._changes.setdefault(
                (change.product_id, change.data_hash), change
            )

    async def get_recent(self, limit: int = 50) -> list[dict]:
        return []

    @property
    def stored_change_count(self) -> int:
        return len(self._changes)


def make_products(count: int, namespace: str, version: int = 1) -> list[dict]:
    return [
        {
            "product_id": f"{namespace}-{index}",
            "name": f"Product {index}",
            "quantity": version,
        }
        for index in range(count)
    ]


async def test_sync_spike_persists_large_product_batch_once() -> None:
    product_count = 2_000
    repository = InMemoryUniqueRepository()
    sync = SyncInventory(
        StaticInventory(make_products(product_count, "spike")),
        repository,
    )

    first_saved = await sync.execute()
    second_saved = await sync.execute()

    assert first_saved == product_count
    assert second_saved == 0
    assert repository.stored_change_count == product_count


async def test_concurrent_syncs_store_only_one_copy_of_each_state() -> None:
    product_count = 200
    sync_count = 12
    repository = InMemoryUniqueRepository()
    products = make_products(product_count, "concurrent")

    await asyncio.gather(
        *(
            SyncInventory(StaticInventory(products), repository).execute()
            for _ in range(sync_count)
        )
    )

    assert repository.stored_change_count == product_count


async def test_postgres_concurrent_syncs_respect_unique_constraint() -> None:
    database_url = os.getenv("CDMS_SPIKE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip(
            "Set CDMS_SPIKE_TEST_DATABASE_URL to an isolated *_test database"
        )

    database_name = make_url(database_url).database
    if not database_name or not database_name.endswith("_test"):
        pytest.fail(
            "CDMS_SPIKE_TEST_DATABASE_URL must point to a database ending in _test"
        )

    namespace = f"load-{uuid4().hex}"
    products = make_products(100, namespace)
    engine = create_async_engine(database_url, pool_size=20, max_overflow=0)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    database_ready = False

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        database_ready = True

        repository = PostgresChangeRepository(session_factory)
        await asyncio.gather(
            *(
                SyncInventory(StaticInventory(products), repository).execute()
                for _ in range(12)
            )
        )

        async with session_factory() as session:
            stored_count = await session.scalar(
                select(func.count())
                .select_from(InventoryChangeModel)
                .where(InventoryChangeModel.product_id.like(f"{namespace}-%"))
            )

        assert stored_count == len(products)
    finally:
        try:
            if database_ready:
                async with engine.begin() as connection:
                    await connection.execute(
                        delete(InventoryChangeModel).where(
                            InventoryChangeModel.product_id.like(
                                f"{namespace}-%"
                            )
                        )
                    )
        finally:
            await engine.dispose()
