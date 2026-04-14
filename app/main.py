"""Futures Terminal — Streamlit entry point.

Run: streamlit run app/main.py
"""
from __future__ import annotations

import streamlit as st

from app.config import INSTRUMENTS

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
    st.caption("Scaffold in progress. Panels will appear here as data sources are wired up.")

    cols = st.columns(3)
    cols[0].metric("Price", "—")
    cols[1].metric("Change", "—")
    cols[2].metric("Volume", "—")

    st.info("Next: price chart panel, news feed, CFTC positioning, sentiment.")


if __name__ == "__main__":
    main()
