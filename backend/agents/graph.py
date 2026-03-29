from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # Falling back to MemorySaver for scaffolding
from backend.agents.state import AgentState
from backend.agents.supervisor import AgentSupervisor
from backend.agents import nodes

# Initialize the Supervisor
supervisor = AgentSupervisor(max_retries=3)

def create_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    # 1. Register Nodes via Supervisor wrapper
    workflow.add_node("DataIngestionAgent", lambda s: supervisor.execute_with_retry("DataIngestionAgent", nodes.data_ingestion_agent, s))
    workflow.add_node("SignalDetectionAgent", lambda s: supervisor.execute_with_retry("SignalDetectionAgent", nodes.signal_detection_agent, s))
    workflow.add_node("TechnicalAnalysisAgent", lambda s: supervisor.execute_with_retry("TechnicalAnalysisAgent", nodes.technical_analysis_agent, s))
    workflow.add_node("ContextEnrichmentAgent", lambda s: supervisor.execute_with_retry("ContextEnrichmentAgent", nodes.context_enrichment_agent, s))
    workflow.add_node("PortfolioAnalysisAgent", lambda s: supervisor.execute_with_retry("PortfolioAnalysisAgent", nodes.portfolio_analysis_agent, s))
    workflow.add_node("SignalScoringAgent", lambda s: supervisor.execute_with_retry("SignalScoringAgent", nodes.signal_scoring_agent, s))
    workflow.add_node("ImpactEvaluationAgent", lambda s: supervisor.execute_with_retry("ImpactEvaluationAgent", nodes.impact_evaluation_agent, s))
    workflow.add_node("BacktestingAgent", lambda s: supervisor.execute_with_retry("BacktestingAgent", nodes.backtesting_agent, s))
    workflow.add_node("RecommendationAgent", lambda s: supervisor.execute_with_retry("RecommendationAgent", nodes.recommendation_agent, s))
    workflow.add_node("ExplanationAgent", lambda s: supervisor.execute_with_retry("ExplanationAgent", nodes.explanation_agent, s))
    workflow.add_node("UserFeedbackAgent", lambda s: supervisor.execute_with_retry("UserFeedbackAgent", nodes.user_feedback_agent, s))

    # 2. Sequential Workflow Edges
    workflow.set_entry_point("DataIngestionAgent")
    workflow.add_edge("DataIngestionAgent", "SignalDetectionAgent")
    workflow.add_edge("SignalDetectionAgent", "TechnicalAnalysisAgent")
    workflow.add_edge("TechnicalAnalysisAgent", "ContextEnrichmentAgent")
    workflow.add_edge("ContextEnrichmentAgent", "PortfolioAnalysisAgent")
    workflow.add_edge("PortfolioAnalysisAgent", "SignalScoringAgent")

    # 3. Parallel Branches from Signal Scoring Agent
    workflow.add_edge("SignalScoringAgent", "ImpactEvaluationAgent")
    workflow.add_edge("SignalScoringAgent", "BacktestingAgent")

    # Both parallel branches merge into Recommendation Agent
    workflow.add_edge("ImpactEvaluationAgent", "RecommendationAgent")
    workflow.add_edge("BacktestingAgent", "RecommendationAgent")

    # 4. Final sequence
    workflow.add_edge("RecommendationAgent", "ExplanationAgent")
    workflow.add_edge("ExplanationAgent", "UserFeedbackAgent")
    workflow.add_edge("UserFeedbackAgent", END)

    return workflow

def compile_graph():
    # In production, we swap MemorySaver with RedisSaver to satisfy 
    # the "Checkpointing with Redis memory" requirement.
    redis_memory = MemorySaver() 
    app = create_workflow().compile(checkpointer=redis_memory)
    return app

# Expose compiled app
agent_app = compile_graph()

def execute_agent_workflow(initial_state: dict, thread_id: str):
    """ Executes the graph. Triggers via API or Scheduler. """
    config = {"configurable": {"thread_id": thread_id}}
    result = agent_app.invoke(initial_state, config)
    return result
