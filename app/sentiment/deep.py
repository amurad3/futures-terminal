"""'Deep Analyze' — richer sentiment + thesis via the Claude API.

Falls back gracefully when ANTHROPIC_API_KEY is not set.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.config import ANTHROPIC_API_KEY, has_anthropic

SYSTEM_PROMPT = """You are a macro-savvy markets analyst reviewing recent headlines for a futures trader.

Given a set of headlines relevant to one instrument, produce:
1. A single overall sentiment label: bullish / bearish / mixed / neutral
2. A confidence score 0-1
3. The 3-5 most important drivers (short bullets)
4. Key risks / counter-narrative (short bullets)
5. One-paragraph thesis

Be concise, no fluff. Do not invent facts that aren't in the headlines.
Respond in compact markdown."""


@dataclass
class DeepAnalysis:
    label: str
    confidence: float
    markdown: str


def analyze(symbol: str, instrument_name: str, headlines: Iterable[str]) -> DeepAnalysis:
    if not has_anthropic():
        return DeepAnalysis(
            label="unavailable",
            confidence=0.0,
            markdown=(
                "**Deep Analyze requires an Anthropic API key.**\n\n"
                "Add `ANTHROPIC_API_KEY=sk-ant-...` to your `.env` file and restart."
            ),
        )

    from anthropic import Anthropic

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    headlines_block = "\n".join(f"- {h}" for h in headlines if h)
    user_msg = (
        f"Instrument: {symbol} ({instrument_name})\n\n"
        f"Recent headlines:\n{headlines_block}\n\n"
        "Analyze sentiment and drivers for this instrument specifically."
    )

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = "".join(block.text for block in resp.content if hasattr(block, "text"))
    except Exception as e:
        return DeepAnalysis(label="error", confidence=0.0, markdown=f"**Claude API error:** {e}")

    label = _extract_label(text)
    return DeepAnalysis(label=label, confidence=0.0, markdown=text)


def _extract_label(text: str) -> str:
    low = text.lower()
    for lbl in ("bullish", "bearish", "mixed", "neutral"):
        if lbl in low:
            return lbl
    return "unknown"
