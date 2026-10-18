"""Adversarial checks for company context, raw figures and calculated evidence."""
import asyncio
import json
from datetime import UTC, datetime

import pandas as pd
import pytest
from fastapi import HTTPException

from app.services.ai import financial_evidence as engine
from app.services.ai import stock_analysis_service as agent
from app.tests.test_stock_analysis import NOW, QUOTE, snapshot


def full_snapshot():
    data = snapshot()
    data["info"].update(returnOnEquity=.2221, trailingEps=10)
    data["frames"]["income"] = pd.DataFrame({pd.Timestamp(f"{year}-12-31"): {"Total Revenue": revenue, "Net Income": revenue / 5, "Operating Income": revenue / 4} for year, revenue in [(2025, 200), (2024, 150), (2023, 100), (2022, 80)]})
    data["frames"]["balance"][pd.Timestamp("2024-12-31")] = {"Stockholders Equity": 30}
    data["frames"]["quarterly"] = pd.DataFrame({pd.Timestamp(day): {"Total Revenue": 60, "Net Income": 6} for day in ["2026-06-30", "2026-03-31", "2025-12-31", "2025-09-30", "2025-06-30"]})
    return data


def bundle(data=None):
    return engine.build_evidence(QUOTE, data or full_snapshot(), NOW)


def test_roe_is_recomputed_from_average_equity_and_provider_conversion_is_distinct():
    evidence, _, _, _, trends = bundle()
    labels = {item.label: item for item in evidence}
    annual = labels["Annual return on equity"]
    provider = labels["Return on equity (provider)"]
    assert annual.value == 100 and annual.operation == "roe" and annual.kind == "calculated"
    assert annual.periodType == "annual" and annual.periodEnd.isoformat() == "2025-12-31" and len(annual.inputs) == 3
    assert provider.value == 22.21 and provider.kind == "normalized" and provider.periodEnd is None
    assert labels["TTM net profit margin"].value == 10
    assert labels["TTM net profit margin"].periodEnd.isoformat() == "2026-06-30"
    assert len([row for row in trends if row.periodType == "annual"]) == 4
    assert len([row for row in trends if row.periodType == "quarterly"]) == 5


@pytest.mark.parametrize("field,value", [("symbol", "NVDA"), ("exchange", "NYQ")])
def test_other_company_or_exchange_is_rejected(field, value):
    data = full_snapshot()
    data["info"][field] = value
    with pytest.raises(ValueError):
        bundle(data)


@pytest.mark.parametrize("mutation", ["figure", "raw", "currency", "period", "source", "cycle", "identity", "source_url", "metric"])
def test_tampered_evidence_fails_independent_validation(mutation):
    data = full_snapshot()
    evidence, metrics, sources, _, _ = bundle(data)
    by_label = {item.label: item for item in evidence}
    margin = by_label["Net profit margin"]
    if mutation == "figure":
        margin.value += 1
    elif mutation == "raw":
        by_label["Annual revenue"].value += 1
    elif mutation == "currency":
        by_label["Annual revenue"].currency = "INR"
    elif mutation == "period":
        margin.periodEnd = datetime(2024, 12, 31).date()
    elif mutation == "source":
        margin.sourceId = "unregistered"
    elif mutation == "cycle":
        margin.inputs = [margin.id, margin.id]
    elif mutation == "identity":
        margin.symbol = "NVDA"
    elif mutation == "source_url":
        sources[0].url = "https://finance.yahoo.com/quote/NVDA/"
    elif mutation == "metric":
        metrics.append("E999")
    with pytest.raises(ValueError):
        engine.validate_evidence(evidence, metrics, sources, QUOTE, data)


def test_quarter_gaps_and_missing_equity_never_manufacture_ttm_or_roe():
    data = full_snapshot()
    data["frames"]["quarterly"] = data["frames"]["quarterly"].drop(columns=pd.Timestamp("2026-03-31"))
    data["frames"]["balance"].loc["Stockholders Equity", pd.Timestamp("2024-12-31")] = -30
    evidence, _, _, warnings, _ = bundle(data)
    labels = {item.label for item in evidence}
    assert "TTM net profit margin" not in labels and "Annual return on equity" not in labels
    assert any("consecutive quarters" in warning for warning in warnings)


def test_annual_ttm_difference_and_provider_conflict_are_distinct_issues():
    data = full_snapshot()
    data["frames"]["income"].loc["Net Income", pd.Timestamp("2025-12-31")] = -10
    evidence, _, _, _, trends = bundle(data)
    quality = engine.assess_quality(evidence, trends, data, NOW)
    codes = {issue.code for issue in quality.issues}
    assert "annual_ttm_difference" in codes and "provider_earnings_conflict" not in codes
    data["info"]["trailingEps"] = -1
    evidence, _, _, _, trends = bundle(data)
    quality = engine.assess_quality(evidence, trends, data, NOW)
    assert next(issue for issue in quality.issues if issue.code == "provider_earnings_conflict").severity == "high"


def test_stale_data_and_available_history_counts_are_honest():
    data = full_snapshot()
    evidence, _, _, _, trends = bundle(data)
    quality = engine.assess_quality(evidence, trends, data, NOW)
    assert quality.annualPeriods == 4 and quality.quarterlyPeriods == 5 and quality.coverage == "available"
    assert quality.checkedCalculations > 0
    late = engine.assess_quality(evidence, trends, data, datetime(2028, 1, 1, tzinfo=UTC))
    assert {"stale_annual", "stale_quarterly", "stale_quote"} <= {issue.code for issue in late.issues}
    assert late.coverage == "partial"


def test_financial_findings_are_only_selected_from_verified_assertions():
    evidence, *_ = bundle()
    findings = engine.verified_findings(evidence)
    annual_profit = next(key for key, value in findings.items() if "latest fiscal-year" in value["claim"].text)
    selection = {"summary": [annual_profit], "strengths": [annual_profit], "risks": [], "watchItems": []}
    draft = agent._validate_research(json.dumps(selection), evidence)
    assert draft.strengths[0] == findings[annual_profit]["claim"]
    assert draft.strengths[0].significance == "high"
    selection["risks"] = [annual_profit]
    with pytest.raises(ValueError):
        agent._validate_research(json.dumps(selection), evidence)


def test_invalid_evidence_stops_before_nvidia_and_run_context_is_bound(monkeypatch):
    calls = []
    data = full_snapshot()
    monkeypatch.setattr(agent, "_load_financials", lambda symbol: data)
    async def nvidia(context, evidence):
        calls.append(context)
        return agent._validate_research(json.dumps({"summary": ["F1"], "strengths": [], "risks": [], "watchItems": []}), evidence)
    monkeypatch.setattr(agent, "_nvidia_research", nvidia)
    data["info"]["symbol"] = "NVDA"
    with pytest.raises(HTTPException) as error:
        asyncio.run(agent._create_report(QUOTE))
    assert error.value.status_code == 502 and not calls
    data["info"]["symbol"] = "AAPL"
    result = asyncio.run(agent._create_report(QUOTE))
    assert result.companyId == "NASDAQ:AAPL" and calls[0]["analysisRunId"] == result.analysisRunId
    assert result.symbol == "AAPL" and result.quality.annualPeriods == 4


def test_quote_identity_is_checked_before_financial_retrieval(monkeypatch):
    async def wrong_quote(symbol):
        return {**QUOTE, "symbol": "NVDA"}
    monkeypatch.setattr(agent.stocks, "get_stock", wrong_quote)
    with pytest.raises(HTTPException) as error:
        asyncio.run(agent._resolve_quote("AAPL"))
    assert error.value.status_code == 502
