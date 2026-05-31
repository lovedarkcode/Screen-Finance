"""Convenience entry point: `python main.py` runs uvicorn against app.main:app."""
import uvicorn

from app.main import app


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


__all__ = ["app"]
