"""Deterministic financial normalization, calculation and evidence verification."""
from datetime import datetime
from math import isclose
from urllib.parse import quote as urlquote, urlsplit

from app.api.v1 import stocks
from app.schemas.ai import AnalysisEvidence, AnalysisSource, EvidenceIssue, EvidenceQuality, FinancialTrend, ResearchClaim


def validate_identity(quote, info):
    if info.get("symbol") and stocks._normalize_symbol(info["symbol"]) != quote["symbol"]:
        raise ValueError("Financial profile belongs to another listing")
    code = info.get("exchange")
    exchange = {"NSI": "NSE", "NSE": "NSE", "BSE": "BSE", "BOM": "BSE"}.get(code) or stocks.US_EXCHANGES.get(code)
    if code and (exchange or code) != quote["exchange"]:
        raise ValueError("Financial profile exchange does not match the quote")


def _periods(frame, retrieved, count=5):
    if frame is None or frame.empty:
        return []
    # Fiscal period ends, not retrieval dates. Future/empty columns are not evidence.
    result = []
    for column in sorted(frame.columns, reverse=True):
        end = column.date()
        values = {str(key): stocks._number(value) for key, value in frame[column].items()}
        if end > retrieved.date() or not any(value is not None for value in values.values()):
            continue
        if any(period == end for period, _ in result):
            raise ValueError("Duplicate financial reporting period")
        result.append((end, values))
    return result[:count]


def _result(operation, values):
    if operation in ("percent_ratio", "ratio", "growth"):
        if values[1] <= 0:
            raise ValueError("Non-positive denominator")
        return {"percent_ratio": lambda: values[0] / values[1] * 100, "ratio": lambda: values[0] / values[1], "growth": lambda: (values[0] / values[1] - 1) * 100}[operation]()
    if operation == "fcf":
        return values[0] - abs(values[1])
    if operation == "subtract":
        return values[0] - values[1]
    if operation == "scale_percent":
        return values[0] * 100
    if operation == "sum_quarters":
        return sum(values)
    if operation == "roe":
        if min(values[1:]) <= 0:
            raise ValueError("Non-positive equity")
        return values[0] / ((values[1] + values[2]) / 2) * 100
    raise ValueError("Unknown calculation")


def _check_inputs(item, inputs):
    expected_count = {"percent_ratio": 2, "ratio": 2, "growth": 2, "fcf": 2, "subtract": 2, "scale_percent": 1, "sum_quarters": 4, "roe": 3}
    if len(inputs) != expected_count.get(item.operation) or any(not isinstance(raw.value, (int, float)) for raw in inputs):
        raise ValueError("Invalid calculation inputs")
    if item.operation == "scale_percent":
        if inputs[0].unit != "number" or item.unit != "percent" or item.kind != "normalized" or item.periodType != inputs[0].periodType or item.periodEnd != inputs[0].periodEnd:
            raise ValueError("Invalid percentage normalization")
        return
    if any(raw.unit != "currency" for raw in inputs) or len({raw.currency for raw in inputs}) != 1 or not inputs[0].currency:
        raise ValueError("Incompatible units or reporting currencies")
    required_unit = "percent" if item.operation in ("percent_ratio", "growth", "roe") else "times" if item.operation == "ratio" else "currency"
    if item.unit != required_unit or (item.unit == "currency" and item.currency != inputs[0].currency):
        raise ValueError("Incorrect result unit")
    ends = [raw.periodEnd for raw in inputs]
    if not all(ends):
        raise ValueError("Calculation needs fiscal dates")
    if item.operation == "growth":
        if any(raw.periodType != "annual" for raw in inputs) or not 330 <= (ends[0] - ends[1]).days <= 400 or item.periodEnd != ends[0] or item.periodType != "comparison":
            raise ValueError("Revenue growth requires comparable fiscal years")
    elif item.operation == "roe":
        if inputs[0].periodType != "annual" or any(raw.periodType != "instant" for raw in inputs[1:]) or ends[0] != ends[1] or not 330 <= (ends[1] - ends[2]).days <= 400 or item.periodEnd != ends[0] or item.periodType != "annual":
            raise ValueError("ROE requires annual income and beginning/end equity")
    elif item.operation == "sum_quarters":
        if any(raw.periodType != "quarterly" for raw in inputs) or any(not 75 <= (ends[i] - ends[i + 1]).days <= 105 for i in range(3)) or item.periodType != "ttm" or item.periodEnd != ends[0]:
            raise ValueError("TTM requires four consecutive quarters")
    elif len(set(ends)) != 1 or len({raw.periodType for raw in inputs}) != 1 or item.periodEnd != ends[0] or item.periodType != inputs[0].periodType:
        raise ValueError("Calculation periods do not align")


