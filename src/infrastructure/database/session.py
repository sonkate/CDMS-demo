"""
SQLAlchemy async engine and session factory.

DATABASE_URL is required — loaded from environment via Settings.
"""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings

async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)
