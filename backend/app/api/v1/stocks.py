"""Live Indian stock data endpoints for NSE/BSE listed companies."""
from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/stocks", tags=["stocks"])

YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_SUMMARY_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
INDIAN_SUFFIXES = (".NS", ".BO")
PERIODS = {
    "1M": "1mo",
    "6M": "6mo",
    "1Yr": "1y",
    "3Yr": "3y",
    "5Yr": "5y",
    "10Yr": "10y",
    "Max": "max",
}


def _normalize_symbol(symbol: str) -> str:
    clean = quote(symbol.strip().upper(), safe=".^-")
    if not clean:
        raise HTTPException(status_code=400, detail="Symbol is required")
    return clean


def _exchange(symbol: str) -> str:
    if symbol.endswith(".NS"):
        return "NSE"
    if symbol.endswith(".BO"):
        return "BSE"
    return "India"


def _is_indian_equity(symbol: str) -> bool:
    return symbol.upper().endswith(INDIAN_SUFFIXES) or symbol.upper().startswith("^")



def _number(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("raw")
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) else None


def _fmt(value: Any, decimals: int = 2) -> str:
    if isinstance(value, dict) and value.get("fmt"):
        return str(value["fmt"])
    number = _number(value)
    if number is None:
        return "N/A"
    return f"{number:,.{decimals}f}".rstrip("0").rstrip(".")


def _fmt_inr(value: Any) -> str:
    number = _number(value)
    return "N/A" if number is None else f"INR {_fmt(number)}"


def _fmt_crore(value: Any) -> str:
    number = _number(value)
    return "N/A" if number is None else f"INR {_fmt(number / 10_000_000)} Cr."


def _fmt_percent(value: Any, ratio: bool = False) -> str:
    number = _number(value)
    if number is None:
        return "N/A"
    if ratio:
        number *= 100
    return f"{number:.2f} %"


async def _get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=12.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def _quote(symbol: str) -> dict[str, Any]:
    data = await _get_json(
        YAHOO_CHART_URL.format(symbol=symbol),
        {"range": "5d", "interval": "1d", "includePrePost": "false"},
    )
    result = data.get("chart", {}).get("result", [])
    if not result:
        raise HTTPException(status_code=404, detail=f"Live quote not found for {symbol}")
    item = result[0].get("meta", {})
    price = _number(item.get("regularMarketPrice"))
    previous = _number(item.get("chartPreviousClose") or item.get("previousClose"))
    change = None
    change_percent = None
    if change is None and price is not None and previous not in (None, 0):
        change = price - previous
    if change_percent is None and change is not None and previous not in (None, 0):
        change_percent = (change / previous) * 100

    return {
        "symbol": symbol,
        "baseSymbol": symbol.rsplit(".", 1)[0],
        "name": item.get("longName") or item.get("shortName") or symbol,
        "price": price,
        "change": change,
        "changePercent": change_percent,
        "date": datetime.now(UTC).isoformat(),
        "marketStatus": item.get("marketState") or "Live/Delayed",
        "exchange": _exchange(symbol),
        "country": "India",
        "currency": item.get("currency") or "INR",
        "currencySymbol": "INR",
        "sector": "N/A",
        "industry": "N/A",
    }


async def _summary(symbol: str, modules: list[str]) -> dict[str, Any]:
    try:
        data = await _get_json(YAHOO_SUMMARY_URL.format(symbol=symbol), {"modules": ",".join(modules)})
        result = data.get("quoteSummary", {}).get("result")
    except Exception:
        return {}
    if not result:
        return {}
    return result[0]


@router.get("")
async def list_stocks(q: str | None = None, limit: int = 10) -> dict[str, Any]:
    if not q or len(q.strip()) < 2:
        return {"items": [], "total": 0}

    params = {
        "q": q.strip(),
        "quotesCount": max(limit * 3, 10),
        "newsCount": 0,
        "enableFuzzyQuery": "true",
        "quotesQueryId": "tss_match_phrase_query",
    }
    try:
        data = await _get_json(YAHOO_SEARCH_URL, params)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not search live NSE/BSE data") from exc

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for quote_item in data.get("quotes", []):
        symbol = str(quote_item.get("symbol") or "").upper()
        if not _is_indian_equity(symbol) or symbol in seen:
            continue
        seen.add(symbol)
        items.append(
            {
                "symbol": symbol,
                "baseSymbol": symbol.rsplit(".", 1)[0],
                "name": quote_item.get("longname") or quote_item.get("shortname") or symbol,
                "exchange": _exchange(symbol),
                "country": "India",
                "currency": "INR",
                "currencySymbol": "INR",
                "sector": quote_item.get("sector") or "Listed equity",
            }
        )
        if len(items) >= limit:
            break

    return {"items": items, "total": len(items)}