def validate_evidence(evidence, metric_ids, sources, quote, snapshot=None):
    source_map = {source.id: source for source in sources}
    if len(source_map) != len(sources):
        raise ValueError("Duplicate source IDs")
    expected_path = f"/quote/{urlquote(quote['symbol'], safe='.-^')}/"
    for source in sources:
        url = urlsplit(source.url)
        if url.scheme != "https" or url.netloc != "finance.yahoo.com" or not url.path.startswith(expected_path):
            raise ValueError("Source belongs to another company or provider")
    checked = {}
    for item in evidence:
        if item.id in checked or item.symbol != quote["symbol"] or item.exchange != quote["exchange"] or item.sourceId not in source_map:
            raise ValueError("Invalid evidence identity or source")
        if item.unit == "text":
            if not isinstance(item.value, str):
                raise ValueError("Text evidence needs text")
        elif not isinstance(item.value, (int, float)):
            raise ValueError("Financial evidence needs finite numeric values")
        if item.unit == "currency" and not item.currency:
            raise ValueError("Financial amounts require currency")
        if item.periodEnd and item.periodEnd > source_map[item.sourceId].retrievedAt.date():
            raise ValueError("Financial evidence has a future fiscal period")
        if item.kind in ("calculated", "normalized"):
            if not item.formula or any(key not in checked for key in item.inputs) or len(set(item.inputs)) != len(item.inputs):
                raise ValueError("Invalid calculation lineage")
            inputs = [checked[key] for key in item.inputs]
            if not inputs or item.sourceId != inputs[0].sourceId:
                raise ValueError("Calculation source does not match its inputs")
            _check_inputs(item, inputs)
            expected = _result(item.operation, [raw.value for raw in inputs])
            if not isclose(item.value, expected, rel_tol=1e-6, abs_tol=1e-5):
                raise ValueError("Calculated figure failed independent recomputation")
        else:
            if item.inputs or item.operation or item.formula or not item.sourceField:
                raise ValueError("Provider evidence requires a source field and no calculation")
            if snapshot is not None:
                expected_currency = quote["currency"] if item.sourceId in ("quote", "statistics") else str(snapshot["info"].get("financialCurrency") or "").upper()
                if item.unit == "currency" and item.currency != expected_currency:
                    raise ValueError("Evidence currency differs from its source")
                if item.sourceId == "quote":
                    raw = stocks._number(quote.get("price"))
                elif item.sourceId == "statistics":
                    raw = snapshot["info"].get(item.sourceField)
                    raw = str(raw or "").strip()[:2400] if item.unit == "text" else stocks._number(raw)
                else:
                    frame = snapshot["frames"].get(item.sourceId)
                    columns = [column for column in frame.columns if column.date() == item.periodEnd] if frame is not None else []
                    if len(columns) != 1 or item.sourceField not in frame.index:
                        raise ValueError("Evidence source record is missing")
                    raw = stocks._number(frame.loc[item.sourceField, columns[0]])
                if raw != item.value:
                    raise ValueError("Evidence figure differs from its original source record")
        checked[item.id] = item
    if len(set(metric_ids)) != len(metric_ids) or not set(metric_ids) <= checked.keys():
        raise ValueError("Invalid metric references")


