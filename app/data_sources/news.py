"""News aggregator from public RSS feeds.

All sources are free and require no API keys. We fetch, normalize, and
optionally filter headlines by instrument keywords.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import feedparser

from app.config import INSTRUMENTS


# Curated list of finance/macro RSS feeds. Keep conservative — some feeds
# rate-limit or break; we tolerate failures silently per-feed.
FEEDS: list[tuple[str, str]] = [
    ("Reuters Business", "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"),
    ("CNBC Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("CNBC Markets", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("CNBC Economy", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("Investing.com News", "https://www.investing.com/rss/news.rss"),
    ("Investing.com Commodities", "https://www.investing.com/rss/news_11.rss"),
    ("MarketWatch Top", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("MarketWatch Markets", "https://feeds.content.dowjones.io/public/rss/mw_marketpulse"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("FT Markets", "https://www.ft.com/markets?format=rss"),
    ("ZeroHedge", "https://feeds.feedburner.com/zerohedge/feed"),
    ("Bloomberg Markets (Google proxy)", "https://news.google.com/rss/search?q=when:24h+allinurl:bloomberg.com/news/articles&hl=en-US&gl=US&ceid=US:en"),
]


@dataclass
class NewsItem:
    source: str
    title: str
    link: str
    summary: str
    published: datetime | None

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "published": self.published.isoformat() if self.published else None,
        }


def _parse_time(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        t = getattr(entry, key, None) or (entry.get(key) if isinstance(entry, dict) else None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


def fetch_feed(name: str, url: str, limit: int = 30) -> list[NewsItem]:
    try:
        parsed = feedparser.parse(url)
    except Exception:
        return []
    items: list[NewsItem] = []
    for entry in (parsed.entries or [])[:limit]:
        items.append(
            NewsItem(
                source=name,
                title=(entry.get("title") or "").strip(),
                link=(entry.get("link") or "").strip(),
                summary=(entry.get("summary") or entry.get("description") or "").strip(),
                published=_parse_time(entry),
            )
        )
    return items


def fetch_all(limit_per_feed: int = 20) -> list[NewsItem]:
    out: list[NewsItem] = []
    for name, url in FEEDS:
        out.extend(fetch_feed(name, url, limit=limit_per_feed))
    # Newest first; items without dates go last.
    out.sort(key=lambda i: i.published or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return out


def filter_by_symbol(items: Iterable[NewsItem], symbol: str) -> list[NewsItem]:
    inst = INSTRUMENTS.get(symbol)
    if inst is None:
        return list(items)
    needles = [k.lower() for k in inst.keywords]
    out: list[NewsItem] = []
    for it in items:
        hay = f"{it.title} {it.summary}".lower()
        if any(n in hay for n in needles):
            out.append(it)
    return out
