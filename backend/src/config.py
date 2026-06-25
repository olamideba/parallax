from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_ENV: str = Field(default="development")
    LOG_LEVEL: str = Field(default="DEBUG")
    API_V1_PREFIX: str = Field(default="/api/v1")
    BACKEND_CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    # Database
    DATABASE_URL: str | None = Field(default=None)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="")
    POSTGRES_DB: str = Field(default="parallax")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)

    # Redis
    REDIS_URL_ENV: str | None = Field(default=None, alias="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    # Qwen / DashScope
    DASHSCOPE_API_KEY: str = Field(default="")
    QWEN_MODEL_GATEKEEPER: str = Field(default="qwen-turbo")
    QWEN_MODEL_DEBATE: str = Field(default="qwen-plus")
    QWEN_MODEL_ARBITRATOR: str = Field(default="qwen-plus")

    # Debate
    DEBATE_ROUND_CAP: int = Field(default=3)

    # Cloudflare R2
    R2_ACCOUNT_ID: str = Field(default="")
    R2_ACCESS_KEY_ID: str = Field(default="")
    R2_SECRET_ACCESS_KEY: str = Field(default="")
    R2_BUCKET: str = Field(default="parallax-files")
    R2_PUBLIC_BASE_URL: str = Field(default="")

    # Email intake
    INTAKE_WEBHOOK_SECRET: str = Field(default="")

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_URL_ENV:
            return self.REDIS_URL_ENV
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @computed_field
    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.REDIS_URL

    @computed_field
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.REDIS_URL

    @computed_field
    @property
    def R2_ENDPOINT_URL(self) -> str:
        if not self.R2_ACCOUNT_ID:
            return ""
        return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                return "postgresql+asyncpg://" + url[len("postgres://"):]
            if url.startswith("postgresql://"):
                return "postgresql+asyncpg://" + url[len("postgresql://"):]
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