def build_evidence(quote, snapshot, retrieved):
    info, frames = snapshot["info"], snapshot["frames"]
    validate_identity(quote, info)
    currency = info.get("financialCurrency")
    currency = currency.upper() if isinstance(currency, str) and len(currency) == 3 and currency.isascii() and currency.isalpha() else None
    base = f"https://finance.yahoo.com/quote/{urlquote(quote['symbol'], safe='.-^')}"
    paths = {"quote": ("Market quote", "/"), "statistics": ("Key statistics and company profile", "/key-statistics/"), "income": ("Income statements", "/financials/"), "quarterly": ("Quarterly income statements", "/financials/"), "balance": ("Balance sheet", "/balance-sheet/"), "cashflow": ("Cash flow statements", "/cash-flow/")}
    evidence, metrics, warnings = [], [], list(snapshot["warnings"])

    def add(label, value, unit, source, period, period_type="snapshot", end=None, currency=None, field=None, operation=None, inputs=None, formula=None, metric=False, kind="provider"):
        if value is None:
            return None
        item = AnalysisEvidence(id=f"E{len(evidence) + 1}", label=label, value=value, unit=unit, currency=currency, period=period, periodType=period_type, periodEnd=end, sourceId=source, sourceField=field, operation=operation, inputs=[raw.id for raw in inputs or []], formula=formula, kind=kind, symbol=quote["symbol"], exchange=quote["exchange"])
        evidence.append(item)
        if metric:
            metrics.append(item.id)
        return item

    def calc(label, operands, operation, formula, metric=False, period=None, period_type=None, end=None, kind="calculated"):
        if any(raw is None for raw in operands):
            return None
        first = operands[0]
        unit = "percent" if operation in ("percent_ratio", "growth", "roe", "scale_percent") else "times" if operation == "ratio" else "currency"
        try:
            value = stocks._number(_result(operation, [raw.value for raw in operands]))
            if value is None:
                return None
            item = AnalysisEvidence(id="candidate", label=label, value=round(value, 6), unit=unit, currency=first.currency if unit == "currency" else None, sourceId=first.sourceId, period=period or first.period, periodType=period_type or first.periodType, periodEnd=end or first.periodEnd, operation=operation, kind=kind)
            _check_inputs(item, operands)
        except ValueError as error:
            warnings.append(f"{label} was not calculated: {error}.")
            return None
        return add(label, item.value, unit, first.sourceId, item.period, item.periodType, item.periodEnd, item.currency, operation=operation, inputs=operands, formula=formula, metric=metric, kind=kind)

    add("Share price", stocks._number(quote.get("price")), "currency", "quote", quote.get("date") or "Quote timestamp unavailable", "quote", currency=quote["currency"], field="regularMarketPrice")
    profile = str(info.get("longBusinessSummary") or "").strip()[:2400]
    if profile:
        add("Company business description", profile, "text", "statistics", "Latest provider profile", field="longBusinessSummary")
    for field, label, unit in [("marketCap", "Market capitalization", "currency"), ("trailingPE", "Trailing P/E", "times"), ("trailingEps", "Trailing EPS", "currency")]:
        trailing = field != "marketCap"
        add(label, stocks._number(info.get(field)), unit, "statistics", "TTM (provider); exact period end unavailable" if trailing else f"Provider snapshot retrieved {retrieved.date().isoformat()}", "ttm" if trailing else "snapshot", currency=quote["currency"] if unit == "currency" else None, field=field, metric=True)
    raw_roe = add("Provider ROE ratio", stocks._number(info.get("returnOnEquity")), "number", "statistics", "TTM (provider); exact period end unavailable", "ttm", field="returnOnEquity")
    calc("Return on equity (provider)", [raw_roe], "scale_percent", "Provider returnOnEquity × 100 (unit conversion only)", kind="normalized", metric=True)

    if not currency:
        warnings.append("Financial reporting currency is missing; statement amounts and derived ratios were omitted.")
        frames = {}
    annual = _periods(frames.get("income"), retrieved)
    quarterly = _periods(frames.get("quarterly"), retrieved, 6)
    annual_rows, quarter_rows, balance_rows, cash_rows, trends = {}, {}, {}, {}, []
    for source, periods, rows, fields, basis in [
        ("income", annual, annual_rows, [("Total Revenue", "Annual revenue"), ("Net Income", "Annual net income"), ("Operating Income", "Annual operating income")], "annual"),
        ("quarterly", quarterly, quarter_rows, [("Total Revenue", "Quarterly revenue"), ("Net Income", "Quarterly net income")], "quarterly"),
        ("balance", _periods(frames.get("balance"), retrieved), balance_rows, [("Total Debt", "Total debt"), ("Cash And Cash Equivalents", "Cash and cash equivalents"), ("Stockholders Equity", "Shareholders equity"), ("Current Assets", "Current assets"), ("Current Liabilities", "Current liabilities")], "instant"),
        ("cashflow", _periods(frames.get("cashflow"), retrieved), cash_rows, [("Operating Cash Flow", "Operating cash flow"), ("Capital Expenditure", "Capital expenditure")], "annual"),
    ]:
        for index, (end, values) in enumerate(periods):
            period = f"{'Quarter' if basis == 'quarterly' else 'Balance sheet' if basis == 'instant' else 'FY'} ending {end.isoformat()}"
            row = {key: add(label if index == 0 else f"{label} ({end.isoformat()})", values.get(key), "currency", source, period, basis, end, currency, field=key) for key, label in fields}
            rows[end] = row
            if basis in ("annual", "quarterly") and source != "cashflow":
                margin = calc("Net profit margin" if source == "income" and index == 0 else "Quarterly net profit margin" if source == "quarterly" and index == 0 else f"Net profit margin ({end.isoformat()})", [row.get("Net Income"), row.get("Total Revenue")], "percent_ratio", "Same-period net income ÷ revenue × 100", metric=index == 0)
                trends.append(FinancialTrend(period=period, periodEnd=end, periodType=basis, revenueId=row.get("Total Revenue").id if row.get("Total Revenue") else None, netIncomeId=row.get("Net Income").id if row.get("Net Income") else None, netMarginId=margin.id if margin else None))
    if annual_rows:
        end = next(iter(annual_rows))
        income = annual_rows[end]
        revenue, profit = income.get("Total Revenue"), income.get("Net Income")
        calc("Operating margin", [income.get("Operating Income"), revenue], "percent_ratio", "Annual operating income ÷ annual revenue × 100", metric=True)
        previous_dates = list(annual_rows)[1:]
        if previous_dates:
            calc("Annual revenue growth", [revenue, annual_rows[previous_dates[0]].get("Total Revenue")], "growth", "(Latest annual revenue ÷ previous annual revenue − 1) × 100", metric=True, period=f"{end} vs {previous_dates[0]}", period_type="comparison")
        # Match cash flow to the income year, never blindly use the newest column.
        cash = cash_rows.get(end, {})
        fcf = calc("Free cash flow", [cash.get("Operating Cash Flow"), cash.get("Capital Expenditure")], "fcf", "Operating cash flow − absolute capital expenditure", metric=True)
        calc("Free cash flow margin", [fcf, revenue], "percent_ratio", "Free cash flow ÷ same-period annual revenue × 100", metric=True)
        current_equity = balance_rows.get(end, {}).get("Stockholders Equity")
        prior_end = next((day for day in balance_rows if 330 <= (end - day).days <= 400), None)
        prior_equity = balance_rows.get(prior_end, {}).get("Stockholders Equity")
        calc("Annual return on equity", [profit, current_equity, prior_equity], "roe", "Annual net income ÷ average of beginning/end shareholders equity × 100", metric=True)
    if balance_rows:
        balance = next(iter(balance_rows.values()))
        calc("Current ratio", [balance.get("Current Assets"), balance.get("Current Liabilities")], "ratio", "Current assets ÷ current liabilities", metric=True)
        calc("Debt to equity", [balance.get("Total Debt"), balance.get("Stockholders Equity")], "ratio", "Total debt ÷ shareholders equity", metric=True)
        calc("Net debt", [balance.get("Total Debt"), balance.get("Cash And Cash Equivalents")], "subtract", "Total debt − cash and cash equivalents; negative means net cash", metric=True)
    if len(quarter_rows) >= 4:
        rows = list(quarter_rows.values())[:4]
        last_end = next(iter(quarter_rows))
        ttm = {}
        for field, label in [("Total Revenue", "TTM revenue"), ("Net Income", "TTM net income")]:
            ttm[field] = calc(label, [row.get(field) for row in rows], "sum_quarters", "Sum of four consecutive reported quarters", period=f"TTM ending {last_end}", period_type="ttm", end=last_end)
        calc("TTM net profit margin", [ttm["Net Income"], ttm["Total Revenue"]], "percent_ratio", "Four-quarter net income ÷ four-quarter revenue × 100", metric=True)
    used = {item.sourceId for item in evidence}
    sources = [AnalysisSource(id=key, label=f"Yahoo Finance · {label}", url=base + path, retrievedAt=retrieved) for key, (label, path) in paths.items() if key in used]
    validate_evidence(evidence, metrics, sources, quote, snapshot)
    return evidence, metrics, sources, warnings, trends


