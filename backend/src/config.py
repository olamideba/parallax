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
    # DashScope OpenAI-compatible endpoint + embeddings.
    DASHSCOPE_BASE_URL: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    DASHSCOPE_EMBED_MODEL: str = Field(default="text-embedding-v4")
    # Must match the pgvector column dimension (PublicationChunkRecord.embedding).
    DASHSCOPE_EMBED_DIMS: int = Field(default=1024)
    DASHSCOPE_TIMEOUT: float = Field(default=60.0)
    # Reranking (qwen3-rerank) lives on a workspace-scoped host, distinct from
    # DASHSCOPE_BASE_URL — see adapters/qwen_cloud/reranker.py.
    DASHSCOPE_WORKSPACE_ID: str = Field(default="")
    DASHSCOPE_RERANK_MODEL: str = Field(default="qwen3-rerank")
    DASHSCOPE_RERANK_REGION: str = Field(default="ap-southeast-1")

    # Debate
    DEBATE_ROUND_CAP: int = Field(default=3)
    # Max tool-call iterations a single debater gets within one turn.
    DEBATE_MAX_TOOL_ROUNDS: int = Field(default=3)
    # How many baseline corpus chunks are pre-fetched for the debaters.
    DEBATE_BASELINE_CHUNKS: int = Field(default=4)

    # Cloudflare R2
    R2_ACCOUNT_ID: str = Field(default="")
    R2_ACCESS_KEY_ID: str = Field(default="")
    R2_SECRET_ACCESS_KEY: str = Field(default="")
    R2_BUCKET: str = Field(default="parallax-files")
    R2_PUBLIC_BASE_URL: str = Field(default="")

    # Email intake
    INTAKE_WEBHOOK_SECRET: str = Field(default="")

    # Intake address derivation
    HMAC_SECRET: str = Field(default="")

    # Resend (inbound / receiving)
    RESEND_WEBHOOK_SECRET: str = Field(default="")
    RESEND_INBOUND_DOMAIN: str = Field(default="")
    RESEND_API_KEY: str = Field(default="")

    # Brevo (outbound / sending)
    BREVO_API_KEY: str = Field(default="")
    BREVO_SENDER_EMAIL: str = Field(default="")
    BREVO_SENDER_NAME: str = Field(default="Parallax")

    # Supabase Auth
    SUPABASE_JWT_SECRET: str = Field(default="")
    SUPABASE_URL: str = Field(default="")

    # Publication ingestion
    UNPAYWALL_EMAIL: str = Field(default="")
    INGEST_CHUNK_SIZE: int = Field(default=2000)
    INGEST_CHUNK_OVERLAP: int = Field(default=200)
    INGEST_HTTP_TIMEOUT: float = Field(default=60.0)
    UPLOAD_MAX_MB: int = Field(default=25)

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
