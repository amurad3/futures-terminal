"""Futures Terminal — Streamlit entry point.

Run: streamlit run app/main.py
"""
from __future__ import annotations

import streamlit as st

from app.config import INSTRUMENTS
from app.ui import chart_panel

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
    st.sidebar.caption("Panels are loaded lazily. Data sources are free/open.")
    return symbol


def main() -> None:
    symbol = sidebar()
    inst = INSTRUMENTS[symbol]

    st.title(f"{inst.symbol} — {inst.name}")

    chart_panel.render(symbol)

    st.divider()
    st.caption("News, positioning, macro, and sentiment panels coming next.")


if __name__ == "__main__":
    main()
