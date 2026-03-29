from backend.agents.state import AgentState
from backend.data_pipeline.ingestion_manager import ingestion_manager

def data_ingestion_agent(state: AgentState) -> dict:
    tickers = state.get("raw_market_data", {}).get("tickers_to_scan", ["AAPL"])
    if not tickers:
        tickers = ["AAPL"]
    
    ingested_data = {"tickers_to_scan": tickers}
    for ticker in tickers:
        ingested_data[ticker] = ingestion_manager.gather_all_data(ticker)
    
    return {
        "raw_market_data": ingested_data,
        "agent_logs": [f"DataIngestionAgent successfully fetched real-time APIs for {', '.join(tickers)}."]
    }

def signal_detection_agent(state: AgentState) -> dict:
    from backend.services.opportunity_radar import opportunity_radar

    tickers = state.get("raw_market_data", {}).get("tickers_to_scan", ["RELIANCE.NS"])
    raw = opportunity_radar.signals_for_tickers(tickers)
    extracted = []
    for s in raw:
        extracted.append(
            {
                "type": s.get("signal_type", "RADAR"),
                "ticker": s.get("ticker", "MARKET"),
                "confidence": float(s.get("confidence", 0.55)),
                "description": s.get("description", "")[:800],
                "action_hint": s.get("action_hint", "REVIEW"),
                "source": s.get("source", "OpportunityRadar"),
            }
        )
    if not extracted:
        extracted = [
            {
                "type": "RADAR_IDLE",
                "ticker": tickers[0],
                "confidence": 0.35,
                "description": "Opportunity radar has no fresh ET/NSE cross-matches for these tickers yet.",
                "action_hint": "REVIEW",
                "source": "OpportunityRadar",
            }
        ]
    return {
        "extracted_signals": extracted,
        "agent_logs": [f"SignalDetectionAgent merged Opportunity Radar ({len(extracted)} signals)."],
    }


def technical_analysis_agent(state: AgentState) -> dict:
    from backend.analysis.technical import technical_analyzer
    from backend.data_pipeline.yahoo_finance import YahooFinanceAPI

    tickers = state.get("raw_market_data", {}).get("tickers_to_scan", ["RELIANCE.NS"])
    yf = YahooFinanceAPI()
    all_patterns = []
    for ticker in tickers:
        df = yf.get_ohlcv_history(ticker, period="6mo", interval="1d")
        if df is None or len(df) < 55:
            continue
        patterns = technical_analyzer.analyze(df)
        for p in patterns:
            p["ticker"] = ticker
            all_patterns.append(p)

    return {
        "technical_patterns": all_patterns,
        "agent_logs": [f"TechnicalAnalysisAgent used live OHLCV (yfinance) for {len(tickers)} names; patterns={len(all_patterns)}."],
    }

def context_enrichment_agent(state: AgentState) -> dict:
    from backend.services.vector_service import vector_service
    from backend.services.graph_service import graph_service
    
    tickers = state.get("raw_market_data", {}).get("tickers_to_scan", ["AAPL"])
    technical_patterns = state.get("technical_patterns", [])
    
    enrichments = []
    
    # Just in case the graph is totally empty at startup, seed it (for prototype only)
    graph_service.seed_mock_data()
    
    for ticker in tickers:
        # 1. Graph Query (Identify relationships between entities, investors, board mapping)
        graph_data = graph_service.get_company_relationships(ticker)
        if graph_data.get("relationships"):
            enrichments.append({
                "ticker": ticker,
                "source": "Neo4j Knowledge Graph",
                "insight_type": "entity_relationships",
                "data": graph_data["relationships"]
            })
            
        # 2. Vector Retrieval (RAG on news and corporate filings for context)
        query_str = f"Latest corporate developments, filings, and earnings impact for {ticker}"
        rag_results = vector_service.query_documents(
            query_text=query_str,
            n_results=3,
            metadata_filter={"ticker": ticker},
        )
        if not rag_results:
            rag_results = vector_service.query_documents(query_str, n_results=3, metadata_filter=None)

        if rag_results:
            enrichments.append({
                "ticker": ticker,
                "source": "ChromaDB RAG",
                "insight_type": "news_and_filings",
                "data": rag_results
            })
            
        # Contextualize specific technical breakouts/patterns with historical vector contexts
        for pattern in technical_patterns:
            if pattern.get("ticker") == ticker:
                pat_name = pattern.get("pattern", "")
                pat_rag = vector_service.query_documents(
                    query_text=f"Historical precedent and market dynamics for {pat_name} in {ticker}",
                    n_results=2,
                    metadata_filter={"ticker": ticker},
                )
                if not pat_rag:
                    pat_rag = vector_service.query_documents(
                        f"Historical precedent for {pat_name} {ticker}", n_results=2, metadata_filter=None
                    )
                if pat_rag:
                    enrichments.append({
                        "ticker": ticker,
                        "source": "ChromaDB RAG",
                        "insight_type": "pattern_context",
                        "data": pat_rag
                    })

    return {
        "contextual_insights": enrichments,
        "agent_logs": [f"ContextEnrichmentAgent gathered vector and graph data for {len(tickers)} tickers."]
    }

