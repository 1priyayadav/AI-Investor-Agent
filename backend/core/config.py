import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Investor Intelligence Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Data Stores
    REDIS_URL: str = "redis://localhost:6379"
    NEO4J_URI: str = "bolt://localhost:7687"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # Indian markets & ET integration
    ET_MARKETS_RSS_URL: str = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    NSE_SCAN_TOP_N: int = 120
    NSE_UNIVERSE_FILE: str = str(_BASE / "data" / "nse_liquid_universe.json")
    VIDEO_OUTPUT_DIR: str = str(_BASE / "static" / "generated_videos")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
