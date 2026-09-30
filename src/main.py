"""
CDMS main entry point.

- Creates DB tables on startup (create_all)
- Starts APScheduler to run SyncInventory every 10 seconds
- Exposes /health and /changes endpoints
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.container import build_sync_inventory
from src.infrastructure.database.models import Base
from src.infrastructure.database.session import async_engine
from src.interface.api.changes import router as changes_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CDMS — Change Data Management Service", version="0.1.0")
app.include_router(changes_router)

scheduler = AsyncIOScheduler()


async def run_sync() -> None:
    """Scheduled job: sync inventory and persist changes."""
    try:
        use_case = build_sync_inventory()
        saved = await use_case.execute()
        logger.info("Scheduled sync done: %d new change(s)", saved)
    except Exception as exc:
        logger.error("Scheduled sync failed: %s", exc, exc_info=True)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")

    scheduler.add_job(run_sync, "interval", seconds=10, id="sync_inventory")
    scheduler.start()
    logger.info("Scheduler started — syncing every 10 seconds.")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    scheduler.shutdown(wait=False)
    await async_engine.dispose()
    logger.info("Shutdown complete.")


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