def assess_quality(evidence, trends, snapshot, retrieved):
    by_label = {item.label: item for item in evidence}
    issues = []
    def issue(code, text, ids=(), severity="medium"):
        issues.append(EvidenceIssue(code=code, text=text, evidenceIds=list(ids), severity=severity))
    for warning in dict.fromkeys(snapshot["warnings"]):
        issue("missing_statement", warning)
    if not snapshot["info"].get("symbol") or not snapshot["info"].get("exchange"):
        issue("partial_identity", "The financial provider omitted part of the listing identity.")
    annual = [row for row in trends if row.periodType == "annual" and row.revenueId and row.netIncomeId]
    quarterly = [row for row in trends if row.periodType == "quarterly" and row.revenueId and row.netIncomeId]
    if len(annual) < 3:
        issue("short_annual_history", f"Only {len(annual)} complete annual periods are available; a three-year comparison is incomplete.")
    if not quarterly:
        issue("missing_quarters", "Quarterly revenue and earnings are unavailable.")
    if annual and not annual[0].netMarginId:
        issue("annual_margin_unavailable", "Annual net margin could not be computed from a positive revenue denominator.")
    if len(annual) >= 2 and "Annual revenue growth" not in by_label:
        issue("growth_unavailable", "Annual revenue growth requires comparable fiscal years and positive prior-year revenue.")
    if "Annual return on equity" not in by_label:
        issue("roe_unavailable", "Annual ROE needs matching annual net income and positive beginning/end equity; these inputs were not all available.")
    for label, rows, threshold in [("annual", annual, 550), ("quarterly", quarterly, 210)]:
        if rows and (retrieved.date() - rows[0].periodEnd).days > threshold:
            issue("stale_" + label, f"The latest {label} financial period is older than the freshness threshold.", [key for key in (rows[0].revenueId, rows[0].netIncomeId) if key])
    profit, pe, eps = (by_label.get(label) for label in ["Annual net income", "Trailing P/E", "Trailing EPS"])
    if profit and pe and profit.value < 0 < pe.value:
        issue("annual_ttm_difference", "Latest fiscal-year net income is negative while provider trailing P/E is positive. Annual and trailing figures cover different periods; the provider's exact trailing period is unavailable.", [profit.id, pe.id])
    if eps and pe and eps.value <= 0 < pe.value:
        issue("provider_earnings_conflict", "Provider trailing EPS is non-positive while trailing P/E is positive. These provider metrics cannot be reconciled from the available data.", [eps.id, pe.id], "high")
    if any(item.periodType == "ttm" and item.periodEnd is None for item in evidence):
        issue("unknown_provider_ttm_end", "Provider trailing ratios have no exact period end and cannot be directly reconciled with fiscal-year calculations.", severity="low")
    price = by_label.get("Share price")
    try:
        quote_date = datetime.fromisoformat(price.period.replace("Z", "+00:00")).date() if price else None
        if quote_date and (retrieved.date() - quote_date).days > 7:
            issue("stale_quote", "The share-price observation is more than seven days old.", [price.id])
    except ValueError:
        issue("unknown_quote_time", "The share-price observation has no verifiable timestamp.")
    if not any(item.sourceId == "income" for item in evidence):
        issue("missing_financials", "Annual financial evidence is unavailable or its reporting currency could not be verified.", severity="high")
    coverage = "limited" if not annual else "partial" if len(annual) < 3 or not quarterly or any(item.severity != "low" for item in issues) else "available"
    return EvidenceQuality(coverage=coverage, checkedCalculations=sum(item.kind == "calculated" for item in evidence), providerMetrics=sum(item.kind == "provider" and item.unit != "text" for item in evidence), annualPeriods=len(annual), quarterlyPeriods=len(quarterly), issues=issues)


