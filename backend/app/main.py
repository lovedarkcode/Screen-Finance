"""FastAPI application entry point."""
# Touch this file to force uvicorn --reload to re-import settings (which re-reads .env).
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.api.v1.filing_results import router as filing_results_router
from app.config import settings
from app.db.session import engine
from app.middleware import RequestContextMiddleware

logger = logging.getLogger("screen-finance")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            database, schema = (await conn.execute(text("SELECT current_database(), current_schema()"))).one()
        logger.info("Postgres connection OK: database=%s schema=%s host=%s port=%s", database, schema, engine.url.host, engine.url.port or 5432)
    except Exception as exc:
        logger.warning("Postgres connection FAILED at startup: %s", type(exc).__name__)

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(filing_results_router, prefix="/api")

    @app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        return {"status": "ok", "service": "screen-finance-backend"}

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/api/health", tags=["health"])
    async def api_health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/api/health/db", tags=["health"])
    @app.get("/health/db", tags=["health"])
    async def health_db() -> dict[str, str]:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "ok", "database": "postgres"}
        except Exception:
            return {"status": "error", "database": "postgres", "detail": "Database connection unavailable"}

    return app


app = create_app()
