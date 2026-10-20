"""Convenience entry point: `python main.py` runs uvicorn against app.main:app."""
import uvicorn

from app.main import app
from app.config import settings


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.ENVIRONMENT == "development")


__all__ = ["app"]
