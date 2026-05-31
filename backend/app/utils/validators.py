"""Input validators."""
from __future__ import annotations

import re

SYMBOL_RE = re.compile(r"^[A-Z0-9\.\-]{1,15}$")


def is_valid_symbol(symbol: str) -> bool:
    return bool(SYMBOL_RE.match(symbol or ""))


def normalize_symbol(symbol: str) -> str:
    return (symbol or "").strip().upper()
