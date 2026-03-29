from fastapi import APIRouter, Depends

from backend.api.deps import TokenData, get_optional_user
from backend.services.market_video_engine import market_video_engine

router = APIRouter()


@router.post("/daily-wrap")
async def generate_daily_wrap(current_user: TokenData = Depends(get_optional_user)):
    meta = market_video_engine.generate_daily_wrap_video()
    return {"status": "ok", "user": current_user.username, **meta}
