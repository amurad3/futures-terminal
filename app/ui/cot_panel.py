"""CFTC Commitments of Traders panel."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.data_sources import cftc


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_history(symbol: str, weeks: int) -> pd.DataFrame:
    return cftc.fetch_history(symbol, weeks=weeks)


def render(symbol: str) -> None:
    st.subheader("CFTC Positioning (weekly)")
    weeks = st.slider("Weeks of history", 12, 156, 52, step=4, key=f"cot_weeks_{symbol}")

    try:
        df = _cached_history(symbol, weeks)
    except Exception as e:
        st.error(f"CFTC fetch failed: {e}")
        return

    if df.empty:
        st.info("No COT data for this instrument (CFTC updates weekly on Fridays).")
        return

    # Derive net positions
    df = df.copy()
    df["noncomm_net"] = df["noncomm_positions_long_all"] - df["noncomm_positions_short_all"]
    df["comm_net"] = df["comm_positions_long_all"] - df["comm_positions_short_all"]
    latest = df.iloc[-1]

    cols = st.columns(4)
    cols[0].metric("Report date", latest["report_date"].strftime("%Y-%m-%d"))
    cols[1].metric(
        "Large specs net",
        f"{int(latest['noncomm_net']):,}",
        delta=f"{int(latest['noncomm_net'] - df.iloc[-2]['noncomm_net']):,}" if len(df) > 1 else None,
    )
    cols[2].metric(
        "Commercials net",
        f"{int(latest['comm_net']):,}",
        delta=f"{int(latest['comm_net'] - df.iloc[-2]['comm_net']):,}" if len(df) > 1 else None,
    )
    cols[3].metric("Open interest", f"{int(latest['open_interest_all']):,}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["report_date"], y=df["noncomm_net"],
        name="Large specs (non-commercial)", line=dict(color="#26a69a", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df["report_date"], y=df["comm_net"],
        name="Commercials (hedgers)", line=dict(color="#ef5350", width=2),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="#888")
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        template="plotly_dark",
        legend=dict(orientation="h", y=1.1),
        yaxis_title="Net contracts",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Source: CFTC Socrata API (Legacy Futures-Only). Updated Fridays ~3:30pm ET.")
