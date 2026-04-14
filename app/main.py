"""Futures Terminal — Streamlit entry point.

Run: streamlit run app/main.py
"""
from __future__ import annotations

import streamlit as st

from app.config import INSTRUMENTS, has_anthropic, has_reddit, has_fred
from app.ui import (
    chart_panel,
    cot_panel,
    macro_panel,
    news_panel,
    sentiment_panel,
    social_panel,
)

st.set_page_config(
    page_title="Futures Terminal",
    page_icon="FT",
    layout="wide",
    initial_sidebar_state="expanded",
)


def sidebar() -> str:
    st.sidebar.title("Futures Terminal")
    st.sidebar.caption("Open-source market terminal")
    symbol = st.sidebar.selectbox(
        "Instrument",
        list(INSTRUMENTS.keys()),
        format_func=lambda s: f"{s} — {INSTRUMENTS[s].name}",
    )
    st.sidebar.divider()
    st.sidebar.caption("**Integrations**")
    st.sidebar.write(f"- Claude (Deep Analyze): {'✅' if has_anthropic() else '⚠ missing key'}")
    st.sidebar.write(f"- Reddit: {'✅' if has_reddit() else '⚠ missing keys'}")
    st.sidebar.write(f"- FRED: {'✅ keyed' if has_fred() else '◌ using no-key CSV'}")
    st.sidebar.divider()
    st.sidebar.caption("All price/news/CFTC sources are free. Add keys in `.env` for Reddit + Claude deep analysis.")
    return symbol


def main() -> None:
    symbol = sidebar()
    inst = INSTRUMENTS[symbol]

    st.title(f"{inst.symbol} — {inst.name}")

    tabs = st.tabs(["📊 Overview", "📰 News", "💬 Social", "🏦 Positioning", "🌐 Macro"])

    with tabs[0]:
        sentiment_panel.render(symbol)
        st.divider()
        chart_panel.render(symbol)

    with tabs[1]:
        news_panel.render(symbol)

    with tabs[2]:
        social_panel.render(symbol)

    with tabs[3]:
        cot_panel.render(symbol)

    with tabs[4]:
        macro_panel.render()


if __name__ == "__main__":
    main()
