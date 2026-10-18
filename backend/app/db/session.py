"""Async SQLAlchemy session factory."""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from app.config import settings


def get_async_database_url(url: str) -> str:
    parsed = make_url(url)
    if parsed.drivername in ("postgres", "postgresql"):
        parsed = parsed.set(drivername="postgresql+asyncpg")
    if parsed.drivername == "postgresql+asyncpg":
        query = dict(parsed.query)
        # Hosted Postgres URLs use libpq options; asyncpg names TLS "ssl".
        if "sslmode" in query:
            query["ssl"] = query.pop("sslmode")
        query.pop("channel_binding", None)
        parsed = parsed.set(query=query)
    return parsed.render_as_string(hide_password=False)


engine = create_async_engine(
    get_async_database_url(settings.DATABASE_URL), echo=settings.DEBUG, future=True,
    **({"poolclass": NullPool} if settings.ENVIRONMENT == "production" else {}),
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
