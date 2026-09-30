from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AgriMarket Intelligence API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/agrimarket"

    # JWT / Auth
    SECRET_KEY: str = "replace-with-a-secure-development-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Admin seed (development only)
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "change-this-password"

    # Transport cost estimation (Phase 6)
    # Formula: base_cost + (distance_km * rate_per_km * quantity_quintals)
    # These are development assumptions — not real commercial quotes.
    TRANSPORT_BASE_COST: float = 200.0      # INR — minimum truck hire charge
    TRANSPORT_RATE_PER_KM: float = 2.5      # INR per km per quintal-equivalent
    TRANSPORT_QUANTITY_UNIT: str = "quintal"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
