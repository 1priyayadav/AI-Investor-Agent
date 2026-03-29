"""
Economic Times Markets RSS — primary editorial/signal surface for Indian retail context.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from backend.core.config import settings
from backend.utils.logger import logger


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "").strip()


class ETMarketsFeed:
    """Fetch and parse ET Markets RSS; ingest into vector DB elsewhere."""

    def __init__(self, rss_url: str | None = None) -> None:
        self.rss_url = rss_url or settings.ET_MARKETS_RSS_URL

    def fetch_recent_headlines(self, limit: int = 40) -> list[dict[str, Any]]:
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                r = client.get(
                    self.rss_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; ET-InvestorBot/1.0)",
                        "Accept": "application/rss+xml, application/xml, text/xml",
                    },
                )
                r.raise_for_status()
                raw = r.content
        except Exception as e:
            logger.error(f"ET Markets RSS HTTP failed: {e}")
            return []

        parsed = feedparser.parse(raw)
        items = []
        for e in getattr(parsed, "entries", [])[:limit]:
            title = _strip_html(getattr(e, "title", "") or "")
            summary = _strip_html(
                getattr(e, "summary", "") or getattr(e, "description", "") or ""
            )
            link = getattr(e, "link", "") or ""
            pub = getattr(e, "published", "") or ""
            text = f"{title}. {summary}"
            alpha_keywords = (
                "block deal",
                "bulk deal",
                "insider",
                "promoter",
                "q1",
                "q2",
                "q3",
                "q4",
                "results",
                "guidance",
                "sebi",
                "regulatory",
                "fii",
                "dii",
                "ipo",
                "listing",
                "upgrade",
                "downgrade",
                "rating",
            )
            lower = text.lower()
            hit_score = sum(1 for k in alpha_keywords if k in lower)
            items.append(
                {
                    "title": title,
                    "summary": summary[:800],
                    "link": link,
                    "published": pub,
                    "source": "ET_Markets_RSS",
                    "alpha_keyword_hits": hit_score,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        logger.info(f"ET Markets RSS: parsed {len(items)} items")
        return items


et_markets_feed = ETMarketsFeed()
