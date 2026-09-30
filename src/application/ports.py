"""
Application layer ports (abstract interfaces).

These define WHAT the application needs — not HOW it's implemented.
Concrete implementations live in infrastructure/.
"""
from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.inventory_change import InventoryChange


class InventoryPort(ABC):
    """Abstraction over any inventory data source."""

    @abstractmethod
    async def fetch_all(self) -> list[dict[str, Any]]:
        """Fetch all current product records as raw dicts."""
        ...


class ChangeRepository(ABC):
    """Abstraction over the change persistence store."""

    @abstractmethod
    async def get_existing_hashes(self, product_id: str) -> set[str]:
        """Return all known data_hash values for a given product_id."""
        ...

    @abstractmethod
    async def save(self, change: InventoryChange) -> None:
        """Persist a new change. Must be idempotent (ON CONFLICT DO NOTHING)."""
        ...

    @abstractmethod
    async def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent changes ordered by created_at DESC."""
        ...