@router.get("/{symbol}")
async def get_stock(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    if not _is_indian_equity(normalized):
        raise HTTPException(status_code=400, detail="Use an NSE/BSE Yahoo symbol such as TCS.NS or TCS.BO")
    try:
        return await _quote(normalized)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load live quote for {symbol}") from exc


@router.get("/{symbol}/metrics")
async def get_metrics(symbol: str) -> list[dict[str, str]]:
    normalized = _normalize_symbol(symbol)
    try:
        quote_data = await _quote(normalized)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load metrics for {symbol}") from exc
    summary = await _summary(
        normalized,
        ["price", "summaryDetail", "defaultKeyStatistics", "financialData"],
    )

    price = summary.get("price", {})
    detail = summary.get("summaryDetail", {})
    stats = summary.get("defaultKeyStatistics", {})
    financial = summary.get("financialData", {})
    high = detail.get("dayHigh") or detail.get("fiftyTwoWeekHigh")
    low = detail.get("dayLow") or detail.get("fiftyTwoWeekLow")

    return [
        {"label": "Market Cap", "value": _fmt_crore(price.get("marketCap") or detail.get("marketCap"))},
        {"label": "Current Price", "value": _fmt_inr(quote_data.get("price"))},
        {"label": "High / Low", "value": f"{_fmt_inr(high)} / {_fmt_inr(low)}"},
        {"label": "Stock P/E", "value": _fmt(detail.get("trailingPE"))},
        {"label": "Book Value", "value": _fmt_inr(stats.get("bookValue"))},
        {"label": "Dividend Yield", "value": _fmt_percent(detail.get("dividendYield"), ratio=True)},
        {"label": "ROE", "value": _fmt_percent(financial.get("returnOnEquity"), ratio=True)},
        {"label": "EPS", "value": _fmt_inr(stats.get("trailingEps"))},
        {"label": "Price to book value", "value": _fmt(stats.get("priceToBook"))},
        {"label": "Debt to equity", "value": _fmt(financial.get("debtToEquity"))},
        {"label": "Revenue", "value": _fmt_crore(financial.get("totalRevenue"))},
        {"label": "Operating Margin", "value": _fmt_percent(financial.get("operatingMargins"), ratio=True)},
    ]


@router.get("/{symbol}/chart")
async def get_chart(symbol: str, range: str = "1Yr") -> list[dict[str, Any]]:
    normalized = _normalize_symbol(symbol)
    period = PERIODS.get(range, "1y")
    try:
        data = await _get_json(
            YAHOO_CHART_URL.format(symbol=normalized),
            {"range": period, "interval": "1d", "includePrePost": "false"},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load chart for {symbol}") from exc

    result = (data.get("chart", {}).get("result") or [{}])[0]
    timestamps = result.get("timestamp") or []
    quote_data = (result.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote_data.get("close") or []
    volumes = quote_data.get("volume") or []

    rows = []
    for timestamp, close, volume in list(zip(timestamps, closes, volumes))[-180:]:
        rows.append(
            {
                "month": datetime.fromtimestamp(timestamp, UTC).strftime("%d %b %Y"),
                "price": _number(close),
                "volume": int(volume or 0),
            }
        )
    return rows


def _statement_table(
    statement_items: list[dict[str, Any]],
    title: str,
    rows: list[tuple[str, str]],
) -> dict[str, Any]:
    columns = []
    for item in statement_items[:4]:
        end_date = item.get("endDate", {}).get("raw")
        columns.append(datetime.fromtimestamp(end_date, UTC).strftime("%b %Y") if end_date else "Period")

    table_rows = []
    for label, key in rows:
        values = [_fmt_crore(item.get(key)) for item in statement_items[:4]]
        if any(value != "N/A" for value in values):
            table_rows.append({"label": label, "values": values})

    return {"title": title, "unit": "Figures in INR Crore", "columns": columns, "rows": table_rows}


@router.get("/{symbol}/quarters")
async def get_quarters(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    summary = await _summary(normalized, ["incomeStatementHistoryQuarterly"])
    items = summary.get("incomeStatementHistoryQuarterly", {}).get("incomeStatementHistory", [])
    return _statement_table(
        items,
        "Quarterly Results",
        [
            ("Revenue", "totalRevenue"),
            ("Total Expenses", "totalOperatingExpenses"),
            ("Operating Income", "operatingIncome"),
            ("Net Profit", "netIncome"),
        ],
    )


@router.get("/{symbol}/profit-loss")
async def get_profit_loss(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    summary = await _summary(normalized, ["incomeStatementHistory"])
    items = summary.get("incomeStatementHistory", {}).get("incomeStatementHistory", [])
    return _statement_table(
        items,
        "Profit & Loss",
        [
            ("Revenue", "totalRevenue"),
            ("Total Expenses", "totalOperatingExpenses"),
            ("Operating Income", "operatingIncome"),
            ("Net Profit", "netIncome"),
        ],
    )


@router.get("/{symbol}/balance-sheet")
async def get_balance_sheet(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    summary = await _summary(normalized, ["balanceSheetHistory"])
    items = summary.get("balanceSheetHistory", {}).get("balanceSheetStatements", [])
    return _statement_table(
        items,
        "Balance Sheet",
        [
            ("Total Assets", "totalAssets"),
            ("Total Liabilities", "totalLiab"),
            ("Shareholders Equity", "totalStockholderEquity"),
            ("Cash", "cash"),
            ("Total Debt", "shortLongTermDebtTotal"),
        ],
    )


@router.get("/{symbol}/cash-flow")
async def get_cash_flow(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    summary = await _summary(normalized, ["cashflowStatementHistory"])
    items = summary.get("cashflowStatementHistory", {}).get("cashflowStatements", [])
    return _statement_table(
        items,
        "Cash Flow",
        [
            ("Operating Cash Flow", "totalCashFromOperatingActivities"),
            ("Investing Cash Flow", "totalCashflowsFromInvestingActivities"),
            ("Financing Cash Flow", "totalCashFromFinancingActivities"),
            ("Capital Expenditure", "capitalExpenditures"),
        ],
    )


@router.get("/{symbol}/ratios")
async def get_ratios(symbol: str) -> dict[str, Any]:
    metrics = await get_metrics(symbol)
    rows = [{"label": item["label"], "values": [item["value"]]} for item in metrics]
    return {"title": "Ratios", "unit": "Live key metrics", "columns": ["Current"], "rows": rows}


@router.get("/{symbol}/about")
async def get_about(symbol: str) -> dict[str, str]:
    normalized = _normalize_symbol(symbol)
    summary = await _summary(normalized, ["assetProfile"])
    profile = summary.get("assetProfile", {})
    return {
        "description": profile.get("longBusinessSummary") or "Company profile is not available from the live data provider.",
        "founded": "N/A",
        "headquarters": ", ".join(part for part in [profile.get("city"), profile.get("state"), profile.get("country")] if part) or "N/A",
        "website": (profile.get("website") or "").replace("https://", "").replace("http://", "") or "N/A",
    }


@router.get("/{symbol}/summary")
async def get_summary(symbol: str) -> dict[str, Any]:
    quote_data = await get_stock(symbol)
    return {
        "summary": f"{quote_data['name']} is listed on {quote_data['exchange']}. Live quote and financial data are loaded from the market data provider when this page opens.",
        "keyPoints": [
            f"Symbol: {quote_data['symbol']}",
            f"Exchange: {quote_data['exchange']}",
            f"Currency: {quote_data['currency']}",
            "Review quarterly results, annual statements and cash flows before making decisions.",
        ],
    }


@router.get("/{symbol}/peers")
async def get_peers(symbol: str) -> list[dict[str, Any]]:
    normalized = _normalize_symbol(symbol)
    summary = await _summary(normalized, ["assetProfile"])
    sector = summary.get("assetProfile", {}).get("sector")
    if not sector or sector == "N/A":
        return []
    search = await list_stocks(sector, 6)
    return [item for item in search["items"] if item["symbol"] != normalized]
