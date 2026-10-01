"""
Use case: SyncInventory

Orchestrates the full scheduled-query flow:
  1. Fetch all products from the inventory source
  2. For each product, compute its hash and check if it's new
  3. Persist new changes
"""

import logging
from datetime import datetime, timezone

from src.application.ports import ChangeRepository, InventoryPort
from src.domain.entities.inventory_change import InventoryChange

logger = logging.getLogger(__name__)

SOURCE = "scheduled"


class SyncInventory:
    def __init__(
        self, inventory: InventoryPort, repository: ChangeRepository
    ) -> None:
        self._inventory = inventory
        self._repository = repository

    async def execute(self) -> int:
        """
        Fetch products and persist any new/changed records.

        Returns the number of new changes saved.
        """
        products = await self._inventory.fetch_all()
        logger.info("Fetched %d products from inventory", len(products))

        saved = 0
        for product in products:
            product_id = product.get("product_id")
            if not isinstance(product_id, str) or not product_id.strip():
                raise ValueError(
                    "Inventory product is missing a valid product_id"
                )
            change = InventoryChange(
                product_id=product_id,
                data=product,
                source=SOURCE,
                changed_at=datetime.now(timezone.utc),
            )
            if await self._repository.save(change):
                logger.info(
                    "Saved new change for product_id=%s hash=%s",
                    product_id,
                    change.data_hash[:8],
                )
                saved += 1

        logger.info("Sync complete: %d new change(s) saved", saved)
        return saved
