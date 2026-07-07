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

    APP_ENV: str = Field(default="development")
    LOG_LEVEL: str = Field(default="DEBUG")
    API_V1_PREFIX: str = Field(default="/api/v1")
    BACKEND_CORS_ORIGINS: list[str] = Field(default=["https://parallax-five-chi.vercel.app","http://localhost:3000"])

    DATABASE_URL: str | None = Field(default=None)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="")
    POSTGRES_DB: str = Field(default="parallax")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)

    REDIS_URL_ENV: str | None = Field(default=None, alias="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    DASHSCOPE_API_KEY: str = Field(default="")
    QWEN_MODEL_GATEKEEPER: str = Field(default="qwen-turbo")
    QWEN_MODEL_DEBATE: str = Field(default="qwen3.5-flash")
    QWEN_MODEL_ARBITRATOR: str = Field(default="qwen3.6-flash")
    # Qwen "thinking" mode generates a large hidden reasoning stream — thousands 
    # of tokens and 1-3 minutes per call. We turn it off by default: debate turns
    # are conversational (not chain-of-thought), and max_tokens can't bind while
    # thinking is on.
    QWEN_DEBATE_THINKING: str = Field(default="")
    DASHSCOPE_BASE_URL: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    DASHSCOPE_EMBED_MODEL: str = Field(default="text-embedding-v4")
    DASHSCOPE_EMBED_DIMS: int = Field(default=1024)
    DASHSCOPE_TIMEOUT: float = Field(default=60.0)
    DASHSCOPE_WORKSPACE_ID: str = Field(default="")
    DASHSCOPE_RERANK_MODEL: str = Field(default="qwen3-rerank")

    RERANK_MIN_QUERY_WORDS: int = Field(default=6)


    DASHSCOPE_TTS_ENABLED: bool = Field(default=True)
    DASHSCOPE_TTS_MODEL: str = Field(default="qwen3-tts-flash")
    DASHSCOPE_TTS_TIMEOUT: float = Field(default=60.0)
    # Words to keep a spoken line short enough to sound like speech, not prose.
    DEBATE_SPOKEN_LINE_MAX_WORDS: int = Field(default=55)

    DEBATE_ROUND_CAP: int = Field(default=3)
    DEBATE_MAX_TOOL_ROUNDS: int = Field(default=3)
    DEBATE_BASELINE_CHUNKS: int = Field(default=4)
    DEBATE_MAX_CONTINUATIONS: int = Field(default=2)
    DEBATE_TURN_CAP_MULTIPLIER: int = Field(default=2)
    DEBATE_MAX_TURN_TOKENS: int = Field(default=700)
    DEBATE_MAX_ARBITER_TOKENS: int = Field(default=1500)
    DEBATE_ARBITER_ATTEMPTS: int = Field(default=3)

    R2_ACCOUNT_ID: str = Field(default="")
    R2_ACCESS_KEY_ID: str = Field(default="")
    R2_SECRET_ACCESS_KEY: str = Field(default="")
    R2_BUCKET: str = Field(default="parallax-files")
    R2_PUBLIC_BASE_URL: str = Field(default="")

    INTAKE_WEBHOOK_SECRET: str = Field(default="")

    HMAC_SECRET: str = Field(default="")

    RESEND_WEBHOOK_SECRET: str = Field(default="")
    RESEND_INBOUND_DOMAIN: str = Field(default="")
    RESEND_API_KEY: str = Field(default="")

    BREVO_API_KEY: str = Field(default="")
    BREVO_SENDER_EMAIL: str = Field(default="")
    BREVO_SENDER_NAME: str = Field(default="Parallax")

    SUPABASE_JWT_SECRET: str = Field(default="")
    SUPABASE_URL: str = Field(default="")

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
