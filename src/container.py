"""
Dependency container — wires concrete infrastructure to use cases.

No DI framework. Plain Python functions.
"""
from src.application.use_cases.sync_inventory import SyncInventory
from src.config import settings
from src.infrastructure.database.repository import PostgresChangeRepository
from src.infrastructure.database.session import async_session_factory
from src.infrastructure.inventory.client import HttpInventoryClient


def build_sync_inventory() -> SyncInventory:
    repo = PostgresChangeRepository(async_session_factory)
    client = HttpInventoryClient(settings.inventory_url)
    return SyncInventory(inventory=client, repository=repo)


def build_change_repository() -> PostgresChangeRepository:
    return PostgresChangeRepository(async_session_factory)
