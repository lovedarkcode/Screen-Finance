"""Allowlist of metrics backed by the financial validation engine."""
SCHEMA_VERSION = "screener-v5"
VALIDATION_VERSION = 1
OPERATORS = ("gt", "gte", "lt", "lte", "eq", "between")


def metric(label, column, unit, periods, definition, aliases=()):
    return {"label": label, "column": column, "unit": unit, "periods": list(periods), "default_period": periods[0], "definition": definition, "operators": list(OPERATORS), "aliases": list(aliases), "data_type": "number", "source": "Yahoo Finance/yfinance, checked against retrieved source records", "available": True}


METRICS = {
    "market_cap": metric("Market capitalization", "market_cap", "currency", ("snapshot",), "Latest provider market capitalization in quote currency.", ("market cap", "market capitalization")),
    "pe": metric("P/E", "pe", "times", ("ttm",), "Positive provider trailing P/E, unavailable for known non-positive trailing earnings; exact TTM end may be unavailable.", ("p/e", "pe ratio", "price to earnings")),
    "roe": metric("ROE", "roe", "percent", ("annual", "ttm"), "Annual net income / average positive beginning/end equity × 100; TTM uses provider ROE percentage.", ("roe", "return on equity")),
    "net_profit_margin": metric("Net profit margin", "net_profit_margin", "percent", ("annual", "ttm", "quarterly"), "Same-period net income / positive revenue × 100.", ("net profit margin", "net margin")),
    "operating_margin": metric("Operating margin", "operating_margin", "percent", ("annual",), "Annual operating income / positive annual revenue × 100.", ("operating margin",)),
    "revenue_growth": metric("Revenue growth", "revenue_growth", "percent", ("annual",), "(Annual revenue / comparable positive prior-year revenue − 1) × 100.", ("revenue growth", "sales growth")),
    "debt_to_equity": metric("Debt/equity", "debt_to_equity", "times", ("snapshot",), "Total debt / positive equity at the same balance-sheet date.", ("debt-to-equity", "debt to equity", "debt/equity")),
    "current_ratio": metric("Current ratio", "current_ratio", "times", ("snapshot",), "Current assets / positive current liabilities at the same date.", ("current ratio",)),
    "total_debt": metric("Total debt", "total_debt", "currency", ("snapshot",), "Latest balance-sheet total debt in reporting currency.", ("total debt",)),
    "net_debt": metric("Net debt", "net_debt", "currency", ("snapshot",), "Total debt minus cash at the same date.", ("net debt",)),
    "operating_cash_flow": metric("Operating cash flow", "operating_cash_flow", "currency", ("annual",), "Reported annual operating cash flow in reporting currency.", ("operating cash flow",)),
    "free_cash_flow": metric("Free cash flow", "free_cash_flow", "currency", ("annual",), "Operating cash flow minus absolute capital expenditure for the same year.", ("free cash flow", "fcf")),
    "free_cash_flow_margin": metric("Free cash flow margin", "free_cash_flow_margin", "percent", ("annual",), "Annual free cash flow / same-period positive revenue × 100.", ("free cash flow margin", "fcf margin")),
    "revenue": metric("Revenue", "sales", "currency", ("annual", "ttm", "quarterly"), "Revenue for the selected period.", ("revenue", "sales")),
    "net_income": metric("Net income", "net_profit", "currency", ("annual", "ttm", "quarterly"), "Net income for the selected period; profitable means net income > 0.", ("net income", "net profit", "profitable", "profitability")),
    "operating_income": metric("Operating income", "operating_profit", "currency", ("annual",), "Operating income for the fiscal year.", ("operating income", "operating profit")),
    "eps": metric("EPS", "eps", "currency", ("ttm",), "Provider trailing EPS in quote currency; exact TTM end may be unavailable.", ("eps", "earnings per share")),
}
UNSUPPORTED = ["ROCE", "ROA", "gross margin", "P/B", "P/S", "EV/EBITDA", "interest coverage", "EPS growth", "net income growth", "revenue CAGR", "profit CAGR", "multi-year consistency", "OR between financial conditions", "currency conversion", "news or price forecasts"]
SECTORS = ["Technology", "Financial Services", "Healthcare", "Consumer Cyclical", "Consumer Defensive", "Industrials", "Energy", "Utilities", "Basic Materials", "Real Estate", "Communication Services"]
SECTOR_ALIASES = {"it": "Technology", "information technology": "Technology", "tech": "Technology", "banking": "Financial Services", "financials": "Financial Services", "health care": "Healthcare"}
METRICS["market_cap"]["aliases"].append("marketcap")
METRICS["pe"]["aliases"].append("pe")
METRICS["debt_to_equity"]["aliases"].extend(["d/e", "dte"])
