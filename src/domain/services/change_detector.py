"""
Domain service: change detection.

Pure function — no side effects, no I/O.
"""
from src.domain.entities.inventory_change import InventoryChange


def is_new_change(existing_hashes: set[str], change: InventoryChange) -> bool:
    """Return True if this change has not been seen before."""
    return change.data_hash not in existing_hashes
