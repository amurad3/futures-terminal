"""Reddit social feed — optional, requires free API credentials.

Create an app at https://www.reddit.com/prefs/apps (type: script) and
put client_id / client_secret in .env. No username/password needed for
read-only access.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from app.config import (
    INSTRUMENTS,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    has_reddit,
)

SUBREDDITS = ["FuturesTrading", "wallstreetbets", "stocks", "investing", "options", "Daytrading", "Commodities"]


@dataclass
class RedditPost:
    subreddit: str
    title: str
    selftext: str
    url: str
    permalink: str
    score: int
    num_comments: int
    created: datetime

    def as_dict(self) -> dict:
        return {
            "subreddit": self.subreddit,
            "title": self.title,
            "selftext": self.selftext,
            "url": self.url,
            "permalink": self.permalink,
            "score": self.score,
            "num_comments": self.num_comments,
            "created": self.created.isoformat(),
        }


def fetch_hot(limit_per_sub: int = 25) -> list[RedditPost]:
    if not has_reddit():
        return []
    import praw  # local import so the app starts without praw configured

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
        check_for_async=False,
    )
    reddit.read_only = True

    out: list[RedditPost] = []
    for sub in SUBREDDITS:
        try:
            for post in reddit.subreddit(sub).hot(limit=limit_per_sub):
                out.append(RedditPost(
                    subreddit=sub,
                    title=str(post.title or ""),
                    selftext=str(post.selftext or "")[:500],
                    url=str(post.url or ""),
                    permalink=f"https://reddit.com{post.permalink}",
                    score=int(post.score or 0),
                    num_comments=int(post.num_comments or 0),
                    created=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                ))
        except Exception:
            continue
    out.sort(key=lambda p: p.created, reverse=True)
    return out


def filter_by_symbol(posts: Iterable[RedditPost], symbol: str) -> list[RedditPost]:
    inst = INSTRUMENTS.get(symbol)
    if inst is None:
        return list(posts)
    needles = [k.lower() for k in inst.keywords] + [symbol.lower(), f"${symbol.lower()}"]
    out: list[RedditPost] = []
    for p in posts:
        hay = f"{p.title} {p.selftext}".lower()
        if any(n in hay for n in needles):
            out.append(p)
    return out
