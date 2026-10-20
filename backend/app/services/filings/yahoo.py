"""Yahoo quarterly income statements; exchange catalogs supply listing identity."""
import asyncio
import calendar
import math
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from urllib.parse import quote

import yfinance as yf
from pydantic import ValidationError

from app.schemas.quarterly_filing import IncomeStatement
from app.services.filings.fmp import PipelineError

PROVIDER = "Yahoo Finance/yfinance"


def fiscal_period(end, annual_end):
    # A 52/53-week year may end a few days either side of a month boundary.
    def nearest_month_end(value):
        candidates = [date((value + timedelta(days=offset)).year, (value + timedelta(days=offset)).month,
                           calendar.monthrange((value + timedelta(days=offset)).year, (value + timedelta(days=offset)).month)[1])
                      for offset in (-15, 0, 15)]
        return min(candidates, key=lambda candidate: abs((value - candidate).days))
    normalized, anchor = nearest_month_end(end), nearest_month_end(annual_end)
    distance = (normalized.month - anchor.month) % 12
    if distance % 3:
        raise ValueError("Quarter does not align with fiscal year end")
    return normalized.year + (normalized.month > anchor.month), f"Q{distance // 3 if distance else 4}"


def number(value):
    if value is None or isinstance(value, bool) or not math.isfinite(float(value)):
        return None
    return str(Decimal(str(value)).quantize(Decimal("0.0000000001")))


def normalize_statements(symbol, info, quarterly, annual):
    if info.get("symbol", "").upper() != symbol:
        raise PipelineError("yahoo_identity_mismatch")
    expected_exchanges = {"NSI", "NSE"} if symbol.endswith(".NS") else {"BSE", "BOM"} if symbol.endswith(".BO") else {"NMS", "NGM", "NCM", "NASDAQ", "NYQ", "NYSE"}
    # The exchange directory and exact returned symbol establish identity even
    # when Yahoo omits the optional exchange field (common for NSE SME profiles).
    if info.get("exchange") and info["exchange"] not in expected_exchanges:
        raise PipelineError("yahoo_exchange_mismatch")
    if quarterly.empty:
        raise PipelineError("yahoo_no_quarterly_data")
    currency = info.get("financialCurrency")
    if not currency:
        raise PipelineError("yahoo_reporting_currency_missing")
    annual_dates = [column.date() for column in annual.columns if column.date() <= datetime.now(UTC).date() and annual[column].notna().any()]
    if not annual_dates:
        raise PipelineError("yahoo_fiscal_year_unknown")
    anchor = max(annual_dates)
    records, rejected = [], 0
    for column in quarterly.columns:
        end = column.date()
        if not quarterly[column].notna().any():
            continue
        values = {str(key): number(value) for key, value in quarterly[column].items()}
        try:
            fiscal_year, quarter = fiscal_period(end, anchor)
            raw = {"symbol": symbol, "provider": PROVIDER, "period_basis": "inferred_from_annual_period_end",
                   "fiscalYear": fiscal_year, "period": quarter, "date": end.isoformat(), "filingDate": None,
                   "reportedCurrency": currency, "revenue": values.get("TotalRevenue"), "netIncome": values.get("NetIncome"),
                   "operatingIncome": values.get("OperatingIncome"), "eps": values.get("BasicEPS"), "epsDiluted": values.get("DilutedEPS")}
            statement = IncomeStatement.model_validate(raw)
            records.append((statement, {**raw, "annual_period_end_anchor": anchor.isoformat(), "provider_fields": values,
                                       "provider_exchange": info.get("exchange"),
                                       "source_url": f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}/financials/"}))
        except (ValidationError, ValueError):
            rejected += 1
    if not records:
        raise PipelineError("yahoo_no_valid_quarters")
    return records, rejected


def fetch_statements(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.get_info()
        quarterly = ticker.get_income_stmt(freq="quarterly")
        annual = ticker.get_income_stmt(freq="yearly")
        return normalize_statements(symbol, info, quarterly, annual)
    except PipelineError:
        raise
    except Exception as error:
        # Do not persist upstream exception text or identify empty frames as success.
        name = type(error).__name__
        raise PipelineError("yahoo_rate_limited" if name == "YFRateLimitError" else "yahoo_request_failed", retryable=True) from None


class YahooClient:
    async def income_statements(self, symbol):
        return await asyncio.to_thread(fetch_statements, symbol)
