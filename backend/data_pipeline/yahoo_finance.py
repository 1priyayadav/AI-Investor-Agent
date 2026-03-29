from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from backend.utils.logger import logger


class YahooFinanceAPI:
    @staticmethod
    def get_stock_price(ticker: str) -> dict[str, Any]:
        try:
            import yfinance as yf

            t = yf.Ticker(ticker)
            info = t.fast_info if hasattr(t, "fast_info") else {}
            last = getattr(info, "last_price", None) or getattr(info, "lastPrice", None)
            hist = t.history(period="5d")
            price = float(hist["Close"].iloc[-1]) if not hist.empty else (float(last) if last else 0.0)
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
            vol = int(hist["Volume"].iloc[-1]) if not hist.empty else 0
            chg = ((price - prev) / prev * 100) if prev else 0.0
            return {
                "ticker": ticker,
                "price": round(price, 2),
                "volume": vol,
                "change_pct": round(chg, 2),
            }
        except Exception as e:
            logger.warning(f"yfinance price fallback for {ticker}: {e}")
            return {"ticker": ticker, "price": 0.0, "volume": 0, "change_pct": 0.0}

    @staticmethod
    def get_ohlcv_history(ticker: str, period: str = "3mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        """Daily OHLCV for technical analysis (NSE symbols use .NS suffix)."""
        try:
            import yfinance as yf

            t = yf.Ticker(ticker)
            df = t.history(period=period, interval=interval, auto_adjust=True)
            if df is None or df.empty or len(df) < 55:
                logger.warning(f"Insufficient OHLCV history for {ticker}")
                return None
            df = df.rename(columns=str.lower)
            if "adj close" in df.columns and "close" not in df.columns:
                df = df.rename(columns={"adj close": "close"})
            return df[["open", "high", "low", "close", "volume"]].dropna()
        except Exception as e:
            logger.error(f"yfinance OHLCV failed for {ticker}: {e}")
            return None
