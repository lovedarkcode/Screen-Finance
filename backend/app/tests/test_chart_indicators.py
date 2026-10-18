"""Daily averages must include lookback and must not use intraday future closes."""
import httpx
from app.tests.test_stock_detail import client
from app.api.v1 import stocks
from app.dependencies import get_db
from app.main import app
from datetime import UTC, datetime


def feed(stamps, closes):
    return {"chart": {"result": [{"timestamp": stamps, "indicators": {"quote": [{"close": closes}]}}]}}


def test_daily_lookback_and_long_ranges(monkeypatch):
    base = 1700006400
    calls = []
    async def provider(url, params):
        calls.append(params)
        if "period1" in params:
            return feed([base + i * 86400 for i in range(101)], list(range(1, 102)))
        return feed([base + 99 * 86400, base + 100 * 86400], [100, 101])
    monkeypatch.setattr(stocks, "_get_json", provider)
    rows = client.get('/api/v1/stocks/TEST.NS/chart?range=5Y&indicators=true').json()
    assert calls[0]['interval'] == '1d'
    assert calls[1]['period1'] < base
    assert rows[0]['dma50'] == 75.5
    assert rows[0]['dma100'] == 50.5
    assert rows[1]['dma100'] == 51.5


def test_intraday_excludes_current_session_close(monkeypatch):
    base = 1700006400
    async def provider(url, params):
        if "period1" in params:
            return feed([base + i * 86400 for i in range(101)], [10] * 100 + [10000])
        return feed([base + 100 * 86400 + 3600], [15])
    monkeypatch.setattr(stocks, "_get_json", provider)
    row = client.get('/api/v1/stocks/TEST.NS/chart?range=1D&indicators=true').json()[0]
    assert row['dma50'] == row['dma100'] == 10


def test_insufficient_history_and_feed_failure(monkeypatch):
    async def provider(url, params):
        return feed([1700006400], [10])
    monkeypatch.setattr(stocks, "_get_json", provider)
    row = client.get('/api/v1/stocks/TEST.NS/chart?indicators=true').json()[0]
    assert row['dma50'] is None and row['dma100'] is None
    async def failing(url, params):
        if 'period1' in params:
            raise httpx.ConnectError('offline')
        return feed([1700006400], [10])
    monkeypatch.setattr(stocks, "_get_json", failing)
    row = client.get('/api/v1/stocks/TEST.NS/chart?indicators=true').json()[0]
    assert row['price'] == 10 and row.get('dma50') is None


def test_pe_snapshots_use_observation_dates_and_exclude_invalid_values():
    class DB:
        async def execute(self, query):
            sql = str(query)
            assert 'financials.updated_at' in sql and 'stocks.symbol' in sql
            return [(datetime(2026, 10, 18, tzinfo=UTC), 20),
                    (datetime(2026, 10, 18, tzinfo=UTC), float('nan'))]
    async def database():
        yield DB()
    app.dependency_overrides[get_db] = database
    try:
        response = client.get('/api/v1/stocks/TEST.NS/pe-history')
        assert response.status_code == 200
        assert response.json() == [{'date': '2026-10-18T00:00:00+00:00', 'pe': 20}]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_three_year_range_uses_explicit_dates(monkeypatch):
    async def provider(url, params):
        assert 'range' not in params
        assert abs(params['period2'] - params['period1'] - 3 * 365.25 * 86400) <= 1
        return feed([], [])
    monkeypatch.setattr(stocks, '_get_json', provider)
    assert client.get('/api/v1/stocks/TEST.NS/chart?range=3Y').status_code == 200
