"""Bound SELECTs over stock masters and independently selected financial metrics."""
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import and_, case, exists, false, func, or_, select, true
from sqlalchemy.orm import aliased

from app.models.financials import Financials
from app.models.stock import Stock
from app.services.screener.metrics import METRICS, VALIDATION_VERSION

DEFAULT_COLUMNS = [("market_cap", "snapshot"), ("pe", "ttm"), ("roe", "annual"), ("revenue_growth", "annual"), ("debt_to_equity", "snapshot"), ("net_profit_margin", "annual")]
EXCHANGES = {
    "NSE": "NSE", "NSI": "NSE", "XNSE": "NSE", "NATIONAL STOCK EXCHANGE": "NSE",
    "BSE": "BSE", "BSE LTD": "BSE", "BOM": "BSE", "XBOM": "BSE", "BOMBAY STOCK EXCHANGE": "BSE",
    "NASDAQ": "NASDAQ", "NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "XNAS": "NASDAQ",
    "NYSE": "NYSE", "NYQ": "NYSE", "XNYS": "NYSE", "ASE": "NYSE American", "NYSE AMERICAN": "NYSE American",
    "PCX": "NYSE Arca", "NYSE ARCA": "NYSE Arca", "CBOE": "Cboe", "BATS": "Cboe",
    "OTC": "OTC", "PNK": "OTC", "OTCQB": "OTCQB", "OTCQX": "OTCQX",
}
COUNTRIES = {"IN": "IN", "IND": "IN", "INDIA": "IN", "US": "US", "USA": "US", "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US"}
VERIFIED = ("recomputed", "normalized", "provider")


def exchange_expression():
    return case(EXCHANGES, value=func.upper(func.trim(Stock.exchange)), else_=func.trim(Stock.exchange))


def market_expression():
    exchange = exchange_expression()
    return case((exchange.in_(["NSE", "BSE"]), "IN"), (exchange.in_(sorted(set(EXCHANGES.values()) - {"NSE", "BSE"})), "US"), else_=case(COUNTRIES, value=func.upper(func.trim(Stock.country)), else_=func.upper(func.trim(Stock.country))))


def _cutoff(screen):
    return datetime.combine(screen.as_of + timedelta(days=1), time(), tzinfo=UTC) if screen.as_of else None


def _selections(screen):
    return list(dict.fromkeys([*((field, basis, None) for field, basis in DEFAULT_COLUMNS), *((item.field, item.period, item.period_end) for item in screen.filters), *([(screen.sort_by, screen.sort_period, None)] if screen.sort_by in METRICS else [])]))


def _metric_date(row, field):
    # A shared TTM/snapshot row may hold metrics with different or unknown dates.
    return row.provenance[field]["period_end"].as_string()


def _value(aliases, selection, screen):
    field, _, _ = selection
    if field == "market_cap":
        if selection[2]:
            return case((false(), Stock.market_cap), else_=None)
        if screen.as_of:
            return case((Stock.updated_at < _cutoff(screen), Stock.market_cap), else_=None)
        return Stock.market_cap
    return getattr(aliases[selection], METRICS[field]["column"])


def _verified(row, field):
    return row.provenance[field]["validation_status"].as_string().in_(VERIFIED)


def _currency(aliases, selection):
    field, _, _ = selection
    return func.upper(func.trim(Stock.currency)) if field == "market_cap" else func.upper(func.trim(aliases[selection].provenance[field]["currency"].as_string()))


