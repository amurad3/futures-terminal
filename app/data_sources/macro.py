"""Macro series from FRED (and Yahoo as no-key fallback).

FRED's API needs a (free) key for high-volume use but allows low-volume
unauthenticated access to the CSV download endpoint. We fall back to
Yahoo tickers when even that fails, so the panel works out-of-the-box.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import StringIO

import pandas as pd
import requests
import yfinance as yf

from app.config import FRED_API_KEY, has_fred


@dataclass
class MacroSeries:
    code: str          # FRED code
    name: str          # display
    yahoo_fallback: str  # yfinance ticker if FRED fails
    direction_hint: str  # "risk-on" or "risk-off" — for coloring


# A compact macro dashboard — the things a futures trader actually watches.
SERIES: list[MacroSeries] = [
    MacroSeries("DTWEXBGS", "US Dollar Index (Broad)", "DX-Y.NYB", "risk-off"),
    MacroSeries("VIXCLS",   "VIX (S&P 500 vol)",        "^VIX",     "risk-off"),
    MacroSeries("DGS10",    "10Y Treasury yield",        "^TNX",     "risk-off"),
    MacroSeries("DGS2",     "2Y Treasury yield",         "^IRX",     "risk-off"),
    MacroSeries("DCOILWTICO", "WTI Crude ($/bbl)",       "CL=F",     "risk-on"),
]


def _fred_csv(code: str) -> pd.DataFrame:
    """Fetch a FRED series as a DataFrame. Returns empty df on failure."""
    if has_fred():
        url = (
            f"https://api.stlouisfed.org/fred/series/observations?"
            f"series_id={code}&api_key={FRED_API_KEY}&file_type=json&limit=500&sort_order=desc"
        )
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            obs = r.json().get("observations", [])
            df = pd.DataFrame(obs)
            if df.empty:
                return df
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df[["date", "value"]].dropna().sort_values("date")
        except Exception:
            pass

    # No-key CSV endpoint
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().tail(500)
    except Exception:
        return pd.DataFrame()


def _yahoo_series(ticker: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=False)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        out = pd.DataFrame({"date": df.index, "value": df["Close"].values})
        return out
    except Exception:
        return pd.DataFrame()


def fetch(series: MacroSeries) -> pd.DataFrame:
    df = _fred_csv(series.code)
    if df.empty:
        df = _yahoo_series(series.yahoo_fallback)
    return df


def snapshot() -> list[dict]:
    """Return the latest value + day change for each macro series."""
    out: list[dict] = []
    for s in SERIES:
        df = fetch(s)
        if df.empty or len(df) < 2:
            out.append({"series": s, "latest": None, "prev": None, "change": None, "df": df})
            continue
        latest = float(df["value"].iloc[-1])
        prev = float(df["value"].iloc[-2])
        out.append({"series": s, "latest": latest, "prev": prev, "change": latest - prev, "df": df})
    return out
