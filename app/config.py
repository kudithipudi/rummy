from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Rummy Score Tracker"
    debug: bool = True

    # Database
    sqlite_db_path: str = "data/rummy.db"

    # Email Service
    mailjet_api_key: str
    mailjet_api_secret: str
    from_email: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"

    # App
    app_url: str = "http://localhost:8000"
    base_path: str = ""  # e.g., "/rummy" if app is deployed in subdirectory

    class Config:
        env_file = ".env"


settings = Settings()