"""Sentiment panel — VADER by default, Claude 'Deep Analyze' on demand."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.config import INSTRUMENTS, has_anthropic
from app.data_sources import news
from app.sentiment import deep, vader


def _color_for(label: str) -> str:
    return {
        "bullish": "#26a69a",
        "bearish": "#ef5350",
        "mixed": "#ffa726",
        "neutral": "#90a4ae",
    }.get(label, "#90a4ae")


@st.cache_data(ttl=180, show_spinner=False)
def _compute_vader(symbol: str) -> dict:
    all_items = news.fetch_all()
    filtered = news.filter_by_symbol(all_items, symbol)
    # If filter is too aggressive, fall back to top N general headlines.
    items = filtered if len(filtered) >= 5 else all_items[:30]
    texts = [f"{i.title}. {i.summary}" for i in items[:60]]
    scores = vader.score_many(texts)
    agg = vader.aggregate(scores)
    return {
        "compound": agg.compound,
        "positive": agg.positive,
        "neutral": agg.neutral,
        "negative": agg.negative,
        "label": agg.label,
        "n_items": len(items),
        "sample_titles": [i.title for i in items[:8]],
        "computed_at": datetime.utcnow().isoformat(),
    }


def render(symbol: str) -> None:
    inst = INSTRUMENTS[symbol]
    st.subheader("Sentiment")

    try:
        v = _compute_vader(symbol)
    except Exception as e:
        st.error(f"VADER sentiment failed: {e}")
        return

    cols = st.columns([1, 1, 1, 2])
    label = v["label"]
    color = _color_for(label)
    cols[0].markdown(
        f"<div style='padding:12px;border-radius:8px;background:{color};text-align:center;"
        f"color:#fff;font-weight:600;font-size:18px'>{label.upper()}</div>",
        unsafe_allow_html=True,
    )
    cols[1].metric("Compound", f"{v['compound']:+.3f}")
    cols[2].metric("Headlines", v["n_items"])
    cols[3].progress(
        max(0.0, min(1.0, (v["compound"] + 1) / 2)),
        text=f"pos {v['positive']:.2f} / neu {v['neutral']:.2f} / neg {v['negative']:.2f}",
    )

    with st.expander("Sample headlines scored"):
        for t in v["sample_titles"]:
            st.caption(f"• {t}")

    st.divider()
    st.markdown("**Deep Analyze** — Claude-powered thesis + drivers")
    if not has_anthropic():
        st.caption("Add `ANTHROPIC_API_KEY` to `.env` to enable. Uses Claude Sonnet 4.5.")
    btn_disabled = not has_anthropic()
    if st.button("Run Deep Analyze", key=f"deep_{symbol}", disabled=btn_disabled, type="primary"):
        with st.spinner("Asking Claude…"):
            items = news.filter_by_symbol(news.fetch_all(), symbol)[:30]
            headlines = [i.title for i in items if i.title]
            analysis = deep.analyze(symbol, inst.name, headlines)
        st.session_state[f"deep_result_{symbol}"] = {
            "label": analysis.label,
            "markdown": analysis.markdown,
            "at": datetime.utcnow().isoformat(),
        }

    result = st.session_state.get(f"deep_result_{symbol}")
    if result:
        st.markdown(f"**Verdict:** `{result['label']}` · _{result['at']}_")
        st.markdown(result["markdown"])
