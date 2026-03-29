from typing import TypedDict, List, Dict, Any, Annotated
import operator

class AgentState(TypedDict):
    """
    Shared Agent State Schema
    Passed between all LangGraph agents during the workflow execution.
    """
    username: str | None
    raw_market_data: Dict[str, Any]
    extracted_signals: List[Dict[str, Any]]
    technical_patterns: List[Dict[str, Any]]
    contextual_insights: List[Dict[str, Any]]
    portfolio_analysis: Dict[str, Any]
    signal_score: float
    impact_estimation: Dict[str, Any]
    recommendation: str
    explanation: str
    backtesting_results: Dict[str, Any]

    # Operational state
    agent_logs: Annotated[List[str], operator.add]
    retry_counts: Dict[str, int]
