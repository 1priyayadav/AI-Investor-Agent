import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.core.config import settings
from backend.api.router import api_router, ws_router
from backend.utils.logger import logger
from backend.scheduler.market_scheduler import start_scheduler

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-agent orchestration for financial market insights",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router, prefix="/ws")

os.makedirs(settings.VIDEO_OUTPUT_DIR, exist_ok=True)
app.mount("/static/generated_videos", StaticFiles(directory=settings.VIDEO_OUTPUT_DIR), name="generated_videos")

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME}...")
    try:
        from backend.services.opportunity_radar import opportunity_radar

        opportunity_radar.refresh_global_signals()
    except Exception as e:
        logger.warning(f"Initial opportunity radar refresh skipped: {e}")
    start_scheduler()

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Access /docs for swagger UI.",
        "version": settings.VERSION
    }

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "environment": "development"}
