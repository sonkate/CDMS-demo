"""
GET /changes — returns the most recent inventory changes.
"""
import logging
from typing import Any

from fastapi import APIRouter

from src.container import build_change_repository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/changes", response_model=list[dict])
async def get_changes() -> list[dict[str, Any]]:
    """Return the last 50 inventory changes, newest first."""
    repo = build_change_repository()
    return await repo.get_recent(limit=50)
