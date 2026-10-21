"""Application configuration and environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "ATIP API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-me-in-production-atip-secret-key-32-chars-min"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://atip:atip_dev_password@localhost:5432/atip_db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis Cache & Ephemeral State
    REDIS_URL: str = "redis://localhost:6379/0"

    # RabbitMQ durable messaging
    RABBITMQ_URL: str = "amqp://atip:atip_dev_password@localhost:5672/"

    # S3 Object Storage (MinIO local)
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "atipadmin"
    S3_SECRET_ACCESS_KEY: str = "atipsecretpassword"
    S3_BUCKET_NAME: str = "atip-artifacts"
    S3_REGION: str = "us-east-1"

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])
    ALLOWED_HOSTS: list[str] = Field(default=["*"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
