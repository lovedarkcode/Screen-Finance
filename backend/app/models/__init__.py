"""ORM model registry — import all models so Alembic autogenerate can see them."""
from app.models.ai_logs import AILog
from app.models.financials import Financials
from app.models.news import News
from app.models.portfolio import Holding, Portfolio
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist

__all__ = [
    "User",
    "Stock",
    "Financials",
    "Portfolio",
    "Holding",
    "Watchlist",
    "AILog",
    "News",
]