def _plan(screen):
    aliases, ranks = {}, {}
    for index, selection in enumerate(_selections(screen)):
        field, basis, end = selection
        if field == "market_cap":
            continue  # Stock-master values do not require a financial row.
        metric_date = _metric_date(Financials, field)
        source = select(Financials, func.row_number().over(partition_by=Financials.stock_id, order_by=(metric_date.desc().nulls_last(), Financials.period_end.desc().nulls_last(), Financials.updated_at.desc().nulls_last(), Financials.id.desc())).label("rank")).where(
            func.lower(func.trim(Financials.period_type)) == basis,
            Financials.validation_version == VALIDATION_VERSION,
            getattr(Financials, METRICS[field]["column"]).is_not(None),
            _verified(Financials, field),
            or_(metric_date.is_(None), metric_date <= (screen.as_of or datetime.now(UTC).date()).isoformat()),
            or_(Financials.period_end.is_(None), Financials.period_end <= (screen.as_of or datetime.now(UTC).date())),
        )
        if end:
            source = source.where(metric_date == end.isoformat())
        if screen.as_of:
            source = source.where(Financials.updated_at < _cutoff(screen))
        ranked = source.subquery(name=f"metric_{index}")
        aliases[selection], ranks[selection] = aliased(Financials, ranked), ranked.c.rank
    statement = select(Stock, *aliases.values()).select_from(Stock)
    for key, row in aliases.items():
        statement = statement.outerjoin(row, and_(row.stock_id == Stock.id, ranks[key] == 1))
    stages = [{"name": "market", "predicates": [market_expression() == screen.market if screen.market else true()]}]
    if screen.exchanges or screen.exchange:
        stages.append({"name": "exchanges", "predicates": [exchange_expression().in_(screen.exchanges or [screen.exchange])]})
    if screen.sector:
        stages.append({"name": "sector", "predicates": [func.lower(func.trim(Stock.sector)) == screen.sector.casefold()]})
    if screen.industry:
        stages.append({"name": "industry", "predicates": [func.lower(func.trim(Stock.industry)) == screen.industry.casefold()]})
    for index, condition in enumerate(screen.filters):
        field, basis = condition.field, condition.period
        selection = (field, basis, condition.period_end)
        expression = _value(aliases, selection, screen)
        value = condition.value
        operations = {"gt": lambda: expression > value, "gte": lambda: expression >= value, "lt": lambda: expression < value, "lte": lambda: expression <= value, "eq": lambda: expression == value, "between": lambda: expression.between(*value)}
        comparison = operations[condition.operator]()
        verified = true() if field == "market_cap" else _verified(aliases[selection], field)
        currency = _currency(aliases, selection)
        currency_ok = currency == condition.currency if condition.currency else true()
        domain_ok = true()
        if field == "pe":
            row = aliases[selection]
            domain_ok = and_(expression > 0, or_(row.eps.is_(None), row.eps > 0))
        # Separate unavailable requested periods from a metric absent at every period.
        any_value = Stock.market_cap.is_not(None) if field == "market_cap" else exists(select(Financials.id).where(Financials.stock_id == Stock.id, getattr(Financials, METRICS[field]["column"]).is_not(None)))
        any_verified = any_value if field == "market_cap" else exists(select(Financials.id).where(Financials.stock_id == Stock.id, getattr(Financials, METRICS[field]["column"]).is_not(None), Financials.validation_version == VALIDATION_VERSION, _verified(Financials, field)))
        missing = expression.is_(None)
        eligible = and_(expression.is_not(None), verified, currency_ok, domain_ok)
        stages.append({"name": f"filter_{index + 1}:{field}:{basis}", "predicates": [eligible, comparison], "checks": {
            "missing_metric": and_(missing, ~any_value),
            "incompatible_period": and_(missing, any_verified),
            "unverified_metric": and_(missing, any_value, ~any_verified),
            "incompatible_currency": and_(expression.is_not(None), verified, ~func.coalesce(currency_ok, false())),
            "invalid_domain": and_(expression.is_not(None), verified, currency_ok, ~domain_ok),
            "failed_condition": and_(eligible, ~comparison),
        }})
    return statement, stages, aliases


def statements(screen, page):
    statement, stages, aliases = _plan(screen)
    statement = statement.where(*(predicate for stage in stages for predicate in stage["predicates"]))
    count = select(func.count()).select_from(statement.order_by(None).subquery())
    order = []
    if screen.sort_by in ("name", "symbol"):
        sort = getattr(Stock, screen.sort_by)
    else:
        selection = (screen.sort_by, screen.sort_period, None)
        sort = _value(aliases, selection, screen)
        if screen.sort_by != "market_cap":
            row = aliases[selection]
            valid = _verified(row, screen.sort_by)
            if screen.sort_by == "pe":
                valid = and_(valid, row.pe > 0, or_(row.eps.is_(None), row.eps > 0))
            sort = case((valid, sort), else_=None)
        if METRICS[screen.sort_by]["unit"] == "currency":
            # Keep all companies; never compare unlike currencies as equal units.
            order.extend([sort.is_(None).asc(), _currency(aliases, selection).asc().nulls_last()])
    statement = statement.order_by(*order, (sort.desc() if screen.sort_desc else sort.asc()).nulls_last(), Stock.symbol.asc(), Stock.id.asc()).offset((page - 1) * screen.limit).limit(screen.limit)
    return statement, count, list(aliases)


