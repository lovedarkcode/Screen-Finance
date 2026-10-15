"""Live Indian stock data endpoints for NSE/BSE listed companies."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import Any
from urllib.parse import quote

import httpx
import yfinance as yf
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool


router = APIRouter(prefix="/stocks", tags=["stocks"])

YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_SUMMARY_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
INDIAN_SUFFIXES = (".NS", ".BO")
PERIODS = {
    "1D": "1d",
    "1W": "5d",
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "3Y": "3y",
    "5Y": "5y",
    "10Y": "10y",
    "15Y": "max",
    "20Y": "max",
    "25Y": "max",
    "30Y": "max",
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
    closes = ((result[0].get("indicators", {}).get("quote") or [{}])[0].get("close") or [])
    previous = _number(item.get("previousClose"))
    if previous is None:
        previous = _number(closes[-2]) if len(closes) >= 2 else _number(item.get("chartPreviousClose"))
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
        "date": datetime.fromtimestamp(item["regularMarketTime"], UTC).isoformat() if item.get("regularMarketTime") else None,
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


SECTORS = {
    "defence": {
        "name": "Defence",
        "icon": "Shield",
        "description": "Defense aerospace, electronics, and naval shipbuilding enterprises of India.",
        "symbols": ["HAL.NS", "BEL.NS", "MAZDOCK.NS", "BDL.NS", "COCHINSHIP.NS"],
    },
    "railway": {
        "name": "Railway",
        "icon": "Train",
        "description": "Rail infrastructure, financing, and transport services.",
        "symbols": ["IRCTC.NS", "IRFC.NS", "RVNL.NS", "IRCON.NS", "CONCOR.NS"],
    },
    "energy": {
        "name": "Energy",
        "icon": "Zap",
        "description": "Oil, gas, power generation, transmission, and renewable energy.",
        "symbols": ["RELIANCE.NS", "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "TATAPOWER.NS", "ADANIGREEN.NS"],
    },
    "production": {
        "name": "Production & Metals",
        "icon": "Factory",
        "description": "Steel, aluminium, cement, and core industrial materials.",
        "symbols": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "GRASIM.NS", "JINDALSTEL.NS"],
    },
    "electronics": {
        "name": "Electronics",
        "icon": "Cpu",
        "description": "Electronics manufacturing, appliances, and hardware components.",
        "symbols": ["DIXON.NS", "SYRMA.NS", "KAYNES.NS", "VOLTAS.NS", "HAVELLS.NS"],
    },
    "it": {
        "name": "IT & Software",
        "icon": "Code",
        "description": "Global software services, consulting, and system integration.",
        "symbols": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"],
    },
    "banking": {
        "name": "Banking & Finance",
        "icon": "Building",
        "description": "Commercial banking, public sector banks, and retail credit providers.",
        "symbols": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS"],
    },
    "auto": {
        "name": "Automobile",
        "icon": "Car",
        "description": "Passenger vehicles, commercial vehicles, and two-wheeler giants.",
        "symbols": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS"],
    },
    "pharma": {
        "name": "Pharmaceuticals",
        "icon": "Pills",
        "description": "Drug formulations, APIs, diagnostics, and healthcare chains.",
        "symbols": ["SUNPHARMA.NS", "CIPLA.NS", "REDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    },
}


@router.get("/sectors")
async def list_sectors() -> list[dict]:
    return [
        {
            "id": sector_id,
            "name": data["name"],
            "icon": data["icon"],
            "description": data["description"],
            "tickerCount": len(data["symbols"]),
        }
        for sector_id, data in SECTORS.items()
    ]


@router.get("/sectors/{sector_id}")
async def get_sector_stocks(sector_id: str) -> list[dict]:
    sector = SECTORS.get(sector_id.lower())
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector '{sector_id}' not found")

    async def fetch_safe_quote(sym: str) -> dict:
        try:
            return await _quote(sym)
        except Exception:
            return {
                "symbol": sym,
                "baseSymbol": sym.rsplit(".", 1)[0],
                "name": sym.rsplit(".", 1)[0],
                "price": None,
                "change": None,
                "changePercent": None,
                "exchange": "NSE",
                "country": "India",
                "currency": "INR",
                "currencySymbol": "INR",
                "sector": sector["name"],
                "industry": "N/A",
                "error": True
            }

    tasks = [fetch_safe_quote(sym) for sym in sector["symbols"]]
    return await asyncio.gather(*tasks)


@router.get("/{symbol}")
async def get_stock(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    if not _is_indian_equity(normalized):
        raise HTTPException(status_code=400, detail="Use an NSE/BSE Yahoo symbol such as TCS.NS or TCS.BO")
    try:
        return await _quote(normalized)
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Stock not found: {symbol}") from exc
        raise HTTPException(status_code=502, detail="Market data provider unavailable") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load live quote for {symbol}") from exc


def _fetch_yfinance_ticker(symbol: str) -> yf.Ticker:
    ticker = yf.Ticker(symbol)
    try:
        # Trigger data fetch in this thread
        _ = ticker.info
    except Exception:
        pass
    return ticker


def _statement_table_from_df(
    df: Any,
    title: str,
    rows: list[tuple[str, str]],
    limit: int = 6,
) -> dict[str, Any]:
    if df is None or getattr(df, "empty", True):
        return {"title": title, "unit": "Figures in INR Crore", "columns": [], "rows": []}

    # Columns: datetimes from DataFrame columns (yfinance returns them newest first)
    col_dates = list(df.columns)[:limit][::-1]
    columns = []
    for col in col_dates:
        if hasattr(col, "strftime"):
            columns.append(col.strftime("%b %Y"))
        else:
            columns.append(str(col))

    table_rows = []
    for label, df_key in rows:
        values = []
        if df_key in df.index:
            row_data = df.loc[df_key]
            for col in col_dates:
                val = row_data.get(col)
                if val is None or (isinstance(val, float) and not isfinite(val)):
                    values.append("N/A")
                else:
                    values.append(_fmt_crore(val))
        else:
            values = ["N/A"] * len(col_dates)

        if any(value != "N/A" for value in values):
            table_rows.append({"label": label, "values": values})

    return {"title": title, "unit": "Figures in INR Crore", "columns": columns, "rows": table_rows}


@router.get("/{symbol}/metrics")
async def get_metrics(symbol: str) -> list[dict[str, str]]:
    normalized = _normalize_symbol(symbol)
    try:
        quote_data = await _quote(normalized)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load metrics for {symbol}") from exc

    try:
        ticker = await run_in_threadpool(_fetch_yfinance_ticker, normalized)
        info = ticker.info
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch data for {symbol}") from exc

    def fmt_div_yield(val: Any) -> str:
        if val is None:
            return "N/A"
        try:
            fval = float(val)
            if fval < 0.2:
                return _fmt_percent(fval, ratio=True)
            return _fmt_percent(fval, ratio=False)
        except Exception:
            return "N/A"

    return [
        {"label": "Market Cap", "value": _fmt_crore(info.get("marketCap"))},
        {"label": "Current Price", "value": _fmt_inr(quote_data.get("price"))},
        {"label": "High / Low", "value": f"{_fmt_inr(info.get('fiftyTwoWeekHigh') or info.get('dayHigh'))} / {_fmt_inr(info.get('fiftyTwoWeekLow') or info.get('dayLow'))}"},
        {"label": "Stock P/E", "value": _fmt(info.get("trailingPE"))},
        {"label": "Book Value", "value": _fmt_inr(info.get("bookValue"))},
        {"label": "Dividend Yield", "value": fmt_div_yield(info.get("dividendYield"))},
        {"label": "ROE", "value": _fmt_percent(info.get("returnOnEquity"), ratio=True)},
        {"label": "EPS", "value": _fmt_inr(info.get("trailingEps"))},
        {"label": "Price to book value", "value": _fmt(info.get("priceToBook"))},
        {"label": "Debt to equity", "value": _fmt(info.get("debtToEquity"))},
        {"label": "Revenue", "value": _fmt_crore(info.get("totalRevenue"))},
        {"label": "Operating Margin", "value": _fmt_percent(info.get("operatingMargins"), ratio=True)},
    ]


@router.get("/{symbol}/chart")
async def get_chart(symbol: str, range: str = "1Yr") -> list[dict[str, Any]]:
    normalized = _normalize_symbol(symbol)
    if range not in PERIODS:
        raise HTTPException(status_code=422, detail="Unsupported chart timeframe")
    period = PERIODS[range]
    interval = "1d"
    if range in ("5Yr", "10Yr", "Max", "5Y", "10Y"):
        interval = "1wk"
    elif range in ("15Y", "20Y", "25Y", "30Y"):
        interval = "1mo"
    elif range == "1D":
        interval = "1m"
    elif range == "1W":
        interval = "30m"
        
    try:
        data = await _get_json(
            YAHOO_CHART_URL.format(symbol=normalized),
            {"range": period, "interval": interval, "includePrePost": "false"},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load chart for {symbol}") from exc

    result = (data.get("chart", {}).get("result") or [{}])[0]
    timestamps = result.get("timestamp") or []
    quote_data = (result.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote_data.get("close") or []
    volumes = quote_data.get("volume") or []

    rows = []
    cutoff = (datetime.now(UTC) - timedelta(days=int(range[:-1]) * 365.25)).timestamp() if range in ("15Y", "20Y", "25Y", "30Y") else 0
    for index, timestamp in enumerate(timestamps):
        close = _number(closes[index]) if index < len(closes) else None
        volume = _number(volumes[index]) if index < len(volumes) else None
        if close is not None and timestamp >= cutoff:
            rows.append(
                {
                    "month": datetime.fromtimestamp(timestamp, UTC).strftime("%d %b %Y"),
                    "date": datetime.fromtimestamp(timestamp, UTC).isoformat(),
                    "timestamp": timestamp,
                    "price": close,
                    "volume": int(volume) if volume is not None and volume >= 0 else None,
                }
            )
    return rows


@router.get("/{symbol}/quarters")
async def get_quarters(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    try:
        ticker = await run_in_threadpool(_fetch_yfinance_ticker, normalized)
        df = ticker.quarterly_income_stmt
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load quarters for {symbol}") from exc
    return _statement_table_from_df(
        df,
        "Quarterly Results",
        [
            ("Revenue", "Total Revenue"),
            ("Total Expenses", "Total Expenses"),
            ("Operating Income", "Operating Income"),
            ("Net Profit", "Net Income"),
        ],
        limit=6,
    )


@router.get("/{symbol}/profit-loss")
async def get_profit_loss(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    try:
        ticker = await run_in_threadpool(_fetch_yfinance_ticker, normalized)
        df = ticker.income_stmt
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load profit & loss for {symbol}") from exc
    return _statement_table_from_df(
        df,
        "Profit & Loss",
        [
            ("Revenue", "Total Revenue"),
            ("Total Expenses", "Total Expenses"),
            ("Operating Income", "Operating Income"),
            ("Net Profit", "Net Income"),
        ],
        limit=6,
    )


@router.get("/{symbol}/balance-sheet")
async def get_balance_sheet(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    try:
        ticker = await run_in_threadpool(_fetch_yfinance_ticker, normalized)
        df = ticker.balance_sheet
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load balance sheet for {symbol}") from exc
    return _statement_table_from_df(
        df,
        "Balance Sheet",
        [
            ("Total Assets", "Total Assets"),
            ("Total Liabilities", "Total Liabilities Net Minority Interest"),
            ("Shareholders Equity", "Stockholders Equity"),
            ("Cash", "Cash And Cash Equivalents"),
            ("Total Debt", "Total Debt"),
        ],
        limit=6,
    )


@router.get("/{symbol}/cash-flow")
async def get_cash_flow(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    try:
        ticker = await run_in_threadpool(_fetch_yfinance_ticker, normalized)
        df = ticker.cashflow
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load cash flow for {symbol}") from exc
    return _statement_table_from_df(
        df,
        "Cash Flow",
        [
            ("Operating Cash Flow", "Operating Cash Flow"),
            ("Investing Cash Flow", "Investing Cash Flow"),
            ("Financing Cash Flow", "Financing Cash Flow"),
            ("Capital Expenditure", "Capital Expenditure"),
        ],
        limit=6,
    )


@router.get("/{symbol}/ratios")
async def get_ratios(symbol: str) -> dict[str, Any]:
    metrics = await get_metrics(symbol)
    rows = [{"label": item["label"], "values": [item["value"]]} for item in metrics]
    return {"title": "Ratios", "unit": "Live key metrics", "columns": ["Current"], "rows": rows}


@router.get("/{symbol}/about")
async def get_about(symbol: str) -> dict[str, str]:
    normalized = _normalize_symbol(symbol)
    try:
        ticker = await run_in_threadpool(_fetch_yfinance_ticker, normalized)
        info = ticker.info
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load details for {symbol}") from exc
    return {
        "description": info.get("longBusinessSummary") or "Company profile is not available from the live data provider.",
        # "founded": str(info.get("founded") or "N/A"),
        "headquarters": ", ".join(part for part in [info.get("city"), info.get("state"), info.get("country")] if part) or "N/A",
        "website": (info.get("website") or "").replace("https://", "").replace("http://", "") or "N/A",
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
    try:
        ticker = await run_in_threadpool(_fetch_yfinance_ticker, normalized)
        info = ticker.info
    except Exception:
        return []
    sector = info.get("sector")
    if not sector or sector == "N/A":
        return []
    search = await list_stocks(sector, 6)
    return [item for item in search["items"] if item["symbol"] != normalized]

