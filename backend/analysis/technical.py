import pandas as pd
import numpy as np
from typing import List, Dict, Any
from backend.utils.logger import logger

class TechnicalAnalyzer:
    def __init__(self):
        pass

    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyzes a DataFrame containing standard OHLCV data natively.
        Returns a list of structured signals detected in the latest timeframe.
        """
        if df.empty or len(df) < 50:
            logger.warning("Not enough data to compute technical indicators (need at least 50 periods).")
            return []

        signals = []
        
        df.columns = [c.lower() for c in df.columns]
        
        # Calculate Indicators Natively (Avoiding pandas_ta due to Py3.14 Numba incompatibility)
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['vol_sma_20'] = df['volume'].rolling(window=20).mean()
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # Recent data for pattern detection
        current_data = df.iloc[-1]
        prev_data = df.iloc[-2]
        current_idx = df.index[-1]
        
        # 1. Volume Spikes
        vol_spike = False
        if pd.notna(current_data.get('vol_sma_20')) and current_data['volume'] > (current_data['vol_sma_20'] * 2.0):
            vol_spike = True
            signals.append({
                "pattern": "volume_spike",
                "confidence": 0.85,
                "volume_confirmation": True
            })
            
        # 2. RSI Extremes
        rsi = current_data.get('rsi_14')
        if pd.notna(rsi):
            if rsi < 30:
                signals.append({
                    "pattern": "oversold",
                    "confidence": 0.75,
                    "volume_confirmation": vol_spike
                })
            elif rsi > 70:
                signals.append({
                    "pattern": "overbought",
                    "confidence": 0.75,
                    "volume_confirmation": vol_spike
                })
                
        # 3. Moving Average Crossover (Golden Cross / Death Cross)
        if pd.notna(prev_data.get('sma_50')):
            if prev_data['sma_20'] <= prev_data['sma_50'] and current_data['sma_20'] > current_data['sma_50']:
                signals.append({
                    "pattern": "golden_cross",
                    "confidence": 0.82,
                    "volume_confirmation": vol_spike
                })
            elif prev_data['sma_20'] >= prev_data['sma_50'] and current_data['sma_20'] < current_data['sma_50']:
                signals.append({
                    "pattern": "death_cross",
                    "confidence": 0.82,
                    "volume_confirmation": vol_spike
                })
            
        # 4. Support / Resistance & Breakout
        recent_high = df['high'].rolling(window=20).max().shift(1).iloc[-1]
        recent_low = df['low'].rolling(window=20).min().shift(1).iloc[-1]
        
        if pd.notna(recent_high):
            if current_data['close'] > recent_high:
                signals.append({
                    "pattern": "breakout_bullish",
                    "confidence": 0.88 if vol_spike else 0.65,
                    "volume_confirmation": vol_spike
                })
            elif current_data['close'] < recent_low:
                signals.append({
                    "pattern": "breakdown_bearish",
                    "confidence": 0.88 if vol_spike else 0.65,
                    "volume_confirmation": vol_spike
                })
                
        # 5. Divergence Detection (Over last 15 periods)
        recent_close = df['close'].iloc[-15:]
        recent_rsi = df['rsi_14'].iloc[-15:]
        
        if not recent_close.empty and not recent_rsi.isna().all():
            close_min_idx = recent_close.idxmin()
            close_max_idx = recent_close.idxmax()
            rsi_min_idx = recent_rsi.idxmin()
            rsi_max_idx = recent_rsi.idxmax()
            
            # Bullish Divergence: Price hits new low, but RSI does not (momentum is shifting up)
            if close_min_idx == current_idx and rsi_min_idx != current_idx and rsi < 40:
                signals.append({
                    "pattern": "bullish_divergence",
                    "confidence": 0.72,
                    "volume_confirmation": vol_spike
                })
                
            # Bearish Divergence: Price hits new high, but RSI does not (momentum is slowing)
            if close_max_idx == current_idx and rsi_max_idx != current_idx and rsi > 60:
                signals.append({
                    "pattern": "bearish_divergence",
                    "confidence": 0.72,
                    "volume_confirmation": vol_spike
                })
            
        return signals

technical_analyzer = TechnicalAnalyzer()
