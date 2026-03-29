from typing import Dict, Any, List
from backend.utils.logger import logger

class SignalScorer:
    def score_signals(self, signals: List[Dict[str, Any]], portfolio_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        scored_signals = []
        affected_holdings = portfolio_analysis.get("affected_holdings", [])
        
        for signal in signals:
            # 1. Base strength from upstream confidence
            strength = signal.get("confidence", 0.5) * 10 
            
            # 2. Volume confirmation augmentation
            if signal.get("volume_confirmation", False):
                strength += 1.5
                
            # 3. Portfolio exposure weighting
            ticker = signal.get("ticker", signal.get("asset", ""))
            exposure_bonus = 0.0
            for holding in affected_holdings:
                if holding.get("affected_stock") == ticker:
                    weight = holding.get("portfolio_weight", 0)
                    if weight > 10:
                        exposure_bonus = 2.0
                    elif weight > 0:
                        exposure_bonus = 1.0
                        
            strength += exposure_bonus
            
            # Cap scores securely at 10.0 natively
            final_strength = min(10.0, round(strength, 1))
            final_confidence = min(1.0, round(final_strength / 10.0, 2))
            
            scored = signal.copy()
            scored["signal_strength"] = final_strength
            scored["confidence"] = final_confidence
            
            # In case Backtesting module evaluates sequentially after Scoring, seed the historical key
            if "historical_success_rate" not in scored:
                scored["historical_success_rate"] = 0.0
                
            scored_signals.append(scored)
            logger.info(f"Scored {ticker} signal natively: Strength {final_strength}/10")

        # Prioritize signals strictly according to compound strength logic
        return sorted(scored_signals, key=lambda x: x["signal_strength"], reverse=True)

signal_scorer = SignalScorer()
