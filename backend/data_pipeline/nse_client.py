"""
NSE India public JSON endpoints (FII/DII, optional bulk-deals). Uses session + cookies; may fail behind strict firewalls — graceful fallback.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from backend.utils.logger import logger


class NSEPublicClient:
    BASE = "https://www.nseindia.com"

    def __init__(self) -> None:
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    def _session(self) -> httpx.Client:
        c = httpx.Client(timeout=25.0, headers=self._headers, follow_redirects=True)
        c.get(self.BASE)  # cookie
        return c

    def fiidii_today(self) -> Optional[dict[str, Any]]:
        try:
            with self._session() as client:
                r = client.get(f"{self.BASE}/api/fiidiiTradeReact?reqType=fii")
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.warning(f"NSE FII/DII fetch failed: {e}")
            return None

    def bulk_deals_today(self) -> Optional[list[dict[str, Any]]]:
        try:
            with self._session() as client:
                r = client.get(f"{self.BASE}/api/historical/bulk-deals")
                r.raise_for_status()
                data = r.json()
                if isinstance(data, list):
                    return data[:50]
                if isinstance(data, dict) and "data" in data:
                    return data["data"][:50]
        except Exception as e:
            logger.warning(f"NSE bulk deals fetch failed: {e}")
        return None


nse_public_client = NSEPublicClient()
