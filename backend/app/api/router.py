"""Top-level API router aggregating all v1 sub-routers."""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai,
    auth,
    news,
    portfolio,
    screener,
    stocks,
    watchlist,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(stocks.router)
api_router.include_router(ai.router)
api_router.include_router(screener.router)
api_router.include_router(portfolio.router)
api_router.include_router(watchlist.router)
api_router.include_router(news.router)
api_router.include_router(admin.router)
