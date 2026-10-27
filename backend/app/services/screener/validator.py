"""Validate every condition before it can reach the SQL allowlist."""
import math
import re
from collections import defaultdict
from datetime import UTC, datetime

from app.schemas.screener import FinancialFilter, ParsedScreen, ScreenDefinition
from app.services.screener.metrics import METRICS, SECTORS, SECTOR_ALIASES

NUMBER = re.compile(r"(?<![\w.])[+-]?(?:\d+(?:,\d+)*(?:\.\d+)?|\.\d+)(?:e[+-]?\d+)?", re.I)
SCALES = {"trillion": 1e12, "billion": 1e9, "million": 1e6, "crore": 1e7, "crores": 1e7, "lakh": 1e5, "lakhs": 1e5, "thousand": 1e3, "cr": 1e7, "bn": 1e9, "b": 1e9, "m": 1e6, "k": 1e3}
EXCHANGE_PATTERN = r"(?:nyse american|nyse arca|nasdaq|nse|bse|nyse|otcqb|otcqx|otc|cboe)"
SP500_PATTERN = r"\b(?:s\s*&\s*p\s*500|sp\s*500|standard\s*(?:&|and)\s*poor'?s\s*500)\b"


class ScreenIssue(ValueError):
    def __init__(self, message, status="clarification"):
        super().__init__(message)
        self.status = status


def _sector(value):
    stripped = (value or "").strip()
    return SECTOR_ALIASES.get(stripped.casefold(), next((name for name in SECTORS if name.casefold() == stripped.casefold()), stripped or None))


def guard_query(query):
    if re.search(r"\b(ignore|override)\b.{0,35}\b(instructions?|prompts?|rules)\b|\b(drop|delete|alter|truncate)\s+table\b|\bunion\s+select\b|system\s*prompt", query, re.I):
        raise ScreenIssue("Enter a financial screening request with explicit conditions, rather than instructions or SQL.", "unsupported")
    logical_query = re.sub(r"\b(?:greater|less) than or equal(?: to)?\b", "comparison", query, flags=re.I)
    logical_query = re.sub(r"\b" + EXCHANGE_PATTERN + r"\b(?:\s*(?:,?\s*\b(?:or|and)\b|[,/&])\s*\b" + EXCHANGE_PATTERN + r"\b)+", "exchange coverage", logical_query, flags=re.I)
    if re.search(r"\bor\b", logical_query, re.I):
        raise ScreenIssue("OR between financial conditions is not supported yet. Exchange choices such as NSE or BSE are supported; financial conditions must all match.", "unsupported")
    if re.search(r"\b(cheap|low debt|strong fundamentals|fundamentally strong|high quality|undervalued|overvalued)\b", query, re.I):
        raise ScreenIssue("Please specify numeric thresholds—for example debt/equity below 0.5 or P/E below 25. Vague descriptions do not have automatic thresholds.")
    if re.search(r"\b(cagr|roce|roa|ev/ebitda|interest coverage|gross (?:profit )?margin|p/b|p/s|eps growth|net income growth|profit growth|consisten\w*)\b|\b(?:last|past|over)\s+(?:\d+|three|four|five)\s+years?\b", query, re.I):
        raise ScreenIssue("That metric or multi-year condition is not available in the validated screening dataset. Use the supported metrics and latest annual, TTM or quarterly periods.", "unsupported")
    exclusion_query = re.sub(r"\b(?:without|no)\s+(?:any\s+)?(?:financial\s+)?filters?\b", "", query, flags=re.I)
    if re.search(r"\b(exclude|excluding|except|without|not in)\b", exclusion_query, re.I):
        raise ScreenIssue("Exclusion conditions are not supported yet. State positive market, sector and numeric AND conditions.", "unsupported")


def _mentioned_metrics(text):
    matches, covered = set(), set()
    aliases = sorted(((alias, field) for field, info in METRICS.items() for alias in info["aliases"]), key=lambda item: -len(item[0]))
    for alias, field in aliases:
        for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I):
            positions = set(range(match.start(), match.end()))
            if not positions & covered:
                matches.add(field)
                covered |= positions
    return matches


def _operator(text):
    for operator, pattern in [("between", r"\bbetween\b"), ("gte", r">=|≥|\bat least\b|greater than or equal"), ("lte", r"<=|≤|\bat most\b|\bup to\b|less than or equal"), ("gt", r">|\b(above|over|greater than|more than)\b"), ("lt", r"<|\b(below|under|less than)\b"), ("eq", r"(?<![<>])=|\b(equal(?: to)?|exactly)\b")]:
        if re.search(pattern, text, re.I):
            return operator
    return None


