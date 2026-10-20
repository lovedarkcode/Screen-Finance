"""Application configuration loaded from environment variables / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "Screen Finance API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    PORT: int = Field(default=8000, ge=1, le=65535)

    BACKEND_CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
        ]
    )

    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/screenfinance")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    QDRANT_URL: str = Field(default="http://localhost:6333")

    JWT_SECRET_KEY: str = Field(default="change-me-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)

    OPENAI_API_KEY: str | None = None
    NVIDIA_API_KEY: SecretStr | None = None
    NVIDIA_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    NVIDIA_SCREENER_MODEL: str | None = None
    NEBIUS_API_KEY: SecretStr | None = None
    NEBIUS_BASE_URL: str = "https://api.tokenfactory.us-central1.nebius.com/v1/"
    NEBIUS_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"
    FMP_API_KEY: SecretStr | None = Field(default=None, validation_alias=AliasChoices("FMP_API_KEY", "FMP"))
    RESULTS_TICKERS: str = "RELIANCE.NS,TATASTEEL.NS,AAPL,MSFT"
    RESULTS_AI_BATCH_SIZE: int = Field(default=8, ge=1, le=32)
    RESULTS_BATCH_SIZE: int = Field(default=150, ge=1, le=200)
    RESULTS_REQUEST_DELAY: float = Field(default=1.0, ge=0.5, le=30)
    RESULTS_REFRESH_HOURS: int = Field(default=24, ge=6, le=168)

    @field_validator("NEBIUS_BASE_URL", mode="before")
    @classmethod
    def resolve_nebius_website(cls, value):
        # Marketing-site URLs are aliases, never destinations for API credentials.
        if isinstance(value, str) and value.rstrip("/") in ("https://nebius.ai", "https://nebius.com"):
            return "https://api.tokenfactory.us-central1.nebius.com/v1/"
        return value

    @property
    def ai_provider(self) -> str:
        return "Nebius" if self.NEBIUS_API_KEY and self.NEBIUS_API_KEY.get_secret_value().strip() else "NVIDIA"

    @property
    def ai_api_key(self) -> SecretStr | None:
        return self.NEBIUS_API_KEY if self.ai_provider == "Nebius" else self.NVIDIA_API_KEY

    @property
    def ai_base_url(self) -> str:
        return self.NEBIUS_BASE_URL if self.ai_provider == "Nebius" else "https://integrate.api.nvidia.com/v1"

    @property
    def ai_model(self) -> str:
        return self.NEBIUS_MODEL if self.ai_provider == "Nebius" else self.NVIDIA_MODEL

    @property
    def screener_model(self) -> str:
        return self.NEBIUS_MODEL if self.ai_provider == "Nebius" else self.NVIDIA_SCREENER_MODEL or self.NVIDIA_MODEL

    FINNHUB_API_KEY: str | None = None
    ALPHA_VANTAGE_API_KEY: str | None = None
    POLYGON_API_KEY: str | None = None

    GOOGLE_CLIENT_ID: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
