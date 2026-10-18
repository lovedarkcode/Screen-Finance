"""Live Indian and US stock quotes, history and company fundamentals."""
from __future__ import annotations

import asyncio
import re
from bisect import bisect_right
from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import Any
from urllib.parse import quote

import httpx
import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from app.dependencies import get_db
from app.models.financials import Financials
from app.models.stock import Stock
from fastapi.concurrency import run_in_threadpool


router = APIRouter(prefix="/stocks", tags=["stocks"])

YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_SUMMARY_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
INDIAN_SUFFIXES = (".NS", ".BO")
US_EXCHANGES = {
    "NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NAS": "NASDAQ",
    "NYQ": "NYSE", "NYS": "NYSE", "ASE": "NYSE American", "PCX": "NYSE Arca",
    "BTS": "Cboe", "BATS": "Cboe", "CXI": "Cboe", "NAE": "NYSE American",
    "PNK": "OTC", "OQB": "OTCQB", "OQX": "OTCQX", "OEM": "OTC",
    "SNP": "S&P", "DJI": "Dow Jones", "NIM": "NASDAQ",
}
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
    clean = symbol.strip().upper()
    # Yahoo uses a hyphen for US share classes (BRK.B -> BRK-B).
    if re.fullmatch(r"[A-Z]{1,5}\.[AB]", clean):
        clean = clean.replace(".", "-")
    if not re.fullmatch(r"\^?[A-Z0-9][A-Z0-9&.\-]{0,39}", clean):
        raise HTTPException(status_code=400, detail="Enter a valid stock symbol")
    if not (_is_indian_equity(clean) or clean.startswith("^") or re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)?", clean)):
        raise HTTPException(status_code=400, detail="Use an NSE/BSE or US stock symbol, such as TCS.NS or AAPL")
    return clean


def _exchange(symbol: str, metadata: dict | None = None) -> str:
    if symbol.endswith(".NS"):
        return "NSE"
    if symbol.endswith(".BO"):
        return "BSE"
    metadata = metadata or {}
    code = metadata.get("exchange") or metadata.get("exchangeName")
    return US_EXCHANGES.get(code) or {"NSI": "NSE", "BSE": "BSE", "BOM": "BSE"}.get(code) or metadata.get("exchDisp") or metadata.get("fullExchangeName") or "India"


def _is_indian_equity(symbol: str) -> bool:
    return symbol.upper().endswith(INDIAN_SUFFIXES) or symbol.upper() in {"^NSEI", "^NSEBANK", "^BSESN", "^CNXIT"}


def _market_metadata(symbol: str, metadata: dict) -> dict:
    code = metadata.get("exchange") or metadata.get("exchangeName")
    indian = _is_indian_equity(symbol) or code in {"NSI", "BSE", "BOM"}
    if not indian and code not in US_EXCHANGES:
        raise HTTPException(status_code=400, detail="Only Indian and US exchange listings are supported")
    currency = metadata.get("currency") or ("INR" if indian else "USD")
    return {
        "exchange": _exchange(symbol, metadata),
        "market": "IN" if indian else "US",
        "country": "India" if indian else "United States",
        "currency": currency,
        "currencySymbol": {"INR": "INR", "USD": "$"}.get(currency, currency),
        "timeZone": metadata.get("exchangeTimezoneName") or ("Asia/Kolkata" if indian else "America/New_York"),
    }


def _report_currency(ticker: Any, symbol: str) -> str:
    info = getattr(ticker, "info", None) or {}
    return info.get("financialCurrency") or info.get("currency") or ("INR" if _is_indian_equity(symbol) else "USD")



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


def _fmt_money(value: Any, currency: str = "INR") -> str:
    number = _number(value)
    return "N/A" if number is None else f"{currency} {_fmt(number)}"


