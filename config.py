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

    # Scheduler - how often to re-scrape (in minutes)
    scrape_interval_minutes: int = 60

    # City context
    city: str = "Philadelphia"
    timezone: str = "America/New_York"

    # Partner API key for business submissions
    partner_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
