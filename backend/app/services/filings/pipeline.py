"""Idempotent filing persistence and leased, recoverable summary generation."""
import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.config import settings
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.quarterly_result import QuarterlyResult
from app.services.filings.fmp import PipelineError
from app.services.filings.summary import generate_summary

logger = logging.getLogger("screen-finance.filings")
MAX_SUMMARY_ATTEMPTS = 6


def insert_for(session, model):
    return (sqlite_insert if session.get_bind().dialect.name == "sqlite" else pg_insert)(model)


def reset_summary():
    return {"summary_status": "pending", "summary_attempts": 0, "summary_error": None, "next_retry_at": None,
            "ai_summary": None, "ai_summary_json": None, "summary_model": None,
            "summary_token": None, "summary_lease_until": None}


def canonical_value(value):
    if isinstance(value, Decimal):
        if value == 0:
            return "0"
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    return str(value)


async def ensure_company(session, symbol, provider):
    company = (await session.execute(select(Company).where(Company.symbol == symbol))).scalar_one_or_none()
    if company:
        return company.id
    profile = await provider.profile(symbol)
    values = profile.model_dump(exclude={"symbol"})
    await session.execute(insert_for(session, Company).values(symbol=symbol, **values).on_conflict_do_nothing(index_elements=[Company.symbol]))
    await session.commit()
    return (await session.execute(select(Company.id).where(Company.symbol == symbol))).scalar_one()


