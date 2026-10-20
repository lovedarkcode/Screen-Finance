"""Deterministic comparisons and allowed research claims from stored facts."""
from decimal import Decimal


def comparison_period(current, history, *, yearly):
    quarter = int(current.quarter_period[1])
    year = current.fiscal_year - 1 if yearly or quarter == 1 else current.fiscal_year
    period = current.quarter_period if yearly else f"Q{quarter - 1 if quarter > 1 else 4}"
    low, high = (330, 400) if yearly else (75, 105)
    return next((row for row in history if row.fiscal_year == year and row.quarter_period == period
                 and getattr(row, "provider", None) == getattr(current, "provider", None)
                 and getattr(row, "period_basis", None) == getattr(current, "period_basis", None)
                 and low <= (current.period_end - row.period_end).days <= high), None)


def change(current, previous, field):
    value = getattr(current, field)
    if previous is None or value is None or getattr(previous, field) is None:
        return {"value": None, "reason": "Comparable figure unavailable"}
    if current.currency != previous.currency or field == "eps" and current.eps_basis != previous.eps_basis:
        return {"value": None, "reason": "Currency or EPS basis differs"}
    old = getattr(previous, field)
    if field == "operating_margin":
        return {"value": (value - old).quantize(Decimal("0.01")), "reason": None}
    if old <= 0:
        return {"value": None, "reason": "Prior figure is zero or negative"}
    return {"value": ((value / old - 1) * 100).quantize(Decimal("0.01")), "reason": None}


def comparisons(current, history):
    yearly = comparison_period(current, history, yearly=True)
    preceding = comparison_period(current, history, yearly=False)
    return {
        "year_ago_period_end": yearly.period_end if yearly else None,
        "preceding_period_end": preceding.period_end if preceding else None,
        "metrics": {field: {"value": getattr(current, field), "unit": "percentage_points" if field == "operating_margin" else "percent",
                            "yoy": change(current, yearly, field), "qoq": change(current, preceding, field)}
                    for field in ("revenue", "net_income", "eps", "operating_margin")},
    }


def findings(current, history):
    data = comparisons(current, history)
    result = {}

    def add(key, section, text):
        result[key] = {"id": key, "section": section, "text": text}

    def amount(value):
        return f"{current.currency} {value:,.2f}" if value is not None else "unavailable"

    add("S_METRICS", "executive_summary", f"For FY{current.fiscal_year} {current.quarter_period}, revenue was {amount(current.revenue)} and net income was {amount(current.net_income)}.")
    margin = f"{current.operating_margin:.2f}%" if current.operating_margin is not None else "unavailable"
    add("S_MARGIN_EPS", "executive_summary", f"Operating margin was {margin} and {current.eps_basis or 'reported'} EPS was {amount(current.eps)} per share.")
    for field, label in (("revenue", "revenue"), ("net_income", "net income"), ("eps", "EPS"), ("operating_margin", "operating margin")):
        delta = data["metrics"][field]["yoy"]["value"]
        if delta is None or delta == 0:
            continue
        unit = "percentage points" if field == "operating_margin" else "%"
        text = f"Year-on-year {label} {'increased' if delta > 0 else 'decreased'} by {abs(delta):.2f}{' ' if field == 'operating_margin' else ''}{unit}."
        section = "positive_triggers" if delta > 0 else "red_flags"
        add(f"{'P' if delta > 0 else 'R'}_{field.upper()}_YOY", section, text)
        add(f"S_{field.upper()}_YOY", "executive_summary", text)
    if current.net_income is not None and current.net_income < 0:
        add("R_NET_LOSS", "red_flags", f"The company reported a quarterly net loss of {amount(abs(current.net_income))}.")
    previous = comparison_period(current, history, yearly=False)
    if previous and previous.currency == current.currency and all(value is not None for value in (current.revenue, current.net_income, previous.revenue, previous.net_income)):
        if current.revenue > previous.revenue and current.net_income < previous.net_income:
            add("R_SEQUENTIAL_DIVERGENCE", "red_flags", "Sequential net income declined despite revenue growth compared with the preceding fiscal quarter.")
        if previous.net_income < 0 < current.net_income:
            add("P_RETURN_TO_PROFIT", "positive_triggers", "The company returned to a net profit after reporting a loss in the preceding fiscal quarter.")
    return result, data
