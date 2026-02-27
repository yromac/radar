from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Radar"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./radar.db"

    # Google Calendar
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_credentials_file: Optional[str] = "credentials.json"
    google_token_file: Optional[str] = "token.json"

    # Scheduler - hour of day to run the full scrape (24h, local timezone)
    scrape_hour: int = 23  # 11 PM

    # City context
    city: str = "Philadelphia"
    timezone: str = "America/New_York"

    # Base URL of this API server (used to build response links in calendar events)
    app_base_url: str = "http://localhost:8000"

    # Partner API key for business submissions
    partner_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