async def save_statement(session, company_id, statement, raw):
    values = statement.financial_values()
    fingerprint = hashlib.sha256(json.dumps(statement.model_dump(), default=canonical_value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    # International filingDate may be a period-end proxy, according to FMP.
    company = await session.get(Company, company_id)
    is_us = company.country.upper() in ("US", "USA", "UNITED STATES")
    date_kind = "filing" if is_us and statement.filing_date and statement.filing_date != statement.period_end else "report_period_fallback" if statement.filing_date else "unavailable"
    key = and_(QuarterlyResult.company_id == company_id, QuarterlyResult.provider == statement.provider, QuarterlyResult.fiscal_year == statement.fiscal_year,
               QuarterlyResult.quarter_period == statement.quarter_period)
    existing = (await session.execute(select(QuarterlyResult).where(key))).scalar_one_or_none()
    now = datetime.now(UTC)
    values.update(company_id=company_id, raw_json_dump=raw, source_hash=fingerprint, filing_date_kind=date_kind, updated_at=now)
    if existing and existing.source_hash == fingerprint:
        # Preserve successful summaries and attempt counts on ordinary repeated polls.
        await session.execute(update(QuarterlyResult).where(key).values(raw_json_dump=raw))
        await session.commit()
        return "unchanged"
    insert = insert_for(session, QuarterlyResult).values(**values)
    await session.execute(insert.on_conflict_do_update(
        index_elements=[QuarterlyResult.company_id, QuarterlyResult.provider, QuarterlyResult.fiscal_year, QuarterlyResult.quarter_period],
        set_={**values, **reset_summary(), "revision": QuarterlyResult.revision + 1},
        where=QuarterlyResult.source_hash != fingerprint,
    ))
    # A corrected/backfilled prior quarter also changes summaries that compare to it.
    quarter = int(statement.quarter_period[1])
    next_year, next_quarter = (statement.fiscal_year + 1, "Q1") if quarter == 4 else (statement.fiscal_year, f"Q{quarter + 1}")
    dependents = or_(and_(QuarterlyResult.fiscal_year == next_year, QuarterlyResult.quarter_period == next_quarter),
                     and_(QuarterlyResult.fiscal_year == statement.fiscal_year + 1, QuarterlyResult.quarter_period == statement.quarter_period))
    await session.execute(update(QuarterlyResult).where(QuarterlyResult.company_id == company_id, QuarterlyResult.provider == statement.provider, dependents).values(**reset_summary()))
    # Financials are durable before any AI request is made.
    await session.commit()
    return "revised" if existing else "inserted"


def eligible_summary(now):
    return and_(QuarterlyResult.summary_attempts < MAX_SUMMARY_ATTEMPTS,
                or_(and_(QuarterlyResult.summary_status.in_(["pending", "failed"]),
                         or_(QuarterlyResult.next_retry_at.is_(None), QuarterlyResult.next_retry_at <= now)),
                    and_(QuarterlyResult.summary_status == "processing", QuarterlyResult.summary_lease_until <= now)))


async def summarize_pending(session_factory=SessionLocal, *, generate=generate_summary, limit=None):
    counts = {"completed": 0, "failed": 0}
    for _ in range(limit or settings.RESULTS_AI_BATCH_SIZE):
        now, token = datetime.now(UTC), str(uuid4())
        async with session_factory() as session:
            candidate = (await session.execute(select(QuarterlyResult.id).where(eligible_summary(now))
                                               .order_by(QuarterlyResult.period_end.desc(), QuarterlyResult.id.desc()).limit(1))).scalar_one_or_none()
            if candidate is None:
                break
            claimed = (await session.execute(update(QuarterlyResult).where(QuarterlyResult.id == candidate, eligible_summary(now))
                .values(summary_status="processing", summary_token=token, summary_lease_until=now + timedelta(minutes=5), summary_attempts=QuarterlyResult.summary_attempts + 1)
                .returning(QuarterlyResult.id))).scalar_one_or_none()
            await session.commit()
            if claimed is None:
                continue
            current = await session.get(QuarterlyResult, claimed)
            company = await session.get(Company, current.company_id)
            history = (await session.execute(select(QuarterlyResult).where(QuarterlyResult.company_id == company.id,
                QuarterlyResult.provider == current.provider,
                QuarterlyResult.fiscal_year >= current.fiscal_year - 1, QuarterlyResult.period_end <= current.period_end))).scalars().all()
            source_hash, attempts = current.source_hash, current.summary_attempts
            await session.commit()  # Release the DB connection during remote inference.
            try:
                text, structured = await generate(company, current, history)
                values = {"summary_status": "completed", "ai_summary": text, "ai_summary_json": structured,
                          "summary_model": settings.NEBIUS_MODEL, "summary_error": None, "next_retry_at": None}
                outcome = "completed"
            except PipelineError as error:
                values = {"summary_status": "failed", "summary_error": error.code,
                          "next_retry_at": now + timedelta(seconds=min(60 * 2 ** attempts, 3600)) if error.retryable else None}
                if not error.retryable:
                    values["summary_attempts"] = MAX_SUMMARY_ATTEMPTS
                outcome = "failed"
                logger.warning("Summary unavailable: result_id=%s code=%s", claimed, error.code)
            values.update(summary_token=None, summary_lease_until=None)
            stored = await session.execute(update(QuarterlyResult).where(QuarterlyResult.id == claimed, QuarterlyResult.source_hash == source_hash,
                                  QuarterlyResult.summary_token == token).values(**values))
            await session.commit()
            if stored.rowcount:
                counts[outcome] += 1
    return counts


async def ingest_tickers(provider, tickers, session_factory=SessionLocal):
    results = []
    for symbol in tickers:
        try:
            statements, rejected = await provider.income_statements(symbol)
            # Select the most recent revision if a provider response repeats a fiscal quarter.
            unique = {}
            for statement, raw in sorted(statements, key=lambda pair: (pair[0].filing_date or pair[0].period_end, str(pair[1].get("acceptedDate") or ""))):
                unique[(statement.fiscal_year, statement.quarter_period)] = (statement, raw)
            async with session_factory() as session:
                company_id = await ensure_company(session, symbol, provider)
                counts = {"inserted": 0, "revised": 0, "unchanged": 0}
                for statement, raw in sorted(unique.values(), key=lambda pair: pair[0].period_end):
                    counts[await save_statement(session, company_id, statement, raw)] += 1
            results.append({"ticker": symbol, **counts, "rejected": rejected})
        except PipelineError as error:
            failure = {"ticker": symbol, "error": error.code}
            if error.http_status == 402:
                failure.update(status="FAILED", reason="PROVIDER_TIER_RESTRICTION", code=402)
                logger.error("Infrastructure limitation: HTTP 402 Payment Required; ticker=%s reason=PROVIDER_TIER_RESTRICTION. Quarterly access is blocked by the provider subscription; no records inserted for this ticker.", symbol)
            else:
                logger.warning("Quarterly provider unavailable: ticker=%s code=%s", symbol, error.code)
            results.append(failure)
        except Exception as error:
            # Report only the exception class; DB/provider messages can contain credentials.
            results.append({"ticker": symbol, "error": "storage_failed", "error_type": type(error).__name__})
            logger.error("Filing storage failed: ticker=%s error_type=%s", symbol, type(error).__name__)
    return results


async def retry_failed(session_factory=SessionLocal):
    async with session_factory() as session:
        await session.execute(update(QuarterlyResult).where(QuarterlyResult.summary_status == "failed").values(**reset_summary()))
        await session.commit()
