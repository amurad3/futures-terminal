"""Price data via Yahoo Finance (yfinance).

Free, ~15 min delayed for futures. Continuous front-month contracts
(e.g. ES=F) are what most traders look at for chart context.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache

import pandas as pd
import yfinance as yf

from app.config import INSTRUMENTS, Instrument


VALID_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "1d"}
# Yahoo intraday data has lookback caps; keep sensible defaults.
DEFAULT_PERIOD = {
    "1m": "5d",
    "5m": "1mo",
    "15m": "1mo",
    "30m": "2mo",
    "60m": "3mo",
    "1d": "2y",
}


def _ticker(symbol: str) -> str:
    if symbol in INSTRUMENTS:
        return INSTRUMENTS[symbol].yahoo
    return symbol


def fetch_history(symbol: str, interval: str = "15m", period: str | None = None) -> pd.DataFrame:
    """Fetch OHLCV history. Returns DataFrame indexed by timestamp."""
    if interval not in VALID_INTERVALS:
        raise ValueError(f"interval must be one of {VALID_INTERVALS}")
    period = period or DEFAULT_PERIOD.get(interval, "1mo")
    df = yf.download(
        _ticker(symbol),
        interval=interval,
        period=period,
        progress=False,
        auto_adjust=False,
    )
    if df.empty:
        return df
    # yfinance sometimes returns MultiIndex columns; flatten.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    df.index.name = "timestamp"
    return df


def fetch_quote(symbol: str) -> dict:
    """Latest quote snapshot: price, day change, volume."""
    df = fetch_history(symbol, interval="1d", period="5d")
    if df.empty or len(df) < 2:
        return {"price": None, "change": None, "change_pct": None, "volume": None, "as_of": None}
    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last["close"])
    prev_close = float(prev["close"])
    change = price - prev_close
    return {
        "price": price,
        "change": change,
        "change_pct": (change / prev_close * 100) if prev_close else None,
        "volume": float(last.get("volume", 0) or 0),
        "as_of": df.index[-1].to_pydatetime() if isinstance(df.index[-1], pd.Timestamp) else datetime.utcnow(),
    }


@lru_cache(maxsize=32)
def _cached_history(symbol: str, interval: str, period: str, bucket: int) -> pd.DataFrame:
    """Internal cached wrapper. `bucket` is a time bucket for TTL eviction."""
    return fetch_history(symbol, interval=interval, period=period)


def fetch_history_cached(symbol: str, interval: str = "15m", period: str | None = None, ttl_seconds: int = 60) -> pd.DataFrame:
    """Cached fetch — bucket timestamp enforces a TTL on the lru_cache."""
    period = period or DEFAULT_PERIOD.get(interval, "1mo")
    bucket = int(datetime.utcnow().timestamp() // max(ttl_seconds, 1))
    return _cached_history(symbol, interval, period, bucket)
