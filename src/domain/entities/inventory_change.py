"""
Domain entity: InventoryChange.

Pure Python — no FastAPI, SQLAlchemy, httpx, or any infra dependency.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class InventoryChange:
    product_id: str
    data: dict[str, Any]
    source: str
    changed_at: datetime = field(default_factory=datetime.utcnow)
    data_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.data_hash = self._compute_hash(self.data)

    @staticmethod
    def _compute_hash(data: dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
