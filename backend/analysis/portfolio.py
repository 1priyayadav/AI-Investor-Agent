from typing import List, Dict, Any
from backend.utils.logger import logger

class PortfolioAnalyzer:
    def __init__(self):
        # Mock sector mapping for prototyping
        self.sector_map = {
            "AAPL": "Technology",
            "TSLA": "Consumer Cyclical",
            "RELIANCE.NS": "Energy",
            "TCS.NS": "Technology",
            "INFY.NS": "Technology",
            "HDFCBANK.NS": "Financials",
            "ICICIBANK.NS": "Financials",
            "SBIN.NS": "Financials",
            "BHARTIARTL.NS": "Communication",
            "ITC.NS": "Consumer",
            "MARUTI.NS": "Consumer Cyclical",
            "ADANIENT.NS": "Infrastructure",
            "LT.NS": "Infrastructure",
            "KOTAKBANK.NS": "Financials",
            "ICICI Bank": "Financials",
        }

    def analyze_portfolio(self, portfolio_items: List[Dict[str, Any]], signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assesses the incoming portfolio dictionary against generated technical/news signals.
        """
        if not portfolio_items:
            return {"total_value": 0, "holdings": [], "sector_exposure": {}, "affected_holdings": []}

        # 1. basic valuation
        total_value = sum(item['shares'] * item['average_price'] for item in portfolio_items)
        
        # 2. Exposure & Sector Concentration
        sector_exposure = {}
        enriched_holdings = []
        for item in portfolio_items:
            ticker = item['ticker']
            value = item['shares'] * item['average_price']
            weight = (value / total_value) * 100 if total_value > 0 else 0
            
            sector = self.sector_map.get(ticker, "Unknown")
            sector_exposure[sector] = sector_exposure.get(sector, 0) + weight
            
            enriched_holdings.append({
                "ticker": ticker,
                "weight": round(weight, 2),
                "sector": sector,
                "value": round(value, 2)
            })

        # 3. Signal Relevance (Affected Holdings)
        affected_holdings = []
        for signal in signals:
            ticker = signal.get("ticker", signal.get("asset"))
            if not ticker:
                continue
                
            holding = next((h for h in enriched_holdings if h['ticker'] == ticker), None)
            if holding:
                is_bullish = False
                pattern = signal.get("pattern", signal.get("type", "")).lower()
                
                if "bullish" in pattern or "breakout" in pattern or "golden" in pattern:
                    is_bullish = True
                
                # Estimate a simulated impact securely
                impact_pct = "+2.4%" if is_bullish else "-1.5%"
                
                affected_holdings.append({
                    "affected_stock": ticker,
                    "portfolio_weight": holding["weight"],
                    "estimated_impact": impact_pct,
                    "signal_reason": pattern
                })
        
        # 4. Determine highest concentration risk natively
        max_sector = max(sector_exposure, key=sector_exposure.get) if sector_exposure else "None"
        max_exposure = sector_exposure.get(max_sector, 0)
        risk_alert = None
        if max_exposure > 40:
            risk_alert = f"High sector concentration risk in {max_sector} ({round(max_exposure, 1)}%)"

        return {
            "total_value": round(total_value, 2),
            "holdings": enriched_holdings,
            "sector_exposure": {k: round(v, 2) for k, v in sector_exposure.items()},
            "affected_holdings": affected_holdings,
            "concentration_risk": risk_alert
        }

portfolio_analyzer = PortfolioAnalyzer()
