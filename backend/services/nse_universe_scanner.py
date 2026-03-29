"""
Batch-scan NSE liquid universe for technical patterns (yfinance OHLCV). Not every NSE symbol — configurable list (~100+) for production realism.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from backend.analysis.technical import technical_analyzer
from backend.core.config import settings
from backend.data_pipeline.yahoo_finance import YahooFinanceAPI
from backend.services.cache_service import cache_service
from backend.utils.logger import logger

_PATTERN_CACHE = "nse_universe:patterns:latest"


def _load_universe() -> list[str]:
    p = Path(settings.NSE_UNIVERSE_FILE)
    if not p.exists():
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


class NSEUniverseScanner:
    def scan_batch(self, max_symbols: int | None = None) -> list[dict[str, Any]]:
        universe = _load_universe()
        n = max_symbols or settings.NSE_SCAN_TOP_N
        symbols = universe[:n]
        results: list[dict[str, Any]] = []
        yf = YahooFinanceAPI()

        for sym in symbols:
            try:
                df = yf.get_ohlcv_history(sym, period="6mo", interval="1d")
                if df is None or len(df) < 55:
                    continue
                patterns = technical_analyzer.analyze(df)
                for p in patterns:
                    p2 = dict(p)
                    p2["ticker"] = sym
                    p2["scan_id"] = str(uuid.uuid4())
                    results.append(p2)
                time.sleep(0.15)
            except Exception as e:
                logger.debug(f"scan skip {sym}: {e}")

        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        top = results[:200]
        cache_service.set_data(_PATTERN_CACHE, top, ttl_seconds=7200)
        logger.info(f"NSE universe scan: {len(top)} pattern rows from {len(symbols)} symbols")
        return top

    def latest_patterns(self, limit: int = 30) -> list[dict[str, Any]]:
        cached = cache_service.get_data(_PATTERN_CACHE)
        if cached:
            return cached[:limit]
        return self.scan_batch()[:limit]


nse_universe_scanner = NSEUniverseScanner()
