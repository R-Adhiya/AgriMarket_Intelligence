from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AgriMarket Intelligence API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database (Phase 2+)
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/agrimarket"

    # Security (Phase 3+)
    SECRET_KEY: str = "change-me-in-production"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