def verified_findings(evidence):
    """Finite, evidence-checked assertions for NVIDIA to select and rank."""
    labels = {item.label: item for item in evidence}
    findings = {}
    def add(text, ids, sections, significance="medium"):
        key = f"F{len(findings) + 1}"
        findings[key] = {"claim": ResearchClaim(text=text, evidenceIds=ids, findingId=key, significance=significance), "sections": sections}
    for label, positive, negative, priority in [
        ("Net profit margin", "The latest fiscal-year financial statements report positive net profitability.", "The latest fiscal-year financial statements report a net loss.", "high"),
        ("TTM net profit margin", "The four consecutive reported quarters together show positive net profitability.", "The four consecutive reported quarters together show an aggregate net loss.", "high"),
        ("Annual revenue growth", "Revenue increased between the two comparable reported fiscal years.", "Revenue declined between the two comparable reported fiscal years.", "high"),
        ("Free cash flow", "Operating cash flow exceeded absolute capital expenditure in the reported fiscal year.", "Operating cash flow did not cover absolute capital expenditure in the reported fiscal year.", "high"),
        ("Annual return on equity", "Annual net income generated a positive return on average beginning and ending shareholders equity.", "Annual net income generated a negative return on average beginning and ending shareholders equity.", "medium"),
    ]:
        item = labels.get(label)
        if item and item.value != 0:
            add(positive if item.value > 0 else negative, [item.id], ["summary", "strengths" if item.value > 0 else "risks"], priority)
            add(f"Monitor whether the direction of {label.lower()} persists in subsequent comparable reporting periods.", [item.id], ["watchItems"], priority)
    current = labels.get("Current ratio")
    if current and current.value < 1:
        add("Reported current liabilities exceed current assets. The liquidity implications depend on the company's business and funding arrangements.", [current.id], ["risks"], "high")
    net_debt = labels.get("Net debt")
    if net_debt and net_debt.value < 0:
        add("Reported cash and cash equivalents exceed total debt at the balance-sheet date.", [net_debt.id], ["strengths"], "medium")
    profit, pe = labels.get("Annual net income"), labels.get("Trailing P/E")
    if profit and pe and profit.value < 0 < pe.value:
        add("Annual net income is negative while provider trailing valuation is positive; different earnings periods prevent a direct comparison.", [profit.id, pe.id], ["summary", "risks", "watchItems"], "high")
    price = labels.get("Share price")
    if price and not any("summary" in item["sections"] for item in findings.values()):
        add("The report includes the latest available share-price observation for this listing; financial trend conclusions require further statement data.", [price.id], ["summary"], "low")
    return findings