def _numbers(text, field):
    values = []
    for match in NUMBER.finditer(text):
        value = float(match.group().replace(",", ""))
        suffix = text[match.end():].lstrip().lower()
        scale = re.match(r"(trillion|billion|million|crores?|lakhs?|thousand|cr|bn|b|m|k)\b", suffix)
        if scale:
            value *= SCALES[scale.group()]
        if METRICS[field]["unit"] == "times" and (suffix.startswith("%") or suffix.startswith("percent")):
            value /= 100
        values.append(value)
    return values


def _verify_extraction(parsed, query, market=None):
    lower = query.casefold()
    market_patterns = {"US": r"\b(us|usa|united states|nasdaq|nyse|american)\b|u\.s\.", "IN": r"\b(india|indian|nse|bse)\b"}
    mentioned = {market for market, pattern in market_patterns.items() if re.search(pattern, lower)}
    index_match = re.search(SP500_PATTERN, query, re.I)
    if index_match:
        mentioned.add("US")
    if parsed.index != ("SP500" if index_match else None):
        raise ScreenIssue("The requested index membership was not preserved. Specify S&P 500 explicitly.")
    if market and mentioned and mentioned != {market}:
        raise ScreenIssue("The prompt names a different market. Change the market selector or update the prompt.")
    expected_market = next(iter(mentioned)) if len(mentioned) == 1 else None
    expected_market = market or expected_market
    if parsed.market != expected_market:
        raise ScreenIssue("The requested market coverage was not preserved. Omit market to screen all imported companies.")
    exchanges = {match.group().casefold() for match in re.finditer(r"\b" + EXCHANGE_PATTERN + r"\b", query, re.I)}
    interpreted_exchanges = {name.casefold() for name in parsed.exchanges} | ({parsed.exchange.casefold()} if parsed.exchange else set())
    if exchanges != interpreted_exchanges:
        raise ScreenIssue("The requested exchanges were not preserved. Specify the exchange choices explicitly.")
    sector_terms = {**{name.casefold(): name for name in SECTORS}, **SECTOR_ALIASES}
    sectors = {canonical for term, canonical in sector_terms.items() if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", lower)}
    interpreted_sector = _sector(parsed.sector)
    if len(sectors) > 1 or (sectors and interpreted_sector not in sectors) or (interpreted_sector and not sectors and interpreted_sector.casefold() not in lower):
        raise ScreenIssue("The requested sector was not preserved. Name an explicit sector in your prompt.")
    if parsed.industry and parsed.industry.casefold() not in lower:
        raise ScreenIssue("The requested industry could not be matched verbatim. Choose an explicit industry.")
    sort_clause = re.search(r"\bsort(?:ed)?(?:\s+the\s+results)?\s+by\s+([^.;]+)", query, re.I)
    if sort_clause and _mentioned_metrics(sort_clause.group(1)) and parsed.sort_by not in _mentioned_metrics(sort_clause.group(1)):
        raise ScreenIssue("The requested sort metric was not preserved.")
    if re.search(r"\bascending\b|\blowest\b.{0,25}\bfirst\b", query, re.I) and parsed.sort_desc:
        raise ScreenIssue("The requested ascending sort order was not preserved.")
    if re.search(r"\bdescending\b|\bhighest\b.{0,25}\bfirst\b", query, re.I) and not parsed.sort_desc:
        raise ScreenIssue("The requested descending sort order was not preserved.")
    covered = [False] * len(query)
    if index_match:
        covered[index_match.start():index_match.end()] = [True] * len(index_match.group())
    if parsed.as_of:
        match = re.search(r"\bas of\s+" + re.escape(parsed.as_of.isoformat()), query, re.I)
        if not match:
            raise ScreenIssue("The screening date was not explicitly requested. Use 'as of YYYY-MM-DD'.")
        covered[match.start():match.end()] = [True] * len(match.group())
    for match in re.finditer(r"\b(?:top|first|limit(?: to)?|show|return)\s+(\d+)\b", query, re.I):
        if int(match.group(1)) != parsed.limit:
            raise ScreenIssue("The requested result limit was not preserved. Use a limit between one and one hundred.")
        covered[match.start(1):match.end(1)] = [True] * len(match.group(1))
    for condition in parsed.filters:
        text = condition.source_text.casefold()
        start = lower.find(text)
        if start < 0:
            raise ScreenIssue("A filter could not be traced to the request. Please restate the metric and threshold explicitly.")
        for index in range(start, start + len(text)):
            covered[index] = True
        if _mentioned_metrics(text) != {condition.field}:
            raise ScreenIssue("A financial metric could not be matched faithfully to its source condition. Please name each metric explicitly.")
        currencies = {currency for currency, pattern in {"USD": r"\$|\busd\b|\bu\.?s\.? dollars?\b", "INR": r"₹|\binr\b|\brupees?\b|\brs\.?\b"}.items() if re.search(pattern, text)}
        expected_currency = condition.currency or ("INR" if parsed.market == "IN" else "USD")
        if currencies and (METRICS[condition.field]["unit"] != "currency" or currencies != {expected_currency}):
            raise ScreenIssue("The explicit threshold currency was not preserved. Use INR for Indian screens or USD for US screens; currency conversion is unavailable.")
        expected_operator = _operator(text)
        if expected_operator and condition.operator != expected_operator:
            raise ScreenIssue("A comparison operator was not preserved. Please specify above, below, equal, or between explicitly.")
        explicit_dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        if explicit_dates and (len(explicit_dates) != 1 or str(condition.period_end) != explicit_dates[0]):
            raise ScreenIssue("The requested fiscal period end was not preserved.")
        for basis, pattern in [("ttm", r"\bttm\b|trailing twelve"), ("quarterly", r"\bquarter(?:ly)?\b"), ("annual", r"\bannual\b|fiscal year")]:
            if re.search(pattern, text) and (condition.period or METRICS[condition.field]["default_period"]) != basis:
                raise ScreenIssue("The financial reporting period was not preserved.")
        # Exact period ends are metadata, not financial threshold values.
        threshold_text = re.sub(r"\d{4}-\d{2}-\d{2}", "", text)
        numbers = _numbers(threshold_text, condition.field)
        actual = list(condition.value) if isinstance(condition.value, tuple) else [condition.value]
        if not numbers and re.search(r"\b(profitable|positive|negative)\b", text):
            if actual != [0] or condition.operator != ("lt" if "negative" in text else "gt"):
                raise ScreenIssue("The sign-based condition was not interpreted consistently. Please specify a numeric threshold.")
        elif len(numbers) != len(actual) or any(not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a, b in zip(numbers, actual)):
            raise ScreenIssue("A numeric threshold or unit could not be verified against the request. Please restate it explicitly.")
        elif not expected_operator:
            raise ScreenIssue("Please specify the comparison for each threshold: above, below, equal or between.")
    if any(not all(covered[match.start():match.end()]) for match in NUMBER.finditer(query)):
        raise ScreenIssue("Some numbers or conditions were not represented by the extracted filters. Please restate all metrics and thresholds explicitly.")
    if _mentioned_metrics(query) - {item.field for item in parsed.filters} - {parsed.sort_by}:
        raise ScreenIssue("A requested financial condition was not extracted. Please restate it explicitly.")


def validate_screen(screen, query=None, market=None):
    warnings = []
    if query is not None and isinstance(screen, ParsedScreen):
        conditions = []
        for item in screen.filters:
            if item.period_end and item.period_end.isoformat() not in item.source_text:
                item = item.model_copy(update={"period_end": None})
                warnings.append("An unrequested AI fiscal date was removed. Filters use the latest available reporting periods.")
            conditions.append(item)
        screen = screen.model_copy(update={"filters": conditions})
    if isinstance(screen, ParsedScreen) and screen.unresolved_conditions:
        raise ScreenIssue("Please clarify the unsupported or ambiguous conditions: " + "; ".join(screen.unresolved_conditions)[:800])
    if screen.as_of and screen.as_of > datetime.now(UTC).date():
        raise ScreenIssue("Future screening dates are unavailable.", "unsupported")
    if screen.index and screen.market != "US":
        raise ScreenIssue("S&P 500 membership requires the US market.", "invalid")
    if screen.index and screen.as_of:
        raise ScreenIssue("Historical S&P 500 membership is not available. Remove the historical screening date.", "unsupported")
    selected_exchanges = list(dict.fromkeys(screen.exchanges or ([screen.exchange] if screen.exchange else [])))
    if screen.exchange and screen.exchanges and set(screen.exchanges) != {screen.exchange}:
        raise ScreenIssue("Use either a single exchange or a list of exchanges, not conflicting selections.", "invalid")
    if screen.market and any((name in ("NSE", "BSE")) != (screen.market == "IN") for name in selected_exchanges):
        raise ScreenIssue("The selected exchange does not belong to the selected market.", "invalid")
    if screen.sort_by not in {*METRICS, "name", "symbol"}:
        raise ScreenIssue("Choose a supported sort field.", "invalid")
    normal = screen.model_dump(exclude={"filters", "unresolved_conditions"})
    normal["exchange"] = selected_exchanges[0] if len(selected_exchanges) == 1 else None
    normal["exchanges"] = selected_exchanges if len(selected_exchanges) > 1 else []
    normal["sector"] = _sector(screen.sector)
    normal["industry"] = (screen.industry or "").strip() or None
    normal["filters"], seen = [], set()
    bounds = defaultdict(lambda: [-math.inf, True, math.inf, True])
    for item in screen.filters:
        definition = METRICS.get(item.field)
        if not definition:
            raise ScreenIssue("The request contains an unsupported financial metric. Choose from the supported metric list.", "unsupported")
        period = item.period or definition["default_period"]
        if period not in definition["periods"]:
            raise ScreenIssue(f"{definition['label']} is unavailable for the requested financial period.", "unsupported")
        if item.period_end and item.period_end > datetime.now(UTC).date():
            raise ScreenIssue("Future financial periods cannot be screened from reported data.", "unsupported")
        values = item.value if isinstance(item.value, tuple) else (item.value,)
        if any(isinstance(value, bool) or not math.isfinite(value) for value in values) or ((item.operator == "between") != (len(values) == 2)):
            raise ScreenIssue("Use one finite threshold, or two ordered bounds for between.", "invalid")
        if len(values) == 2 and values[0] > values[1]:
            raise ScreenIssue("The lower between bound must not exceed its upper bound.", "invalid")
        currency = item.currency
        if definition["unit"] == "currency":
            expected = {"IN": "INR", "US": "USD"}.get(screen.market)
            if currency and expected and currency != expected:
                raise ScreenIssue("Cross-currency screening needs an explicit conversion, which is not supported. Use INR thresholds for India or USD for US listings.")
            if not expected and not currency and any(value != 0 for value in values):
                raise ScreenIssue("Specify a market or currency for nonzero monetary thresholds; currencies are not converted.")
            currency = currency or (expected if any(value != 0 for value in values) else None)
        elif currency:
            raise ScreenIssue("Percentages and ratios must not have a currency.", "invalid")
        condition = FinancialFilter(field=item.field, operator=item.operator, value=item.value, period=period, period_end=item.period_end, currency=currency)
        key = condition.model_dump_json()
        if key in seen:
            continue
        seen.add(key)
        normal["filters"].append(condition)
        group = (item.field, period, item.period_end, currency)
        lower, lower_inc, upper, upper_inc = bounds[group]
        lo = values[0] if item.operator in ("gt", "gte", "eq", "between") else -math.inf
        hi = values[-1] if item.operator in ("lt", "lte", "eq", "between") else math.inf
        li, ui = item.operator != "gt", item.operator != "lt"
        if lo > lower:
            lower, lower_inc = lo, li
        elif lo == lower:
            lower_inc = lower_inc and li
        if hi < upper:
            upper, upper_inc = hi, ui
        elif hi == upper:
            upper_inc = upper_inc and ui
        if lower > upper or (lower == upper and not (lower_inc and upper_inc)):
            raise ScreenIssue(f"The conditions for {definition['label']} contradict each other.", "invalid")
        bounds[group] = [lower, lower_inc, upper, upper_inc]
        if not item.period:
            warnings.append(f"{definition['label']} uses the latest available {period} period.")
    if normal["sort_by"] in METRICS:
        definition = METRICS[normal["sort_by"]]
        normal["sort_period"] = screen.sort_period or definition["default_period"]
        if normal["sort_period"] not in definition["periods"]:
            raise ScreenIssue("The sort metric is unavailable for the requested period.", "invalid")
    else:
        normal["sort_period"] = None
    if query is not None:
        guard_query(query)
        _verify_extraction(screen, query, market)
    warnings.append("Screening covers the imported stock universe, not every exchange listing. Missing or incompatible metric values do not match numeric filters.")
    if screen.sort_by in METRICS and METRICS[screen.sort_by]["unit"] == "currency":
        warnings.append("Monetary sorting groups values by currency; unavailable values sort last. No currency conversion is applied.")
    if screen.as_of:
        warnings.append("Historical screening uses stored observation dates. Overwritten snapshots and data without an observation date are unavailable for historical screens.")
    return ScreenDefinition(**normal), list(dict.fromkeys(warnings))
