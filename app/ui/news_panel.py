"""News feed panel."""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from app.data_sources import news


@st.cache_data(ttl=180, show_spinner=False)
def _cached_fetch_all() -> list[dict]:
    return [i.as_dict() for i in news.fetch_all()]


def _humanize(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    now = datetime.now(timezone.utc)
    delta = now - dt
    mins = int(delta.total_seconds() // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def render(symbol: str) -> None:
    st.subheader("News")
    cols = st.columns([1, 1, 3])
    filtered = cols[0].toggle("Filter by instrument", value=True, key=f"news_filter_{symbol}")
    limit = cols[1].number_input("Max items", min_value=10, max_value=200, value=40, step=10, key=f"news_limit_{symbol}")
    if cols[2].button("Reload news", key=f"news_reload_{symbol}"):
        _cached_fetch_all.clear()

    try:
        items = _cached_fetch_all()
    except Exception as e:
        st.error(f"Failed to fetch news: {e}")
        return

    if filtered:
        # Reuse the filter logic on dicts by constructing lightweight objects
        from app.data_sources.news import NewsItem

        news_items = [
            NewsItem(
                source=d["source"],
                title=d["title"],
                link=d["link"],
                summary=d["summary"],
                published=datetime.fromisoformat(d["published"]) if d["published"] else None,
            )
            for d in items
        ]
        news_items = news.filter_by_symbol(news_items, symbol)
        items = [i.as_dict() for i in news_items]

    items = items[: int(limit)]
    if not items:
        st.info("No headlines matched. Turn off filtering to see everything.")
        return

    for it in items:
        with st.container(border=True):
            top = st.columns([5, 1])
            top[0].markdown(f"**[{it['title']}]({it['link']})**" if it["link"] else f"**{it['title']}**")
            top[1].caption(_humanize(it["published"]))
            st.caption(f"{it['source']}")
            if it["summary"]:
                summary = it["summary"]
                # RSS summaries are often HTML. Strip crudely.
                import re
                clean = re.sub(r"<[^>]+>", "", summary)
                if len(clean) > 320:
                    clean = clean[:320].rstrip() + "…"
                st.write(clean)
