"""Price chart panel — candlesticks with volume."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app.data_sources.prices import fetch_history_cached, fetch_quote


INTERVAL_OPTIONS = ["5m", "15m", "30m", "60m", "1d"]


def render(symbol: str) -> None:
    st.subheader("Price")
    cols = st.columns([1, 1, 2])
    interval = cols[0].selectbox("Interval", INTERVAL_OPTIONS, index=1, key=f"int_{symbol}")
    period = cols[1].selectbox(
        "Period",
        ["5d", "1mo", "3mo", "6mo", "1y"],
        index=1,
        key=f"per_{symbol}",
    )
    refresh = cols[2].button("Refresh", key=f"refresh_{symbol}")
    if refresh:
        # Bust the cache by touching session state
        st.cache_data.clear() if hasattr(st, "cache_data") else None

    try:
        df = fetch_history_cached(symbol, interval=interval, period=period, ttl_seconds=60)
        quote = fetch_quote(symbol)
    except Exception as e:
        st.error(f"Failed to fetch price data: {e}")
        return

    if df is None or df.empty:
        st.warning("No data returned from Yahoo Finance.")
        return

    # Quote strip
    q_cols = st.columns(4)
    price = quote.get("price")
    chg = quote.get("change")
    chg_pct = quote.get("change_pct")
    vol = quote.get("volume")
    q_cols[0].metric("Last", f"{price:,.2f}" if price is not None else "—")
    q_cols[1].metric(
        "Day change",
        f"{chg:+,.2f}" if chg is not None else "—",
        f"{chg_pct:+.2f}%" if chg_pct is not None else None,
    )
    q_cols[2].metric("Volume", f"{vol:,.0f}" if vol else "—")
    q_cols[3].metric("Bars", f"{len(df):,}")

    fig = _build_chart(df, symbol)
    st.plotly_chart(fig, use_container_width=True)


def _build_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            name=symbol,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )
    if "volume" in df.columns:
        colors = [
            "#26a69a" if c >= o else "#ef5350"
            for o, c in zip(df["open"], df["close"])
        ]
        fig.add_trace(
            go.Bar(x=df.index, y=df["volume"], marker_color=colors, name="vol", showlegend=False),
            row=2, col=1,
        )
    fig.update_layout(
        height=560,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        showlegend=False,
    )
    return fig
