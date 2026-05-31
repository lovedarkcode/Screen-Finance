"""Financial calculations."""
from __future__ import annotations


def pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current - previous) / previous * 100


def cagr(start: float, end: float, years: float) -> float | None:
    if start <= 0 or years <= 0:
        return None
    return ((end / start) ** (1 / years) - 1) * 100


def pe_ratio(price: float, eps: float) -> float | None:
    return price / eps if eps else None
