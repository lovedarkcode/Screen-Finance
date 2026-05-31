"""Re-export of `app.config.settings` for clean `from app.core.settings import settings` imports."""
from app.config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
