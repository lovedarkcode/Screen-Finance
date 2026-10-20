"""The company master reuses the existing stocks table and its foreign keys."""
from app.models.stock import Stock

Company = Stock

__all__ = ["Company"]
