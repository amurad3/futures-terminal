# Futures Terminal

An open-source Bloomberg-style terminal for futures traders, focused on ES, NQ, CL (oil), and GC (gold). Aggregates free data sources (prices, news, CFTC positioning, Reddit, macro) and runs on-demand sentiment analysis.

## Stack

- **Backend + UI:** Streamlit (Python)
- **Price data:** Yahoo Finance (`yfinance`) — free, 15-min delayed
- **News:** RSS feeds (Reuters, CNBC, Investing.com, etc.)
- **Macro:** FRED (free, requires free API key for high-volume)
- **Positioning:** CFTC Commitments of Traders
- **Social:** Reddit (free API)
- **Sentiment:** VADER (offline, free) + optional Claude API for deep analysis

## Quickstart

```bash
cd futures-terminal
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
streamlit run app/main.py
```

## Environment

Copy `.env.example` to `.env` and fill in any keys you have. All are optional — the app runs without them, just with reduced features.

```
ANTHROPIC_API_KEY=           # for "Deep Analyze" button
REDDIT_CLIENT_ID=            # for social feed
REDDIT_CLIENT_SECRET=
FRED_API_KEY=                # for macro panel (higher rate limits)
```

## Status

Under active development. See commit history.
