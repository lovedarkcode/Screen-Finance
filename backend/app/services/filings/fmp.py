"""FMP stable API client with bounded retries and credential-safe failures."""
import asyncio
import logging
import json
from decimal import Decimal

import httpx
from pydantic import ValidationError

from app.config import settings
from app.schemas.quarterly_filing import CompanyProfile, IncomeStatement, normalize_ticker

# FMP requires a query-string key. Never emit httpx request URLs at INFO/DEBUG.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def reject_nonfinite(value):
    raise ValueError("Non-finite provider number")


class PipelineError(Exception):
    def __init__(self, code: str, *, retryable=False, http_status=None, reason=None):
        self.code = code
        self.retryable = retryable
        self.http_status = http_status
        self.reason = reason
        super().__init__(code)


class FMPClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get(self, endpoint, symbol, **params):
        if not settings.FMP_API_KEY or not settings.FMP_API_KEY.get_secret_value().strip():
            raise PipelineError("fmp_key_missing")
        for attempt in range(3):
            try:
                response = await self.client.get(
                    f"https://financialmodelingprep.com/stable/{endpoint}",
                    params={"symbol": normalize_ticker(symbol), **params, "apikey": settings.FMP_API_KEY.get_secret_value()},
                    timeout=20, follow_redirects=False,
                )
            except httpx.TransportError:
                if attempt == 2:
                    raise PipelineError("fmp_connection_failed", retryable=True) from None
                await asyncio.sleep(2 ** attempt)
                continue
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt == 2:
                    raise PipelineError(f"fmp_http_{response.status_code}", retryable=True)
                wait = response.headers.get("Retry-After", "")
                delay = min(float(wait), 10) if wait.isdigit() else 2 ** attempt
                await asyncio.sleep(delay)
                continue
            if response.status_code == 402:
                raise PipelineError("fmp_http_402", http_status=402, reason="PROVIDER_TIER_RESTRICTION")
            if response.status_code != 200:
                raise PipelineError(f"fmp_http_{response.status_code}", http_status=response.status_code)
            if len(response.content) > 2_000_000:
                raise PipelineError("fmp_response_too_large")
            try:
                data = json.loads(response.text, parse_float=Decimal, parse_constant=reject_nonfinite)
            except ValueError:
                raise PipelineError("fmp_invalid_json") from None
            if not isinstance(data, list):
                raise PipelineError("fmp_invalid_response")
            return data

    async def income_statements(self, symbol):
        data = await self.get("income-statement", symbol, period="quarter", limit=8)
        if not data:
            raise PipelineError("fmp_no_quarterly_coverage")
        valid, rejected = [], 0
        for raw in data:
            try:
                record = IncomeStatement.model_validate(raw)
                if record.symbol != symbol:
                    raise ValueError("Listing mismatch")
                # Keep the exact provider record, with credentials excluded defensively.
                clean = {key: value for key, value in raw.items() if key.lower() not in ("apikey", "api_key", "authorization", "token")}
                # Preserve fractional provider numbers exactly in JSONB as decimal strings.
                clean = json.loads(json.dumps(clean, default=str, allow_nan=False))
                valid.append((record, clean))
            except (ValidationError, ValueError, TypeError):
                rejected += 1
        if not valid:
            raise PipelineError("fmp_no_valid_quarterly_records")
        return valid, rejected

    async def profile(self, symbol):
        data = await self.get("profile", symbol)
        try:
            profile = CompanyProfile.model_validate(data[0])
            if profile.symbol != symbol:
                raise ValueError("Listing mismatch")
            return profile
        except (IndexError, ValidationError, ValueError, TypeError):
            raise PipelineError("fmp_invalid_company_profile") from None