def _fmt_large(value: Any, currency: str = "INR") -> str:
    number = _number(value)
    scale, unit = (10_000_000, "Cr.") if currency == "INR" else (1_000_000, "Million")
    return "N/A" if number is None else f"{currency} {_fmt(number / scale)} {unit}"


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
        YAHOO_CHART_URL.format(symbol=quote(symbol, safe=".^-")),
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
        "baseSymbol": symbol.rsplit(".", 1)[0] if symbol.endswith(INDIAN_SUFFIXES) else symbol,
        "name": item.get("longName") or item.get("shortName") or symbol,
        "price": price,
        "change": change,
        "changePercent": change_percent,
        "date": datetime.fromtimestamp(item["regularMarketTime"], UTC).isoformat() if item.get("regularMarketTime") else None,
        "marketStatus": item.get("marketState") or "Live/Delayed",
        **_market_metadata(symbol, item),
        "sector": "N/A",
        "industry": "N/A",
    }


async def _summary(symbol: str, modules: list[str]) -> dict[str, Any]:
    try:
        data = await _get_json(YAHOO_SUMMARY_URL.format(symbol=quote(symbol, safe=".^-")), {"modules": ",".join(modules)})
        result = data.get("quoteSummary", {}).get("result")
    except Exception:
        return {}
    if not result:
        return {}
    return result[0]


