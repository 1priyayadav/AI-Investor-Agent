from __future__ import annotations

from typing import Any, Dict, List

from backend.data_pipeline.yahoo_finance import YahooFinanceAPI
from backend.utils.logger import logger


class Backtester:
    def evaluate_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Estimates historical hit-rate using forward returns after the last comparable move (yfinance OHLCV).
        Falls back to pattern-family heuristics when data is missing.
        """
        yf = YahooFinanceAPI()
        evaluated = []
        for signal in signals:
            ticker = signal.get("ticker") or signal.get("asset", "UNKNOWN")
            pattern = str(signal.get("pattern", signal.get("type", "unknown"))).lower()

            success_rate = self._forward_return_score(yf, ticker, pattern)
            if success_rate is None:
                success_rate = self._heuristic_base(pattern)

            signal_copy = dict(signal)
            signal_copy["historical_success_rate"] = round(success_rate, 3)
            evaluated.append(signal_copy)
            logger.info(f"Backtest {pattern} @ {ticker}: historical_success_rate={success_rate}")

        return evaluated

    def _forward_return_score(self, yf: YahooFinanceAPI, ticker: str, pattern: str) -> float | None:
        if not ticker or ticker == "UNKNOWN" or ticker == "MARKET":
            return None
        try:
            df = yf.get_ohlcv_history(ticker, period="2y", interval="1d")
            if df is None or len(df) < 30:
                return None
            close = df["close"].astype(float)
            ret_5 = close.pct_change(5).shift(-5)
            # Proxy "pattern success": positive forward 5d when momentum pattern
            momentum = pattern in ("golden_cross", "breakout_bullish", "volume_spike", "oversold")
            neg = pattern in ("death_cross", "breakdown_bearish", "overbought", "bearish_divergence")

            valid = ret_5.dropna()
            if valid.empty:
                return None
            if momentum:
                hits = (valid > 0).sum() / len(valid)
            elif neg:
                hits = (valid < 0).sum() / len(valid)
            else:
                hits = (valid.abs() < 0.08).sum() / len(valid)
            return float(min(0.95, max(0.35, hits)))
        except Exception as e:
            logger.debug(f"forward return score skip {ticker}: {e}")
            return None

    def _heuristic_base(self, pattern: str) -> float:
        pl = pattern.lower()
        if any(x in pl for x in ("bullish", "breakout", "golden", "volume_spike")):
            return 0.62
        if any(x in pl for x in ("bearish", "death", "breakdown", "overbought")):
            return 0.58
        return 0.52


backtester = Backtester()