def portfolio_analysis_agent(state: AgentState) -> dict:
    from backend.analysis.portfolio import portfolio_analyzer
    from backend.api.routes.portfolio import MOCK_PORTFOLIOS

    uid = state.get("username") or "testuser"
    user_portfolio = MOCK_PORTFOLIOS.get(uid, MOCK_PORTFOLIOS.get("testuser", []))
    
    portfolio_dicts = []
    for item in user_portfolio:
        if hasattr(item, "dict"):
            portfolio_dicts.append(item.dict())
        elif hasattr(item, "model_dump"):
            portfolio_dicts.append(item.model_dump())
        else:
            portfolio_dicts.append(item)
            
    tech_patterns = state.get("technical_patterns", [])
    extracted_signals = state.get("extracted_signals", [])
    all_signals = tech_patterns + extracted_signals
    
    analysis = portfolio_analyzer.analyze_portfolio(portfolio_dicts, all_signals)
    
    return {
        "portfolio_analysis": analysis,
        "agent_logs": ["PortfolioAnalysisAgent evaluated user holdings against live signals."]
    }

def signal_scoring_agent(state: AgentState) -> dict:
    from backend.analysis.scoring import signal_scorer
    
    tech_patterns = state.get("technical_patterns", [])
    extracted_signals = state.get("extracted_signals", [])
    all_signals = tech_patterns + extracted_signals
    
    portfolio_analysis = state.get("portfolio_analysis", {})
    
    scored_signals = signal_scorer.score_signals(all_signals, portfolio_analysis)
    
    return {
        "technical_patterns": [s for s in scored_signals if "pattern" in s],
        "extracted_signals": [s for s in scored_signals if "type" in s],
        "signal_score": scored_signals[0]["signal_strength"] if scored_signals else 0.0,
        "agent_logs": [f"SignalScoringAgent scored {len(scored_signals)} signals securely."]
    }

def impact_evaluation_agent(state: AgentState) -> dict:
    from backend.data_pipeline.nse_client import nse_public_client

    fiidii = nse_public_client.fiidii_today()
    port = state.get("portfolio_analysis", {})
    return {
        "impact_estimation": {
            "expected_roi": "data-driven",
            "risk_score": "elevated" if port.get("concentration_risk") else "moderate",
            "fii_dii_snapshot": fiidii,
            "portfolio_concentration": port.get("sector_exposure", {}),
        }
    }

def backtesting_agent(state: AgentState) -> dict:
    from backend.analysis.backtesting import backtester
    
    tech_patterns = state.get("technical_patterns", [])
    extracted_signals = state.get("extracted_signals", [])
    all_signals = tech_patterns + extracted_signals
    
    backtested_signals = backtester.evaluate_signals(all_signals)
    
    avg_success = 0.0
    if backtested_signals:
        avg_success = sum(s.get("historical_success_rate", 0) for s in backtested_signals) / len(backtested_signals)
    
    return {
        "technical_patterns": [s for s in backtested_signals if "pattern" in s],
        "extracted_signals": [s for s in backtested_signals if "type" in s],
        "backtesting_results": {"average_historical_success_rate": round(avg_success, 2)},
        "agent_logs": ["BacktestingAgent augmented signals with historical probabilities."]
    }

def recommendation_agent(state: AgentState) -> dict:
    score = state.get("signal_score", 5.0)
    rec = "Hold"
    if score > 7.5: rec = "Strong Buy"
    elif score > 6.0: rec = "Buy"
    elif score < 4.0: rec = "Sell"
    return {"recommendation": rec, "agent_logs": ["RecommendationAgent calibrated bias constraint."]}

def explanation_agent(state: AgentState) -> dict:
    tech_patterns = state.get("technical_patterns", [])
    context = state.get("contextual_insights", [])
    bt = state.get("backtesting_results", {})

    plain = []
    for p in tech_patterns[:5]:
        pat = p.get("pattern", "?")
        t = p.get("ticker", "")
        h = p.get("historical_success_rate")
        if h is not None:
            plain.append(f"{t}: {pat.replace('_', ' ')} — back-tested hit-rate ~{float(h)*100:.1f}% on recent history.")
        else:
            plain.append(f"{t}: {pat.replace('_', ' ')} pattern detected.")

    if plain:
        explanation = " ".join(plain)
        explanation += f" Context layers: {len(context)} ET/Chroma/Neo4j enrichments."
    else:
        explanation = "Limited technical overlap on this scan; rely on Opportunity Radar + macro flows in the dashboard."
    if bt.get("average_historical_success_rate"):
        explanation += f" Avg historical success proxy: {bt['average_historical_success_rate']}."

    return {"explanation": explanation, "agent_logs": ["ExplanationAgent produced plain-English + backtest-aware copy."]}

def user_feedback_agent(state: AgentState) -> dict:
    return {"agent_logs": ["User Feedback Agent processed the final graph state."]}
