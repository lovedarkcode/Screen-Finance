"""Stock data endpoints. Returns data matching the frontend's stock.service.js shape."""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/stocks", tags=["stocks"])


_MOCK_DB: dict[str, dict] = {
    "AAPL": {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 195.27,
        "change": 1.72,
        "changePercent": 0.89,
        "date": "23 May 2026, 04:00 PM EDT",
        "marketStatus": "Market Closed",
        "exchange": "NASDAQ",
        "country": "US",
    }
}

_MOCK_METRICS = [
    {"label": "Market Cap", "value": "$2,996,858 Cr."},
    {"label": "Current Price", "value": "$195.27"},
    {"label": "High / Low", "value": "$198.62 / $164.08"},
    {"label": "Stock P/E", "value": "31.26"},
    {"label": "Book Value", "value": "$4.70"},
    {"label": "Dividend Yield", "value": "0.48 %"},
    {"label": "ROCE", "value": "38.72 %"},
    {"label": "ROE", "value": "147.11 %"},
    {"label": "Face Value", "value": "$0.10"},
    {"label": "Promoter holding", "value": "0.06 %"},
    {"label": "ROCE 5Yr", "value": "35.18 %"},
    {"label": "Sales", "value": "$3,94,328 Cr."},
    {"label": "PEG Ratio", "value": "2.44"},
    {"label": "Debt", "value": "$1,18,950 Cr."},
    {"label": "EPS", "value": "$6.24"},
    {"label": "Industry PE", "value": "28.11"},
    {"label": "OPM", "value": "30.58 %"},
    {"label": "ROE 10Yr", "value": "92.39 %"},
    {"label": "Price to book value", "value": "41.55"},
    {"label": "Debt to equity", "value": "1.22"},
    {"label": "ROE 5Yr", "value": "106.29 %"},
]

_QUARTER_COLS = [
    "Mar 2024", "Jun 2024", "Sep 2024", "Dec 2024", "Mar 2025",
    "Jun 2025", "Sep 2025", "Dec 2025", "Mar 2026",
]

_MOCK_QUARTERS = {
    "columns": _QUARTER_COLS,
    "rows": [
        {"label": "Sales",            "values": ["90,753","85,777","94,930","124,300","90,753","85,777","94,930","124,300","95,359"]},
        {"label": "Expenses",         "values": ["53,902","49,635","54,447","68,855","53,912","49,649","54,856","69,052","53,667"]},
        {"label": "Operating Profit", "values": ["36,851","36,142","40,483","55,445","36,841","35,928","40,074","55,049","41,692"]},
        {"label": "OPM %",            "values": ["40.61%","42.12%","42.61%","44.62%","40.58%","41.90%","42.19%","44.28%","43.72%"]},
        {"label": "Net Profit",       "values": ["23,636","21,448","24,196","36,330","23,686","21,448","23,482","35,248","24,780"]},
        {"label": "EPS ($)",          "values": ["1.53","1.40","1.54","2.36","1.53","1.40","1.52","2.30","1.62"]},
    ],
}

_MONTHS = ["Jun 2025", "Aug 2025", "Oct 2025", "Dec 2025", "Feb 2026", "Apr 2026"]
_SEED_PRICES = [165, 172, 180, 188, 184, 195]
_MOCK_CHART = [
    {"month": m, "price": p, "volume": 80_000_000 + (i * 12_000_000) % 80_000_000}
    for i, (m, p) in enumerate(zip(_MONTHS, _SEED_PRICES))
]


@router.get("")
async def list_stocks(limit: int = 25) -> dict:
    return {"items": list(_MOCK_DB.values())[:limit], "total": len(_MOCK_DB)}


@router.get("/{symbol}")
async def get_stock(symbol: str) -> dict:
    stock = _MOCK_DB.get(symbol.upper())
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    return stock


@router.get("/{symbol}/metrics")
async def get_metrics(symbol: str) -> list[dict]:
    return _MOCK_METRICS


@router.get("/{symbol}/chart")
async def get_chart(symbol: str, range: str = "1Yr") -> list[dict]:
    return _MOCK_CHART


@router.get("/{symbol}/quarters")
async def get_quarters(symbol: str) -> dict:
    return _MOCK_QUARTERS


@router.get("/{symbol}/profit-loss")
async def get_profit_loss(symbol: str) -> dict:
    return {"items": [], "symbol": symbol}


@router.get("/{symbol}/balance-sheet")
async def get_balance_sheet(symbol: str) -> dict:
    return {"items": [], "symbol": symbol}


@router.get("/{symbol}/cash-flow")
async def get_cash_flow(symbol: str) -> dict:
    return {"items": [], "symbol": symbol}


@router.get("/{symbol}/ratios")
async def get_ratios(symbol: str) -> dict:
    return {"items": [], "symbol": symbol}


@router.get("/{symbol}/peers")
async def get_peers(symbol: str) -> list[dict]:
    return [
        {"name": "Microsoft Corp.",      "symbol": "MSFT",  "price": 415.75,  "changePercent": 1.21},
        {"name": "NVIDIA Corporation",   "symbol": "NVDA",  "price": 1037.89, "changePercent": 1.32},
        {"name": "Alphabet Inc.",        "symbol": "GOOGL", "price": 167.34,  "changePercent": 0.85},
        {"name": "Meta Platforms, Inc.", "symbol": "META",  "price": 475.92,  "changePercent": -0.35},
        {"name": "Amazon.com, Inc.",     "symbol": "AMZN",  "price": 182.63,  "changePercent": 0.73},
    ]
