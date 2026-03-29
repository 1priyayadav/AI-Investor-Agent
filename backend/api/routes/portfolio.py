from fastapi import APIRouter, Depends
from backend.api.deps import get_current_user, TokenData
from pydantic import BaseModel
from typing import List, Dict

from backend.analysis.portfolio import portfolio_analyzer

router = APIRouter()


class PortfolioItem(BaseModel):
    ticker: str
    shares: float
    average_price: float


class PortfolioResponse(BaseModel):
    username: str
    holdings: List[PortfolioItem]
    total_value: float = 0.0
    sector_exposure: Dict[str, float] = {}


# Mock DB — Indian-heavy default for demo
MOCK_PORTFOLIOS = {
    "testuser": [
        PortfolioItem(ticker="RELIANCE.NS", shares=20, average_price=2450.0),
        PortfolioItem(ticker="INFY.NS", shares=15, average_price=1520.0),
        PortfolioItem(ticker="ICICIBANK.NS", shares=40, average_price=1100.0),
    ]
}


@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(current_user: TokenData = Depends(get_current_user)):
    holdings = MOCK_PORTFOLIOS.get(current_user.username, [])
    hd = [h.model_dump() for h in holdings]
    analysis = portfolio_analyzer.analyze_portfolio(hd, [])
    return PortfolioResponse(
        username=current_user.username,
        holdings=holdings,
        total_value=float(analysis.get("total_value", 0)),
        sector_exposure=analysis.get("sector_exposure", {}),
    )


@router.post("/")
async def update_portfolio(items: List[PortfolioItem], current_user: TokenData = Depends(get_current_user)):
    MOCK_PORTFOLIOS[current_user.username] = items
    hd = [h.model_dump() for h in items]
    analysis = portfolio_analyzer.analyze_portfolio(hd, [])
    return {
        "message": "Portfolio updated successfully",
        "holdings": items,
        "total_value": analysis.get("total_value"),
        "sector_exposure": analysis.get("sector_exposure"),
    }
