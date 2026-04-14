"""CFTC Commitments of Traders (COT) data.

The CFTC publishes weekly reports on Friday (for Tuesday-close positions).
Their Socrata API exposes this for free with no key required. We use the
"Legacy Futures-Only" dataset which has the classic Commercial /
Non-Commercial / Non-Reportable breakdown traders actually read.

Dataset docs: https://publicreporting.cftc.gov/resource/6dca-aqww
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import requests

from app.config import INSTRUMENTS

# Legacy futures-only reports
SOCRATA_ENDPOINT = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"


@dataclass
class CotSnapshot:
    report_date: datetime
    market_name: str
    # Non-commercial (speculators, "large specs")
    noncomm_long: int
    noncomm_short: int
    noncomm_spread: int
    # Commercial (hedgers — producers, swap dealers in older schema)
    comm_long: int
    comm_short: int
    # Non-reportable (small specs)
    nonrept_long: int
    nonrept_short: int
    open_interest: int

    @property
    def noncomm_net(self) -> int:
        return self.noncomm_long - self.noncomm_short

    @property
    def comm_net(self) -> int:
        return self.comm_long - self.comm_short


def fetch_history(symbol: str, weeks: int = 52) -> pd.DataFrame:
    """Fetch recent COT reports for a tracked instrument."""
    inst = INSTRUMENTS.get(symbol)
    if inst is None or not inst.cftc_code:
        return pd.DataFrame()

    params = {
        "cftc_contract_market_code": inst.cftc_code,
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": weeks,
    }
    try:
        r = requests.get(SOCRATA_ENDPOINT, params=params, timeout=15)
        r.raise_for_status()
        rows = r.json()
    except Exception:
        return pd.DataFrame()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Numeric casting — Socrata returns strings
    numeric_cols = [
        "noncomm_positions_long_all", "noncomm_positions_short_all", "noncomm_postions_spread_all",
        "comm_positions_long_all", "comm_positions_short_all",
        "nonrept_positions_long_all", "nonrept_positions_short_all",
        "open_interest_all",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["report_date"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"], errors="coerce")
    df = df.sort_values("report_date")
    return df


def latest_snapshot(symbol: str) -> CotSnapshot | None:
    df = fetch_history(symbol, weeks=1)
    if df.empty:
        return None
    row = df.iloc[-1]
    def _n(col: str) -> int:
        v = row.get(col)
        return int(v) if pd.notna(v) else 0

    return CotSnapshot(
        report_date=row["report_date"].to_pydatetime(),
        market_name=str(row.get("market_and_exchange_names", "")),
        noncomm_long=_n("noncomm_positions_long_all"),
        noncomm_short=_n("noncomm_positions_short_all"),
        noncomm_spread=_n("noncomm_postions_spread_all"),
        comm_long=_n("comm_positions_long_all"),
        comm_short=_n("comm_positions_short_all"),
        nonrept_long=_n("nonrept_positions_long_all"),
        nonrept_short=_n("nonrept_positions_short_all"),
        open_interest=_n("open_interest_all"),
    )
