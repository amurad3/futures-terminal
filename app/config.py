"""Central configuration for the futures terminal."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CACHE_DIR = ROOT / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Instrument:
    """A tradable futures instrument we track."""

    symbol: str            # display symbol, e.g. "ES"
    yahoo: str             # yfinance ticker for continuous front-month, e.g. "ES=F"
    name: str              # human name
    cftc_code: str | None  # CFTC COT report code
    keywords: tuple[str, ...]  # for filtering news/social


INSTRUMENTS: dict[str, Instrument] = {
    "ES": Instrument(
        symbol="ES",
        yahoo="ES=F",
        name="E-mini S&P 500",
        cftc_code="13874A",
        keywords=("S&P 500", "SPX", "ES futures", "E-mini"),
    ),
    "NQ": Instrument(
        symbol="NQ",
        yahoo="NQ=F",
        name="E-mini Nasdaq-100",
        cftc_code="209742",
        keywords=("Nasdaq", "NDX", "NQ futures"),
    ),
    "CL": Instrument(
        symbol="CL",
        yahoo="CL=F",
        name="Crude Oil (WTI)",
        cftc_code="067651",
        keywords=("crude oil", "WTI", "oil futures", "OPEC"),
    ),
    "GC": Instrument(
        symbol="GC",
        yahoo="GC=F",
        name="Gold",
        cftc_code="088691",
        keywords=("gold", "bullion", "XAU"),
    ),
}


# --- API keys (all optional) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "").strip()
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "futures-terminal/0.1").strip()
FRED_API_KEY = os.getenv("FRED_API_KEY", "").strip()


def has_anthropic() -> bool:
    return bool(ANTHROPIC_API_KEY)


def has_reddit() -> bool:
    return bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)


def has_fred() -> bool:
    return bool(FRED_API_KEY)
