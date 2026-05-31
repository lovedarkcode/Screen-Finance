"""Number, currency, and percentage formatters."""
from __future__ import annotations


def format_currency(value: float, currency: str = "$", decimals: int = 2) -> str:
    return f"{currency}{value:,.{decimals}f}"


def format_large_number(value: float) -> str:
    abs_v = abs(value)
    for unit, suffix in [(1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if abs_v >= unit:
            return f"{value / unit:.2f}{suffix}"
    return f"{value:,.0f}"


def format_percent(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}%"
