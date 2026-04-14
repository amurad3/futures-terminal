"""Reddit social feed panel."""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from app.config import has_reddit
from app.data_sources import reddit as rd


@st.cache_data(ttl=300, show_spinner=False)
def _cached_fetch() -> list[dict]:
    return [p.as_dict() for p in rd.fetch_hot()]


def _ago(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    mins = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
    if mins < 60:
        return f"{mins}m"
    if mins < 60 * 24:
        return f"{mins // 60}h"
    return f"{mins // (60 * 24)}d"


def render(symbol: str) -> None:
    st.subheader("Social (Reddit)")
    if not has_reddit():
        st.caption(
            "Disabled. Add `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` to `.env`. "
            "Create an app at https://www.reddit.com/prefs/apps (type: script)."
        )
        return

    cols = st.columns([1, 1, 2])
    filtered = cols[0].toggle("Filter by instrument", value=True, key=f"rd_filter_{symbol}")
    limit = cols[1].number_input("Max posts", 10, 100, 30, step=5, key=f"rd_limit_{symbol}")
    if cols[2].button("Reload social", key=f"rd_reload_{symbol}"):
        _cached_fetch.clear()

    try:
        posts = _cached_fetch()
    except Exception as e:
        st.error(f"Reddit fetch failed: {e}")
        return

    if filtered:
        from app.data_sources.reddit import RedditPost

        objs = [
            RedditPost(
                subreddit=p["subreddit"], title=p["title"], selftext=p["selftext"],
                url=p["url"], permalink=p["permalink"], score=p["score"],
                num_comments=p["num_comments"],
                created=datetime.fromisoformat(p["created"]),
            )
            for p in posts
        ]
        posts = [p.as_dict() for p in rd.filter_by_symbol(objs, symbol)]

    posts = posts[: int(limit)]
    if not posts:
        st.info("No posts matched the filter.")
        return

    for p in posts:
        with st.container(border=True):
            top = st.columns([5, 1])
            top[0].markdown(f"**[{p['title']}]({p['permalink']})**")
            top[1].caption(f"{_ago(p['created'])} · r/{p['subreddit']}")
            st.caption(f"↑ {p['score']:,} · 💬 {p['num_comments']:,}")
            if p["selftext"]:
                body = p["selftext"]
                if len(body) > 280:
                    body = body[:280].rstrip() + "…"
                st.write(body)
