"""Refresh the existing tables from the same validated evidence as stock analysis."""
from datetime import UTC, datetime
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from fastapi.concurrency import run_in_threadpool
from app.db.session import SessionLocal
from app.models.financials import Financials
from app.models.stock import Stock
from app.services.ai.financial_evidence import assess_quality, build_evidence
from app.services.ai.stock_analysis_service import _load_financials, _resolve_quote
from app.services.screener.metrics import METRICS, VALIDATION_VERSION
from app.api.v1.stocks import _number

STARTER_SYMBOLS = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "JPM", "BE", "F", "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "MTARTECH.NS", "SBIN.NS", "BHARTIARTL.NS"]
LABELS = {"Market capitalization": ("market_cap", "snapshot"), "Trailing P/E": ("pe", "ttm"), "Trailing EPS": ("eps", "ttm"), "Return on equity (provider)": ("roe", "ttm"), "Annual return on equity": ("roe", "annual"), "Net profit margin": ("net_profit_margin", "annual"), "Quarterly net profit margin": ("net_profit_margin", "quarterly"), "TTM net profit margin": ("net_profit_margin", "ttm"), "TTM revenue": ("revenue", "ttm"), "TTM net income": ("net_income", "ttm"), "Operating margin": ("operating_margin", "annual"), "Annual revenue growth": ("revenue_growth", "annual"), "Free cash flow": ("free_cash_flow", "annual"), "Free cash flow margin": ("free_cash_flow_margin", "annual"), "Current ratio": ("current_ratio", "snapshot"), "Debt to equity": ("debt_to_equity", "snapshot"), "Net debt": ("net_debt", "snapshot")}
RAW_FIELDS = {"Total Revenue": "revenue", "Net Income": "net_income", "Operating Income": "operating_income", "Operating Cash Flow": "operating_cash_flow", "Total Debt": "total_debt"}


def normalize_rows(quote, snapshot, retrieved):
    evidence, _, sources, _, trends = build_evidence(quote, snapshot, retrieved)
    quality = assess_quality(evidence, trends, snapshot, retrieved)
    disputed = {key for issue in quality.issues if issue.code == "provider_earnings_conflict" for key in issue.evidenceIds}
    by_id = {item.id: item for item in evidence}
    trailing_eps = next((item.value for item in evidence if item.label == "Trailing EPS"), None)
    rows = {}
    def put(field, basis, item):
        if item.id in disputed:
            return
        if field == "pe" and (item.value <= 0 or trailing_eps is not None and trailing_eps <= 0):
            return  # P/E is unavailable for non-positive trailing earnings, not a cheap valuation.
        snapshot_key = f"{basis}:{item.periodEnd}" if basis in ("annual", "quarterly") else f"{basis}:latest"
        row = rows.setdefault(snapshot_key, {"period": str(item.periodEnd or "provider-latest"), "period_type": basis, "period_end": item.periodEnd, "snapshot_key": snapshot_key, "updated_at": retrieved, "validation_version": VALIDATION_VERSION, "currency": item.currency or snapshot["info"].get("financialCurrency"), "provenance": {}})
        if item.periodEnd and (not row["period_end"] or row["period_end"] < item.periodEnd):
            row["period_end"], row["period"] = item.periodEnd, str(item.periodEnd)
        if field != "market_cap":
            row[METRICS[field]["column"]] = item.value
        row["provenance"][field] = {"currency": item.currency, "period": item.period, "period_end": item.periodEnd.isoformat() if item.periodEnd else None, "updated_at": retrieved.isoformat(), "source": "Yahoo Finance/yfinance", "source_record": item.sourceField, "formula": item.formula, "validation_status": "recomputed" if item.kind == "calculated" else "normalized" if item.kind == "normalized" else "provider", "definition": METRICS[field]["definition"], "inputs": [{"label": by_id[key].label, "value": by_id[key].value, "period": by_id[key].period, "currency": by_id[key].currency} for key in item.inputs]}
    for item in evidence:
        if item.sourceField in RAW_FIELDS and item.periodType in ("annual", "quarterly", "instant"):
            field = RAW_FIELDS[item.sourceField]
            basis = "snapshot" if item.periodType == "instant" else item.periodType
            if basis in METRICS[field]["periods"]:
                put(field, basis, item)
        if item.label in LABELS:
            field, basis = LABELS[item.label]
            put(field, basis, item)
    for trend in trends:
        if trend.netMarginId:
            put("net_profit_margin", trend.periodType, by_id[trend.netMarginId])
    # A refresh clears previously available metrics that are now missing.
    for row in rows.values():
        for key, info in METRICS.items():
            if key != "market_cap":
                row.setdefault(info["column"], None)
    return list(rows.values())


async def sync_symbol(symbol):
    quote = await _resolve_quote(symbol)
    retrieved = datetime.now(UTC)
    snapshot = await run_in_threadpool(_load_financials, quote["symbol"])
    rows = normalize_rows(quote, snapshot, retrieved)
    if not rows:
        raise ValueError("No validated financial data was available")
    info = snapshot["info"]
    values = {"symbol": quote["symbol"], "name": quote["name"], "exchange": quote["exchange"], "country": "IN" if quote["exchange"] in ("NSE", "BSE") else "US", "currency": quote["currency"], "sector": info.get("sector"), "industry": info.get("industry"), "market_cap": _number(info.get("marketCap")), "last_price": quote.get("price"), "updated_at": retrieved}
    async with SessionLocal() as session:
        statement = insert(Stock).values(**values)
        stock_id = (await session.execute(statement.on_conflict_do_update(index_elements=[Stock.symbol], set_={key: value for key, value in values.items() if key != "symbol"}).returning(Stock.id))).scalar_one()
        present = {row["snapshot_key"] for row in rows}
        await session.execute(update(Financials).where(Financials.stock_id == stock_id, Financials.snapshot_key.in_({"ttm:latest", "snapshot:latest"} - present)).values(validation_version=None))
        for row in rows:
            statement = insert(Financials).values(stock_id=stock_id, **row)
            await session.execute(statement.on_conflict_do_update(constraint="uq_financial_snapshot", set_=row))
        await session.commit()
    return {"symbol": quote["symbol"], "snapshots": len(rows), "status": "synced"}
