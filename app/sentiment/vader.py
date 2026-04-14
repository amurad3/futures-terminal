"""Fast, offline sentiment scoring via VADER.

VADER is a lexicon-based sentiment analyzer tuned for social/short-form
text. It's not finance-specific but performs surprisingly well on news
headlines. Use it as the default scorer; escalate to Claude for deep
analysis on demand.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@dataclass
class SentimentScore:
    compound: float   # -1 (most negative) .. +1 (most positive)
    positive: float
    neutral: float
    negative: float

    @property
    def label(self) -> str:
        if self.compound >= 0.2:
            return "bullish"
        if self.compound <= -0.2:
            return "bearish"
        return "neutral"


# Finance-specific nudges: VADER doesn't know these out of the box.
FIN_LEX = {
    "beat": 2.0, "beats": 2.0, "missed": -2.0, "misses": -2.0,
    "surge": 2.0, "surged": 2.0, "rally": 1.8, "rallies": 1.8,
    "plunge": -2.5, "plunged": -2.5, "crash": -3.0, "crashed": -3.0,
    "tumble": -2.0, "tumbled": -2.0, "slump": -1.8, "slumped": -1.8,
    "soar": 2.2, "soared": 2.2, "jump": 1.5, "jumped": 1.5,
    "hawkish": -1.5, "dovish": 1.5,
    "downgrade": -2.0, "downgraded": -2.0, "upgrade": 1.8, "upgraded": 1.8,
    "bullish": 2.5, "bearish": -2.5,
    "recession": -2.5, "stagflation": -2.5, "inflation": -1.0,
    "layoff": -2.0, "layoffs": -2.0, "bankruptcy": -3.0,
    "record high": 2.0, "all-time high": 2.0, "record low": -2.0,
    "cut rates": 1.5, "rate cut": 1.5, "rate hike": -1.2, "hike rates": -1.2,
}


@lru_cache(maxsize=1)
def _analyzer() -> SentimentIntensityAnalyzer:
    a = SentimentIntensityAnalyzer()
    a.lexicon.update(FIN_LEX)
    return a


def score(text: str) -> SentimentScore:
    if not text:
        return SentimentScore(0.0, 0.0, 1.0, 0.0)
    s = _analyzer().polarity_scores(text)
    return SentimentScore(
        compound=s["compound"],
        positive=s["pos"],
        neutral=s["neu"],
        negative=s["neg"],
    )


def score_many(texts: Iterable[str]) -> list[SentimentScore]:
    return [score(t) for t in texts]


def aggregate(scores: list[SentimentScore]) -> SentimentScore:
    """Mean-aggregate a list of scores into one overall score."""
    if not scores:
        return SentimentScore(0.0, 0.0, 1.0, 0.0)
    n = len(scores)
    return SentimentScore(
        compound=sum(s.compound for s in scores) / n,
        positive=sum(s.positive for s in scores) / n,
        neutral=sum(s.neutral for s in scores) / n,
        negative=sum(s.negative for s in scores) / n,
    )
