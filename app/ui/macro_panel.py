"""Macro dashboard — DXY, VIX, rates, oil."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.data_sources import macro


@st.cache_data(ttl=1800, show_spinner=False)
def _cached_snapshot() -> list[dict]:
    # Cache just the values — Series objects aren't hashable-friendly but dicts are fine here
    snap = macro.snapshot()
    return [
        {
            "name": s["series"].name,
            "code": s["series"].code,
            "latest": s["latest"],
            "change": s["change"],
            "df": s["df"].to_dict("records") if not s["df"].empty else [],
        }
        for s in snap
    ]


def render() -> None:
    st.subheader("Macro")
    if st.button("Refresh macro", key="macro_refresh"):
        _cached_snapshot.clear()

    try:
        items = _cached_snapshot()
    except Exception as e:
        st.error(f"Macro fetch failed: {e}")
        return

    cols = st.columns(len(items))
    for col, it in zip(cols, items):
        latest = it["latest"]
        change = it["change"]
        col.metric(
            it["name"],
            f"{latest:,.2f}" if latest is not None else "—",
            f"{change:+.2f}" if change is not None else None,
        )

    # Sparkline grid
    spark_cols = st.columns(len(items))
    for col, it in zip(spark_cols, items):
        if not it["df"]:
            continue
        import pandas as pd
        df = pd.DataFrame(it["df"])
        fig = go.Figure(go.Scatter(x=df["date"], y=df["value"], line=dict(color="#26a69a", width=1.5)))
        fig.update_layout(
            height=110,
            margin=dict(l=4, r=4, t=4, b=4),
            template="plotly_dark",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        col.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.caption("Sources: FRED (primary), Yahoo Finance (fallback).")
