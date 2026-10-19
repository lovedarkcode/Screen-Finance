"""Linked market headlines from Yahoo Finance's public RSS feeds."""
import asyncio
import hashlib
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from time import time
from urllib.parse import urldefrag, urlsplit
from xml.etree import ElementTree

import httpx
from fastapi import HTTPException

from app.api.v1.stocks import _normalize_symbol
from app.core.cache import cache_get, cache_set

FEED_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"
FRESH_SECONDS = 300
STALE_SECONDS = 3600
_local = {}


def parse_feed(content: bytes) -> list[dict]:
    if len(content) > 2_000_000:
        raise ValueError("News feed exceeds size limit")
    root = ElementTree.fromstring(content)
    if root.tag != "rss":
        raise ValueError("Unexpected news feed format")
    items = []
    for item in root.findall("./channel/item"):
        title = unescape((item.findtext("title") or "").strip())
        url = urldefrag((item.findtext("link") or "").strip())[0]
        parsed = urlsplit(url)
        if not title or parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password:
            continue
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "")
            published = published.replace(tzinfo=UTC) if published.tzinfo is None else published
            published = published.astimezone(UTC).isoformat()
        except (TypeError, ValueError, OverflowError):
            published = None
        items.append({"id": hashlib.sha256(url.encode()).hexdigest()[:20],
                      "title": title, "url": url, "source": "Yahoo Finance",
                      "published_at": published})
    return items


async def fetch_feed(client: httpx.AsyncClient, symbol: str) -> list[dict]:
    indian = symbol.endswith((".NS", ".BO")) or symbol in ("^NSEI", "^NSEBANK", "^BSESN", "^CNXIT")
    response = await client.get(FEED_URL, params={"s": symbol, "region": "IN" if indian else "US", "lang": "en-IN" if indian else "en-US"})
    response.raise_for_status()
    return parse_feed(response.content)


async def market_news(symbol: str | None, limit: int) -> dict:
    symbol = _normalize_symbol(symbol) if symbol else None
    key = "news:v1:" + (symbol or "markets")
    saved = _local.get(key)
    try:
        shared = await asyncio.wait_for(cache_get(key), .3)
        if shared:
            saved = shared
    except Exception:
        pass
    now = time()
    if saved and now - saved["fetched_at"] < FRESH_SECONDS:
        return {**saved, "items": saved["items"][:limit], "symbol": symbol, "limit": limit, "cached": True, "stale": False}
    async with httpx.AsyncClient(timeout=8, follow_redirects=True, headers={"User-Agent": "ScreenFinance/1.0 RSS reader"}) as client:
        results = await asyncio.gather(*(fetch_feed(client, ticker) for ticker in ([symbol] if symbol else ["^NSEI", "^GSPC"])), return_exceptions=True)
    successful = [result for result in results if isinstance(result, list)]
    if not successful:
        if saved and now - saved["fetched_at"] < STALE_SECONDS:
            return {**saved, "items": saved["items"][:limit], "symbol": symbol, "limit": limit, "cached": True, "stale": True}
        raise HTTPException(503, "Market news is temporarily unavailable. Please retry.")
    unique, titles = {}, set()
    for item in (item for result in successful for item in result):
        if item["url"] not in unique and item["title"].casefold() not in titles:
            unique[item["url"]] = item
            titles.add(item["title"].casefold())
    items = sorted(unique.values(), key=lambda item: item["published_at"] or "", reverse=True)[:50]
    saved = {"items": items, "fetched_at": now, "updated_at": datetime.fromtimestamp(now, UTC).isoformat(), "partial": len(successful) < len(results)}
    if items:
        if len(_local) >= 64:
            _local.pop(next(iter(_local)))
        _local[key] = saved
        try:
            await asyncio.wait_for(cache_set(key, saved, ttl=STALE_SECONDS), .3)
        except Exception:
            pass
    return {**saved, "items": items[:limit], "symbol": symbol, "limit": limit, "cached": False, "stale": False}
