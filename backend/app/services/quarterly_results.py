"""Read imported quarterly evidence; never substitute refresh times for filing dates."""
from collections import defaultdict
from datetime import UTC, datetime
from math import isfinite
from urllib.parse import quote

from sqlalchemy import select

from app.models.financials import Financials
from app.models.stock import Stock
from app.services.screener.metrics import VALIDATION_VERSION
from app.services.screener.query_builder import market_expression


def metric(record, key):
    metadata = record.provenance or {}
    if key in ("sales", "net_profit"):
        details = metadata.get({"sales": "revenue", "net_profit": "net_income"}[key], {})
        value = getattr(record, key)
    else:
        details = metadata.get("result_metrics", {}).get(key, {})
        value = details.get("value")
    valid = (record.currency and details.get("source_record") and details.get("currency") == record.currency
             and details.get("period_end") == record.period_end.isoformat()
             and details.get("validation_status") in ("provider", "recomputed", "normalized")
             and isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value))
    return {"value": value if valid else None, "source_field": details.get("source_record"), "currency": record.currency}


def growth(current, previous):
    if previous is None or current["value"] is None or previous["value"] is None:
        return {"value": None, "reason": "Comparable figure unavailable"}
    if current["currency"] != previous["currency"] or current["source_field"] != previous["source_field"]:
        return {"value": None, "reason": "Currency or source-field basis differs"}
    if previous["value"] <= 0:
        return {"value": None, "reason": "Prior figure is zero or negative; percentage growth is not meaningful"}
    value = (current["value"] / previous["value"] - 1) * 100
    return {"value": round(value, 2) if isfinite(value) else None, "reason": None if isfinite(value) else "Growth unavailable"}


def format_result(stock, current, history):
    def comparable(low, high, target):
        candidates = [row for row in history if low <= (current.period_end - row.period_end).days <= high]
        return min(candidates, key=lambda row: abs((current.period_end - row.period_end).days - target), default=None)
    previous, last_year = comparable(75, 105, 91), comparable(330, 400, 365)
    metrics = {}
    for key in ("sales", "ebitda", "net_profit", "eps"):
        value = metric(current, key)
        metrics[key] = {**value, "yoy": growth(value, metric(last_year, key) if last_year else None), "qoq": growth(value, metric(previous, key) if previous else None)}
    return {
        "symbol": stock.symbol, "name": stock.name, "exchange": stock.exchange,
        "industry": stock.industry, "sector": stock.sector, "currency": current.currency,
        "quarter_end": current.period_end.isoformat(), "announcement_date": None,
        "retrieved_at": current.updated_at.isoformat() if current.updated_at else None,
        "previous_quarter_end": previous.period_end.isoformat() if previous else None,
        "previous_year_end": last_year.period_end.isoformat() if last_year else None,
        "metrics": metrics, "source_url": f"https://finance.yahoo.com/quote/{quote(stock.symbol, safe='.-')}/financials/",
        "history": [{"quarter_end": row.period_end.isoformat(), "currency": row.currency,
                     **{key: metric(row, key)["value"] for key in metrics}}
                    for row in history if row.period_end <= current.period_end][:8],
    }


async def list_results(session, *, market="IN", quarter=None, industry=None, q="", sort="latest", page=1, page_size=12):
    today = datetime.now(UTC).date()
    statement = select(Stock, Financials).join(Financials, Financials.stock_id == Stock.id).where(
        Financials.period_type == "quarterly", Financials.validation_version == VALIDATION_VERSION,
        Financials.period_end.is_not(None), Financials.period_end <= today,
    )
    if market != "ALL":
        statement = statement.where(market_expression() == market)
    statement = statement.order_by(Stock.symbol, Financials.period_end.desc(), Financials.updated_at.desc(), Financials.id.desc())
    # ponytail: group imported quarterly histories in memory; move filtering/pagination
    # into SQL if the curated universe grows to thousands of companies.
    histories, companies = defaultdict(list), {}
    for stock, record in (await session.execute(statement)).all():
        companies[stock.id] = stock
        if not histories[stock.id] or histories[stock.id][-1].period_end != record.period_end:
            histories[stock.id].append(record)
    quarters = sorted({row.period_end.isoformat() for rows in histories.values() for row in rows}, reverse=True)
    industries = sorted({stock.industry for stock in companies.values() if stock.industry})
    items = []
    for stock_id, history in histories.items():
        stock = companies[stock_id]
        if industry and stock.industry != industry:
            continue
        if q and q.casefold() not in f"{stock.name} {stock.symbol}".casefold():
            continue
        selected = next((row for row in history if quarter is None or row.period_end == quarter), None)
        if selected and any(metric(selected, key)["value"] is not None for key in ("sales", "net_profit", "ebitda", "eps")):
            items.append(format_result(stock, selected, history))
    items.sort(key=lambda item: (item["name"].casefold(), item["symbol"]))
    if sort == "latest":
        items.sort(key=lambda item: item["quarter_end"], reverse=True)
    elif sort in ("sales_growth", "profit_growth"):
        key = "sales" if sort == "sales_growth" else "net_profit"
        items.sort(key=lambda item: (item["metrics"][key]["yoy"]["value"] is None, -(item["metrics"][key]["yoy"]["value"] or 0)))
    observed = [row.updated_at for rows in histories.values() for row in rows if row.updated_at]
    return {
        "items": items[(page - 1) * page_size:page * page_size], "total": len(items),
        "page": page, "page_size": page_size, "quarters": quarters, "industries": industries,
        "universe_count": len(companies), "updated_at": max(observed).isoformat() if observed else None,
        "growing_sales": sum(item["metrics"]["sales"]["yoy"]["value"] is not None and item["metrics"]["sales"]["yoy"]["value"] > 0 for item in items),
        "growing_profit": sum(item["metrics"]["net_profit"]["yoy"]["value"] is not None and item["metrics"]["net_profit"]["yoy"]["value"] > 0 for item in items),
        "date_basis": "Fiscal quarter end, not announcement date",
        "source": "Yahoo Finance/yfinance",
    }
