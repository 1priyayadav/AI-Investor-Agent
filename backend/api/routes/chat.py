from fastapi import APIRouter, Depends
from backend.api.deps import get_optional_user, TokenData
from pydantic import BaseModel
from backend.agents.graph import execute_agent_workflow
import uuid

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []


def extract_tickers(message: str) -> list[str]:
    mapping = {
        "infosys": "INFY.NS",
        "infy": "INFY.NS",
        "apple": "AAPL",
        "reliance": "RELIANCE.NS",
        "tesla": "TSLA",
        "icici": "ICICIBANK.NS",
        "hdfc": "HDFCBANK.NS",
        "tcs": "TCS.NS",
        "sbi": "SBIN.NS",
        "bharti": "BHARTIARTL.NS",
        "itc": "ITC.NS",
        "maruti": "MARUTI.NS",
        "adani": "ADANIENT.NS",
    }
    found = []
    text = message.lower()
    for k, v in mapping.items():
        if k in text:
            found.append(v)
    return found if found else ["RELIANCE.NS"]


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, current_user: TokenData = Depends(get_optional_user)):
    user_msg = request.message
    tickers = extract_tickers(user_msg)

    initial_state = {
        "username": current_user.username,
        "raw_market_data": {"tickers_to_scan": tickers},
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

    thread_id = str(uuid.uuid4())

    try:
        result = execute_agent_workflow(initial_state, thread_id)

        recommendation = result.get("recommendation", "")
        explanation = result.get("explanation", "")
        portfolio = result.get("portfolio_analysis", {})
        score = result.get("signal_score", 0.0)
        impact = result.get("impact_estimation", {})

        reply = f"**Market ChatGPT (portfolio-aware) — {current_user.username} — {', '.join(tickers)}:**\n\n"
        reply += "Multi-step ET Markets + NSE data fusion:\n"
        if recommendation:
            reply += f"- **Recommendation:** {recommendation}\n"
        reply += f"- **Signal strength:** {score}/10\n"
        if explanation:
            reply += f"- **Plain-English + backtests:** {explanation}\n"
        if impact.get("fii_dii_snapshot"):
            reply += "- **Institutional flows (NSE):** snapshot attached in impact layer.\n"

        risk = portfolio.get("concentration_risk")
        if risk:
            reply += f"\n⚠️ **Portfolio alert:** {risk}"

        affected = portfolio.get("affected_holdings", [])
        for hold in affected:
            if hold.get("affected_stock") in tickers:
                reply += f"\n💼 **Your holdings:** {hold.get('affected_stock')} is ~{hold.get('portfolio_weight', 0)}% of the book; est. move {hold.get('estimated_impact', 'neutral')}."

        sources = []
        insights = result.get("contextual_insights", [])
        for inc in insights:
            sources.append(f"{inc.get('source')} — {inc.get('insight_type')}")

        return ChatResponse(
            reply=reply,
            sources=list(set(sources)) if sources else ["ET Markets RSS", "NSE public feeds", "ChromaDB RAG", "Neo4j graph"],
        )
    except Exception as e:
        return ChatResponse(
            reply=f"I experienced an orchestration failure analyzing your query: {str(e)}",
            sources=[],
        )
