"""
Opportunity Radar: combines ET Markets RSS, NSE flows, bulk deals, and ingestion signals into ranked alpha alerts (not plain summaries).
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from backend.core.config import settings
from backend.data_pipeline.et_markets_feed import et_markets_feed
from backend.data_pipeline.nse_client import nse_public_client
from backend.services.cache_service import cache_service
from backend.services.vector_service import stable_id, vector_service
from backend.utils.logger import logger

_CACHE_KEY = "opportunity_radar:v1"
_REDIS_LIST = "radar:signals"


def _ticker_from_text(text: str) -> Optional[str]:
    """Map common Indian large-caps mentioned in ET headlines to yfinance symbols."""
    t = text.upper()
    mapping = [
        ("RELIANCE", "RELIANCE.NS"),
        ("TCS", "TCS.NS"),
        ("HDFC BANK", "HDFCBANK.NS"),
        ("ICICI", "ICICIBANK.NS"),
        ("INFOSYS", "INFY.NS"),
        ("INFY", "INFY.NS"),
        ("SBIN", "SBIN.NS"),
        ("STATE BANK", "SBIN.NS"),
        ("BHARTI", "BHARTIARTL.NS"),
        ("KOTAK", "KOTAKBANK.NS"),
        ("LARSEN", "LT.NS"),
        ("ITC", "ITC.NS"),
        ("TATA MOTORS", "TATAMOTORS.NS"),
        ("MARUTI", "MARUTI.NS"),
    ]
    for k, sym in mapping:
        if k in t:
            return sym
    m = re.search(r"\b([A-Z]{3,15})\b", t)
    if m and m.group(1) not in {"THE", "FOR", "AND", "NSE", "BSE", "FII", "DII", "IPO", "Q1", "Q2", "Q3", "Q4"}:
        cand = m.group(1) + ".NS"
        return cand
    return None


class OpportunityRadar:
    def refresh_global_signals(self) -> list[dict[str, Any]]:
        headlines = et_markets_feed.fetch_recent_headlines(limit=50)
        for h in headlines:
            blob = f"{h['title']}\n{h.get('summary', '')}"
            vector_service.store_document(
                stable_id("et", blob[:500]),
                blob,
                metadata={"source": "ET_Markets", "link": h.get("link", ""), "type": "rss_item"},
            )

        fiidii = nse_public_client.fiidii_today()
        bulk = nse_public_client.bulk_deals_today() or []

        signals: list[dict[str, Any]] = []

        for h in headlines:
            score = 0.2 * min(h.get("alpha_keyword_hits", 0), 10)
            title = h.get("title", "")
            if score <= 0 and len(title) < 10:
                continue
            score += 0.15 * len(title.split())
            ticker_guess = _ticker_from_text(title + " " + h.get("summary", ""))
            action = "REVIEW"
            if any(x in title.lower() for x in ("block deal", "bulk deal", "insider", "promoter")):
                action = "WATCH_BUY_FLOW"
                score += 2.0
            if any(x in title.lower() for x in ("sebi", "regulatory", "penalty")):
                action = "RISK_REVIEW"
                score += 1.5
            if h.get("alpha_keyword_hits", 0) >= 3:
                action = "ALPHA_SCAN"
                score += 1.0

            signals.append(
                {
                    "id": str(uuid.uuid4()),
                    "ticker": ticker_guess or "MARKET",
                    "signal_type": "ET_OPPORTUNITY",
                    "confidence": min(0.95, 0.35 + score / 25.0),
                    "description": title[:500],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "impact_estimate": f"alpha_score={score:.2f}",
                    "action_hint": action,
                    "source": "ET_Markets_RSS",
                    "metadata": {"link": h.get("link"), "keyword_hits": h.get("alpha_keyword_hits")},
                }
            )

        if fiidii:
            signals.append(
                {
                    "id": str(uuid.uuid4()),
                    "ticker": "NIFTY",
                    "signal_type": "FII_DII_FLOW",
                    "confidence": 0.7,
                    "description": f"Institutional flow snapshot: {json.dumps(fiidii)[:800]}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "impact_estimate": "regime",
                    "action_hint": "MACRO_ALIGN",
                    "source": "NSE_FII_DII",
                    "metadata": {},
                }
            )

        for row in bulk[:15]:
            if isinstance(row, dict):
                sym = row.get("symbol") or row.get("Symbol") or "UNKNOWN"
                signals.append(
                    {
                        "id": str(uuid.uuid4()),
                        "ticker": f"{sym}.NS" if "." not in sym else sym,
                        "signal_type": "BULK_BLOCK",
                        "confidence": 0.78,
                        "description": json.dumps(row)[:600],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "impact_estimate": "flow",
                        "action_hint": "WATCH_VOLUME",
                        "source": "NSE_BULK_DEALS",
                        "metadata": row,
                    }
                )

        signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        cache_service.set_data(_CACHE_KEY, signals[:200], ttl_seconds=86400)

        if cache_service.client:
            try:
                cache_service.client.delete(_REDIS_LIST)
                for s in signals[:100]:
                    cache_service.client.rpush(_REDIS_LIST, json.dumps(s))
                cache_service.client.expire(_REDIS_LIST, 86400)
            except Exception as e:
                logger.error(f"Redis radar list: {e}")

        logger.info(f"OpportunityRadar refreshed: {len(signals)} signals")
        return signals

    def get_signals(self, limit: int = 50) -> list[dict[str, Any]]:
        cached = cache_service.get_data(_CACHE_KEY)
        if cached:
            return cached[:limit]
        return self.refresh_global_signals()[:limit]

    def signals_for_tickers(self, tickers: list[str]) -> list[dict[str, Any]]:
        tickers_norm = {t.upper().replace(" ", "") for t in tickers}
        out = []
        for s in self.get_signals(200):
            t = (s.get("ticker") or "").upper()
            if t in tickers_norm or t == "MARKET":
                out.append(s)
        return out[:20]


opportunity_radar = OpportunityRadar()