@router.get("")
async def list_stocks(q: str | None = None, limit: int = Query(default=10, ge=1, le=50)) -> dict[str, Any]:
    if not q or not q.strip():
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
        raise HTTPException(status_code=502, detail="Could not search Indian and US stocks") from exc

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for quote_item in data.get("quotes", []):
        symbol = str(quote_item.get("symbol") or "").upper()
        if not symbol or symbol in seen or quote_item.get("quoteType", "EQUITY") not in {"EQUITY", "INDEX"}:
            continue
        try:
            metadata = _market_metadata(symbol, quote_item)
        except HTTPException:
            continue
        seen.add(symbol)
        items.append(
            {
                "symbol": symbol,
                "baseSymbol": symbol.rsplit(".", 1)[0] if symbol.endswith(INDIAN_SUFFIXES) else symbol,
                "name": quote_item.get("longname") or quote_item.get("shortname") or symbol,
                **metadata,
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

# A same-market sector sample, matching the Indian peer-pool approach above.
US_PEERS = {
    "technology": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL"],
    "financial services": ["JPM", "BAC", "WFC", "GS", "MS"],
    "healthcare": ["JNJ", "LLY", "ABBV", "MRK", "UNH"],
    "energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "consumer cyclical": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
    "consumer defensive": ["WMT", "COST", "PG", "KO", "PEP"],
    "communication services": ["GOOGL", "META", "NFLX", "DIS", "T"],
    "industrials": ["CAT", "GE", "HON", "UPS", "DE"],
    "basic materials": ["LIN", "APD", "FCX", "NEM", "DOW"],
    "utilities": ["NEE", "DUK", "SO", "AEP", "EXC"],
    "real estate": ["PLD", "AMT", "EQIX", "O", "SPG"],
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


def _overview_metrics(info: dict, history: Any, currency: str = "INR") -> list[dict]:
    high = low = None
    if history is not None and not history.empty:
        high, low = _number(history["High"].max()), _number(history["Low"].min())
    debt = _number(info.get("debtToEquity"))
    roe = _number(info.get("returnOnEquity"))
    margin = _number(info.get("operatingMargins"))
    fields = [
        ("marketCap", "Market Cap", info.get("marketCap"), "crore"),
        ("peRatio", "P/E Ratio", info.get("trailingPE"), "number"),
        ("eps", "EPS", info.get("trailingEps"), "inr"),
        ("faceValue", "Face Value", info.get("faceValue"), "inr"),
        ("allTimeHigh", "All Time High", high, "inr"),
        ("allTimeLow", "All Time Low", low, "inr"),
        ("debtToEquity", "Debt/Equity", debt / 100 if debt is not None else None, "number"),
        ("bookValue", "Book Value", info.get("bookValue"), "inr"),
        ("roe", "Return on Equity", roe * 100 if roe is not None else None, "percent"),
        ("operatingMargin", "Operating Margin", margin * 100 if margin is not None else None, "percent"),
        ("revenue", "Revenue", info.get("totalRevenue"), "crore"),
        ("priceToBook", "Price to Book", info.get("priceToBook"), "number"),
    ]
    metrics = []
    for key, label, value, unit in fields:
        item_currency = (info.get("financialCurrency") or currency) if key == "revenue" else currency
        if unit in {"inr", "crore"} and item_currency != "INR":
            unit = "currency" if unit == "inr" else "compact"
        metrics.append({"id": key, "label": label, "value": _number(value), "unit": unit, "currency": item_currency if unit in {"inr", "crore", "currency", "compact"} else None})
    return metrics


def _history_returns(history: Any) -> list[dict]:
    result = []
    for label, days in [("1 Week", 7), ("1 Month", 30), ("3 Months", 90), ("6 Months", 182), ("1 Year", 365), ("3 Years", 1096), ("5 Years", 1826)]:
        value = None
        if history is not None and not history.empty:
            closes = history["Close"].dropna()
            if not closes.empty:
                earlier = closes.loc[closes.index <= closes.index[-1] - timedelta(days=days)]
                if not earlier.empty and earlier.iloc[-1] > 0:
                    value = _number((closes.iloc[-1] / earlier.iloc[-1] - 1) * 100)
        result.append({"label": label, "value": value})
    return result


def _load_overview(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    try:
        history = ticker.history(period="max", auto_adjust=True)
    except Exception:
        history = None
    ceo = next((officer.get("name") for officer in info.get("companyOfficers", []) if "ceo" in officer.get("title", "").lower() or "chief executive" in officer.get("title", "").lower()), None)
    currency = info.get("currency") or ("INR" if _is_indian_equity(symbol) else "USD")
    metrics = _overview_metrics(info, history, currency)
    raw = {item["id"]: item["value"] for item in metrics}
    highlights = []
    if raw["roe"] is not None:
        highlights.append(f"Return on equity is {raw['roe']:.2f}% based on the latest available financial data.")
    if raw["debtToEquity"] is not None:
        highlights.append(f"Debt to equity is {raw['debtToEquity']:.2f} times.")
    if raw["operatingMargin"] is not None:
        highlights.append(f"Operating margin is {raw['operatingMargin']:.2f}%.")
    return {
        "metrics": metrics,
        "currency": currency,
        "financialCurrency": info.get("financialCurrency") or currency,
        "priceRange": {"dayLow": _number(info.get("dayLow")), "dayHigh": _number(info.get("dayHigh")), "week52Low": _number(info.get("fiftyTwoWeekLow")), "week52High": _number(info.get("fiftyTwoWeekHigh")), "open": _number(info.get("open")), "previousClose": _number(info.get("previousClose")), "volume": _number(info.get("volume")), "vwap": None},
        "returns": _history_returns(history),
        "about": {"description": info.get("longBusinessSummary"), "sector": info.get("sector"), "industry": info.get("industry"), "headquarters": ", ".join(str(info[key]) for key in ("city", "state") if info.get(key)), "founded": info.get("founded"), "ceo": ceo, "website": info.get("website")},
        "insights": highlights,
        "source": "Yahoo Finance / yfinance",
        "historyAsOf": history.index[-1].isoformat() if history is not None and not history.empty else None,
    }


@router.get("/{symbol}/overview")
async def get_overview(symbol: str) -> dict:
    normalized = _normalize_symbol(symbol)
    try:
        return await run_in_threadpool(_load_overview, normalized)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Company fundamentals temporarily unavailable") from exc


def _statement_table_from_df(
    df: Any,
    title: str,
    rows: list[tuple[str, str]],
    limit: int = 6,
    currency: str = "INR",
) -> dict[str, Any]:
    unit = f"Figures in {currency} {'Crore' if currency == 'INR' else 'Millions'}"
    if df is None or getattr(df, "empty", True):
        return {"title": title, "unit": unit, "currency": currency, "columns": [], "rows": []}

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
                    values.append(_fmt_large(val, currency))
        else:
            values = ["N/A"] * len(col_dates)

        if any(value != "N/A" for value in values):
            table_rows.append({"label": label, "values": values})

    return {"title": title, "unit": unit, "currency": currency, "columns": columns, "rows": table_rows}


def _quarterly_chart(df: Any, currency: str = "INR") -> list[dict]:
    if df is None or df.empty:
        return []
    result = []
    scale = 100_000 if currency == "INR" else 1_000_000
    for date in list(df.columns)[:5]:
        def cell(key: str) -> float | None:
            return _number(df.loc[key, date]) if key in df.index else None
        revenue = cell("Total Revenue")
        result.append({"date": date.strftime("%d %b %Y"), "totalIncome": revenue / scale if revenue is not None else None, "profitBeforeTax": cell("Pretax Income") / scale if cell("Pretax Income") is not None else None, "netProfitLoss": cell("Net Income") / scale if cell("Net Income") is not None else None, "eps": cell("Diluted EPS") if cell("Diluted EPS") is not None else cell("Basic EPS")})
    return result


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

    currency = quote_data["currency"]
    report_currency = _report_currency(ticker, normalized)

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
        {"label": "Market Cap", "value": _fmt_large(info.get("marketCap"), currency)},
        {"label": "Current Price", "value": _fmt_money(quote_data.get("price"), currency)},
        {"label": "High / Low", "value": f"{_fmt_money(info.get('fiftyTwoWeekHigh') or info.get('dayHigh'), currency)} / {_fmt_money(info.get('fiftyTwoWeekLow') or info.get('dayLow'), currency)}"},
        {"label": "Stock P/E", "value": _fmt(info.get("trailingPE"))},
        {"label": "Book Value", "value": _fmt_money(info.get("bookValue"), currency)},
        {"label": "Dividend Yield", "value": fmt_div_yield(info.get("dividendYield"))},
        {"label": "ROE", "value": _fmt_percent(info.get("returnOnEquity"), ratio=True)},
        {"label": "EPS", "value": _fmt_money(info.get("trailingEps"), currency)},
        {"label": "Price to book value", "value": _fmt(info.get("priceToBook"))},
        {"label": "Debt to equity", "value": _fmt(_number(info.get("debtToEquity")) / 100 if _number(info.get("debtToEquity")) is not None else None)},
        {"label": "Revenue", "value": _fmt_large(info.get("totalRevenue"), report_currency)},
        {"label": "Operating Margin", "value": _fmt_percent(info.get("operatingMargins"), ratio=True)},
    ]


@router.get("/{symbol}/chart")
async def get_chart(symbol: str, range: str = "1Yr", indicators: bool = False) -> list[dict[str, Any]]:
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
    if indicators and interval in ("1wk", "1mo"):
        interval = "1d"
    params = {"range": period, "interval": interval, "includePrePost": "false"}
    if range in ("3Y", "3Yr"):
        # Yahoo's range enum does not include three years.
        now = datetime.now(UTC)
        params = {"period1": int((now - timedelta(days=3 * 365.25)).timestamp()),
                  "period2": int(now.timestamp()), "interval": interval, "includePrePost": "false"}
        
    try:
        data = await _get_json(
            YAHOO_CHART_URL.format(symbol=quote(normalized, safe=".^-")),
            params,
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
    if indicators and rows:
        try:
            history = await _get_json(
                YAHOO_CHART_URL.format(symbol=quote(normalized, safe=".^-")),
                {"period1": int(rows[0]["timestamp"] - 365 * 86400),
                 "period2": int(datetime.now(UTC).timestamp()), "interval": "1d", "includePrePost": "false"},
            )
            daily = (history.get("chart", {}).get("result") or [{}])[0]
            daily_closes = (daily.get("indicators", {}).get("quote") or [{}])[0].get("close") or []
            samples = sorted((stamp, close) for stamp, raw in zip(daily.get("timestamp") or [], daily_closes)
                             if (close := _number(raw)) is not None)
            stamps = [stamp for stamp, _ in samples]
            prefix = [0.0]
            for _, close in samples:
                prefix.append(prefix[-1] + close)
            for row in rows:
                # Intraday overlays use completed prior sessions, never today's future close.
                cutoff = row["timestamp"] if interval == "1d" else row["timestamp"] // 86400 * 86400 - 1
                end = bisect_right(stamps, cutoff)
                for window in (50, 100):
                    row[f"dma{window}"] = (prefix[end] - prefix[end - window]) / window if end >= window else None
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            # Keep price history usable if the supplemental daily feed is unavailable.
            pass
    return rows


@router.get("/{symbol}/pe-history")
async def get_pe_history(symbol: str, db=Depends(get_db)) -> list[dict[str, Any]]:
    """Recorded valuation snapshots, dated when observed rather than backfilled."""
    normalized = _normalize_symbol(symbol)
    result = await db.execute(select(Financials.updated_at, Financials.pe).join(
        Stock, Stock.id == Financials.stock_id
    ).where(Stock.symbol == normalized, Financials.pe > 0,
            Financials.updated_at.is_not(None), Financials.period_type == "ttm")
      .order_by(Financials.updated_at))
    return [{"date": observed.isoformat(), "pe": pe} for observed, pe in result if _number(pe) is not None]


@router.get("/{symbol}/quarters")
async def get_quarters(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    try:
        ticker = await run_in_threadpool(_fetch_yfinance_ticker, normalized)
        df = ticker.quarterly_income_stmt
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load quarters for {symbol}") from exc
    table = _statement_table_from_df(
        df,
        "Quarterly Results",
        [
            ("Revenue", "Total Revenue"),
            ("Total Expenses", "Total Expenses"),
            ("Operating Income", "Operating Income"),
            ("Net Profit", "Net Income"),
        ],
        limit=6,
        currency=_report_currency(ticker, normalized),
    )
    table["chart"] = _quarterly_chart(df, table["currency"])
    table["chartUnit"] = "Lakhs" if table["currency"] == "INR" else "Millions"
    table["incomeLabel"] = "Total Revenue"
    return table


def _load_shareholding(symbol: str) -> list[dict]:
    # The provider exposes a current snapshot, not historical promoter reports.
    holders = yf.Ticker(symbol).major_holders
    if holders is None or holders.empty or "Value" not in holders.columns:
        return []
    insiders = _number(holders["Value"].get("insidersPercentHeld"))
    institutions = _number(holders["Value"].get("institutionsPercentHeld"))
    if insiders is None or institutions is None or min(insiders, institutions) < 0 or insiders + institutions > 1:
        return []
    return [{"label": "Latest available", "periodEnd": None, "source": "Yahoo Finance ownership snapshot", "holdings": [{"name": "Insiders", "value": round(insiders * 100, 4)}, {"name": "Institutions", "value": round(institutions * 100, 4)}, {"name": "Other holders", "value": round((1 - insiders - institutions) * 100, 4)}]}]


@router.get("/{symbol}/shareholding")
async def get_shareholding(symbol: str) -> list[dict]:
    normalized = _normalize_symbol(symbol)
    try:
        return await run_in_threadpool(_load_shareholding, normalized)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Ownership data temporarily unavailable") from exc


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
        currency=_report_currency(ticker, normalized),
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
        currency=_report_currency(ticker, normalized),
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
        currency=_report_currency(ticker, normalized),
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
    pool = next((group["symbols"] for group in SECTORS.values() if normalized in group["symbols"]), None) if _is_indian_equity(normalized) else US_PEERS.get(sector.lower(), [])
    if pool is None:
        sector_ids = {"technology": "it", "financial services": "banking", "energy": "energy", "basic materials": "production", "healthcare": "pharma", "consumer cyclical": "auto", "industrials": "production", "utilities": "energy"}
        group = SECTORS.get(sector_ids.get(sector.lower(), ""))
        pool = group["symbols"] if group else []
    symbols = [normalized] + [item for item in pool if item != normalized][:5]

    async def peer_quote(peer: str) -> dict | None:
        try:
            quote_data = await _quote(peer)
        except Exception:
            return None
        try:
            peer_info = await run_in_threadpool(lambda: _fetch_yfinance_ticker(peer).info)
        except Exception:
            peer_info = {}
        return {**quote_data, "marketCap": _number(peer_info.get("marketCap")), "peRatio": _number(peer_info.get("trailingPE"))}

    rows = await asyncio.gather(*(peer_quote(peer) for peer in symbols))
    return [row for row in rows if row is not None]

