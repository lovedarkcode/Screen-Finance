"""FastAPI application entry point."""
# Touch this file to force uvicorn --reload to re-import settings (which re-reads .env).
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.config import settings
from app.db.session import engine
from app.middleware import RequestContextMiddleware

logger = logging.getLogger("screen-finance")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Postgres connection OK (%s)", engine.url.render_as_string(hide_password=True))
    except Exception as exc:
        logger.warning("Postgres connection FAILED at startup: %s", exc)

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

    @app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        return {"status": "ok", "service": "screen-finance-backend"}

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/api/health", tags=["health"])
    async def api_health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/health/db", tags=["health"])
    async def health_db() -> dict[str, str]:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "ok", "database": "postgres"}
        except Exception as exc:
            return {"status": "error", "database": "postgres", "detail": str(exc)}

    return app


app = create_app()