async def diagnostics(session, screen):
    """Shared production predicates; called by the development-only CLI."""
    statement, stages, _ = _plan(screen)
    result, applied = [], []
    for stage in stages:
        checks = stage.get("checks", {})
        aggregate = statement.with_only_columns(func.count(), func.count().filter(and_(*stage["predicates"])), *(func.count().filter(check) for check in checks.values()), maintain_column_froms=True).where(*applied)
        before, after, *counts = (await session.execute(aggregate)).one()
        applied.extend(stage["predicates"])
        result.append({"stage": stage["name"], "before": before, "remaining": after, "excluded": before - after, **dict(zip(checks, counts))})
    return result


async def empty_explanation(session, screen, universe, total):
    if total:
        return "page_out_of_range", "This page is beyond the matching results. Return to an earlier page."
    if not universe:
        return "empty_universe", "No companies are stored in the selected market universe."
    trace = await diagnostics(session, screen)
    stage = next((item for item in trace if item["before"] and not item["remaining"]), None)
    if stage:
        exclusions = []
        if stage.get("missing_metric", 0) + stage.get("unverified_metric", 0):
            exclusions.append("required metric values are missing or unverified")
        if stage.get("incompatible_period"):
            exclusions.append("data is unavailable for the requested period or screening date")
        if stage.get("incompatible_currency"):
            exclusions.append("reported currencies do not match the threshold currency")
        if stage.get("failed_condition", 0) + stage.get("invalid_domain", 0):
            exclusions.append("available values fail the requested condition")
        if exclusions:
            reason = "no_matches"
            if stage.get("missing_metric", 0) + stage.get("unverified_metric", 0) == stage["before"]:
                reason = "missing_metrics"
            elif stage.get("incompatible_period") == stage["before"]:
                reason = "unavailable_period"
            elif stage.get("incompatible_currency") == stage["before"]:
                reason = "incompatible_currency"
            return reason, "No companies match every condition: " + "; ".join(exclusions) + "."
    return "no_matches", "No stored companies match the selected exchange, sector, industry and financial conditions."


def format_rows(rows, screen, selections):
    result = []
    for stock, *financial_rows in rows:
        by_metric = dict(zip(selections, financial_rows))
        metrics = {}
        for selection in _selections(screen):
            field, basis, end = selection
            row = by_metric.get(selection)
            metadata = (row.provenance or {}).get(field, {}) if row else {}
            value = getattr(row, METRICS[field]["column"]) if row else None
            verified = metadata.get("validation_status") in VERIFIED
            if field == "market_cap":
                observed = stock.updated_at
                available = not screen.as_of or observed is not None and observed.date() <= screen.as_of
                value, verified = (stock.market_cap if available else None), available
                metadata = {"currency": stock.currency, "updated_at": observed.isoformat() if observed else None, "period_end": None, "period": "Quote snapshot", "source": "Stock master", "validation_status": "stored"}
                if end:
                    value = None  # Quote snapshots have no known fiscal reporting end.
            if field == "pe" and (value is not None and value <= 0 or row and row.eps is not None and row.eps <= 0):
                value = None
            metrics[f"{field}:{basis}" + (f":{end}" if end else "")] = {"field": field, "basis": basis, "unit": METRICS[field]["unit"], "definition": METRICS[field]["definition"], **metadata, "value": value if verified else None, "availability": "available" if verified and value is not None else "unavailable"}
        exchange = EXCHANGES.get(stock.exchange.strip().upper(), stock.exchange.strip())
        market = "IN" if exchange in ("NSE", "BSE") else "US" if exchange in EXCHANGES.values() else COUNTRIES.get(stock.country.strip().upper(), stock.country.strip().upper())
        result.append({"symbol": stock.symbol, "name": stock.name, "exchange": exchange, "market": market, "sector": stock.sector, "industry": stock.industry, "currency": stock.currency, "price": stock.last_price if not screen.as_of or stock.updated_at and stock.updated_at.date() <= screen.as_of else None, "updated_at": stock.updated_at.isoformat() if stock.updated_at else None, "metrics": metrics})
    return result


async def last_updated(session):
    stocks = (await session.execute(select(func.max(Stock.updated_at)))).scalar_one()
    financials = (await session.execute(select(func.max(Financials.updated_at)))).scalar_one()
    dates = [value for value in (stocks, financials) if value is not None]
    return max(dates) if dates else None


async def universe_count(session, market):
    statement = select(func.count(Stock.id))
    if market:
        statement = statement.where(market_expression() == market)
    return (await session.execute(statement)).scalar_one()
