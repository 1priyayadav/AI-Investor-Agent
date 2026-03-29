from fastapi import APIRouter, Depends
from backend.api.deps import get_current_user, TokenData
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.services.opportunity_radar import opportunity_radar

router = APIRouter()


class Alert(BaseModel):
    id: str
    ticker: str
    signal_type: str
    confidence: float
    description: str
    timestamp: datetime
    impact_estimate: Optional[str] = None
    action_hint: Optional[str] = None
    source: Optional[str] = None


def _radar_to_alerts() -> List[Alert]:
    out: List[Alert] = []
    for s in opportunity_radar.get_signals(40):
        ts = s.get("timestamp")
        try:
            if isinstance(ts, str):
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            else:
                dt = datetime.utcnow()
        except Exception:
            dt = datetime.utcnow()
        out.append(
            Alert(
                id=s.get("id", "x"),
                ticker=s.get("ticker", "MARKET"),
                signal_type=s.get("signal_type", "RADAR"),
                confidence=float(s.get("confidence", 0.5)),
                description=s.get("description", "")[:2000],
                timestamp=dt,
                impact_estimate=s.get("impact_estimate"),
                action_hint=s.get("action_hint"),
                source=s.get("source"),
            )
        )
    return out


@router.get("/", response_model=List[Alert])
async def get_alerts(current_user: TokenData = Depends(get_current_user)):
    return _radar_to_alerts()
