import json
import time
import uuid

from apscheduler.schedulers.background import BackgroundScheduler

from backend.services.opportunity_radar import opportunity_radar
from backend.services.nse_universe_scanner import nse_universe_scanner
from backend.utils.logger import logger


def _build_alert(signal_type: str, recommendation: str, score: float, ticker: str = "MARKET", count: int = 0) -> dict:
    return {
        "type": signal_type,
        "ticker": ticker,
        "score": round(score, 2),
        "recommendation": recommendation,
        "timestamp": time.strftime("%H:%M"),
        "pipeline_signals": count,
    }


def scan_market():
    """Full LangGraph pipeline scan — results broadcast to WebSocket clients."""
    logger.info("Scheduler: Starting periodic LangGraph market scan...")
    from backend.api.websockets.alerts import manager

    try:
        from backend.agents.graph import execute_agent_workflow

        initial_state = {
            "username": "system",
            "raw_market_data": {"tickers_to_scan": ["RELIANCE.NS", "INFY.NS", "HDFCBANK.NS"]},
            "extracted_signals": [],
            "technical_patterns": [],
            "contextual_insights": [],
            "portfolio_analysis": {},
            "signal_score": 0.0,
            "impact_estimation": {},
            "recommendation": "",
            "explanation": "",
            "backtesting_results": {},
            "agent_logs": [],
            "retry_counts": {},
        }
        results = execute_agent_workflow(initial_state, str(uuid.uuid4()))

        signals = results.get("extracted_signals", [])
        score = float(results.get("signal_score", 5.0))
        rec = results.get("recommendation", "Hold")
        explanation = results.get("explanation", "")

        # Broadcast pipeline summary
        manager.broadcast_from_thread(_build_alert(
            "PIPELINE_SCAN", f"{rec} — {explanation[:200]}", score, "MARKET", len(signals)
        ))

        # Broadcast individual top signals
        for sig in signals[:3]:
            manager.broadcast_from_thread({
                "type": sig.get("type", "SIGNAL"),
                "ticker": sig.get("ticker", "MARKET"),
                "score": round(float(sig.get("confidence", 0.5)) * 10, 1),
                "recommendation": sig.get("description", "")[:200],
                "timestamp": time.strftime("%H:%M"),
                "pipeline_signals": len(signals),
            })

        logger.info(f"Scheduler: LangGraph scan done — {len(signals)} signals broadcast.")

    except Exception as e:
        logger.error(f"Scheduler: LangGraph scan failed: {e}")
        manager.broadcast_from_thread(_build_alert(
            "SCAN_ERROR", f"Pipeline scan encountered an error: {str(e)[:120]}", 0.0
        ))


def refresh_radar_job():
    """Refreshes the Opportunity Radar and broadcasts top signal to WebSocket."""
    logger.info("Scheduler: Refreshing Opportunity Radar...")
    from backend.api.websockets.alerts import manager

    try:
        signals = opportunity_radar.refresh_global_signals()
        if signals:
            top = signals[0]
            manager.broadcast_from_thread({
                "type": top.get("signal_type", "ET_OPPORTUNITY"),
                "ticker": top.get("ticker", "MARKET"),
                "score": round(float(top.get("confidence", 0.5)) * 10, 1),
                "recommendation": top.get("description", "")[:220],
                "timestamp": time.strftime("%H:%M"),
                "pipeline_signals": len(signals),
            })
            logger.info(f"Radar refreshed: {len(signals)} signals, top broadcast.")
    except Exception as e:
        logger.error(f"Radar refresh failed: {e}")


def nse_scan_job():
    """Batch-scans NSE universe for technical patterns."""
    logger.info("Scheduler: Running NSE universe technical scan...")
    from backend.api.websockets.alerts import manager

    try:
        patterns = nse_universe_scanner.scan_batch()
        if patterns:
            top = patterns[0]
            ticker = top.get("ticker", "NSE")
            pattern = top.get("pattern", "signal").replace("_", " ").title()
            conf = round(float(top.get("confidence", 0.5)) * 10, 1)
            manager.broadcast_from_thread({
                "type": "NSE_PATTERN",
                "ticker": ticker,
                "score": conf,
                "recommendation": f"{ticker}: {pattern} detected with {conf}/10 conviction across NSE universe scan.",
                "timestamp": time.strftime("%H:%M"),
                "pipeline_signals": len(patterns),
            })
        logger.info(f"NSE scan done: {len(patterns)} patterns found.")
    except Exception as e:
        logger.error(f"NSE scan failed: {e}")


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run radar refresh at startup (30s delay) and then every 5 minutes
    scheduler.add_job(refresh_radar_job, "interval", minutes=5, next_run_time=__import__("datetime").datetime.now() + __import__("datetime").timedelta(seconds=30))
    scheduler.add_job(scan_market, "interval", minutes=7)
    scheduler.add_job(nse_scan_job, "interval", minutes=25)
    scheduler.start()
    logger.info("Scheduler started: radar=5m (first in 30s), LangGraph=7m, NSE universe=25m")
