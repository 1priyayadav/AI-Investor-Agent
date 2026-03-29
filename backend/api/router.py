from fastapi import APIRouter
from backend.api.routes import auth, portfolio, alerts, chat, market_data, video, radar
from backend.api.websockets import alerts as ws_alerts

api_router = APIRouter()

# REST Endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(chat.router, prefix="/chat", tags=["Market ChatGPT"])
api_router.include_router(market_data.router, prefix="/market", tags=["Market data"])
api_router.include_router(video.router, prefix="/video", tags=["AI Video Engine"])
api_router.include_router(radar.router, prefix="/radar", tags=["Opportunity Radar"])

# Websocket Endpoints
ws_router = APIRouter()
ws_router.include_router(ws_alerts.router, prefix="/alerts", tags=["WebSockets"])
