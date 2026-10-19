from datetime import UTC, datetime
from xml.etree import ElementTree
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import news_service as news

client = TestClient(app)


def article(title='Market headline', url='https://finance.yahoo.com/news/test', date='Mon, 19 Oct 2026 08:00:00 GMT'):
    return f'<item><title>{title}</title><link>{url}</link><pubDate>{date}</pubDate></item>'


def feed(*items):
    return ('<rss><channel>' + ''.join(items) + '</channel></rss>').encode()


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    news._local.clear()
    async def missing(*args, **kwargs):
        return None
    monkeypatch.setattr(news, 'cache_get', missing)
    monkeypatch.setattr(news, 'cache_set', missing)
    yield
    news._local.clear()


def test_parser_handles_dates_and_rejects_unsafe_links():
    rows = news.parse_feed(feed(article('Profit &amp; growth'), article(url='javascript:alert(1)'), article(title=''), article(url='https://user:secret@example.com'), article(url='https://example.com/unknown', date='not a date')))
    assert len(rows) == 2
    assert rows[0]['title'] == 'Profit & growth'
    assert rows[0]['published_at'] == '2026-10-19T08:00:00+00:00'
    assert rows[1]['published_at'] is None
    assert rows[0]['source'] == 'Yahoo Finance'
    with pytest.raises(ElementTree.ParseError):
        news.parse_feed(b'<rss>')
    with pytest.raises(ValueError):
        news.parse_feed(b'<html/>')


def test_api_combines_deduplicates_sorts_and_caches(monkeypatch):
    calls = []
    async def provider(client, symbol):
        calls.append(symbol)
        return news.parse_feed(feed(article(), article(title='Older headline', url='https://example.com/older', date='Sun, 18 Oct 2026 08:00:00 GMT')))
    monkeypatch.setattr(news, 'fetch_feed', provider)
    response = client.get('/api/v1/news?limit=1')
    assert response.status_code == 200
    assert response.json()['items'][0]['title'] == 'Market headline'
    assert set(calls) == {'^NSEI', '^GSPC'}
    cached = client.get('/api/v1/news?limit=6').json()
    assert cached['cached'] and len(cached['items']) == 2
    assert len(calls) == 2
    assert len(client.get('/api/v1/news/trending').json()['items']) == 2


def test_symbol_normalization_limits_and_partial_feed(monkeypatch):
    async def provider(client, symbol):
        if symbol == '^NSEI':
            raise httpx.ConnectError('offline')
        assert symbol in ('^GSPC', 'AAPL')
        return news.parse_feed(feed(article()))
    monkeypatch.setattr(news, 'fetch_feed', provider)
    assert client.get('/api/v1/news').json()['partial']
    assert client.get('/api/v1/news?symbol=aapl').json()['symbol'] == 'AAPL'
    assert client.get('/api/v1/news?limit=0').status_code == 422
    assert client.get('/api/v1/news?limit=51').status_code == 422
    assert client.get('/api/v1/news?symbol=https://bad.example').status_code == 400


def test_provider_failure_returns_bounded_stale_cache_then_error(monkeypatch):
    async def offline(*args):
        raise httpx.ConnectError('offline')
    monkeypatch.setattr(news, 'fetch_feed', offline)
    now = datetime.now(UTC).timestamp()
    news._local['news:v1:markets'] = {'items': news.parse_feed(feed(article())), 'fetched_at':now-600, 'updated_at':datetime.now(UTC).isoformat(), 'partial':False}
    response = client.get('/api/v1/news').json()
    assert response['stale'] and response['cached'] and response['items']
    news._local['news:v1:markets']['fetched_at'] = now-4000
    response = client.get('/api/v1/news')
    assert response.status_code == 503
    assert 'offline' not in response.text


def test_successful_empty_feed_is_not_a_provider_error(monkeypatch):
    async def empty(*args):
        return []
    monkeypatch.setattr(news, 'fetch_feed', empty)
    response = client.get('/api/v1/news')
    assert response.status_code == 200 and response.json()['items'] == []
