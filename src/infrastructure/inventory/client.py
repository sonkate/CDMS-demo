"""
HTTP client for the inventory service.

Implements InventoryPort — fetches products via HTTP GET /products.
"""
from typing import Any

import httpx

from src.application.ports import InventoryPort


class HttpInventoryClient(InventoryPort):
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def fetch_all(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self._base_url}/products")
            response.raise_for_status()
            return response.json()
