"""Vercel ASGI entrypoint for the FastAPI backend."""
from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path

# Provider cookies/timezone caches must use the function's writable temp directory.
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "screen-finance-cache"))

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

