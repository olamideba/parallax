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
    BACKEND_CORS_ORIGINS: list[str] = Field(default=["https://parallax-five-chi.vercel.app","http://localhost:3000"])

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
    QWEN_MODEL_DEBATE: str = Field(default="qwen3.5-flash")
    QWEN_MODEL_ARBITRATOR: str = Field(default="qwen3.6-flash")
    # Qwen "thinking" mode generates a large hidden reasoning stream — thousands
    # of tokens and 1-3 minutes per call. We turn it off by default: debate turns
    # are conversational (not chain-of-thought), and max_tokens can't bind while
    # thinking is on. Per-role granularity lets you A/B test whether the
    # Arbitrator benefits from thinking (weighing evidence + scoring) without
    # bloating the whole debate. Set to "arbitrator" to enable thinking only for
    # the Arbitrator's final verdict; set to "all" to enable everywhere; "" (empty)
    # disables everywhere (default, fastest).
    QWEN_DEBATE_THINKING: str = Field(default="")
    # DashScope OpenAI-compatible endpoint + embeddings.
    DASHSCOPE_BASE_URL: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    DASHSCOPE_EMBED_MODEL: str = Field(default="text-embedding-v4")
    # Must match the pgvector column dimension (PublicationChunkRecord.embedding).
    DASHSCOPE_EMBED_DIMS: int = Field(default=1024)
    DASHSCOPE_TIMEOUT: float = Field(default=60.0)
    # Reranking (qwen3-rerank) rides on the DASHSCOPE_BASE_URL host via the
    # native rerank service — see adapters/qwen_cloud/reranker.py. WORKSPACE_ID
    # is now only the opt-in switch for wiring the reranker into retrieval.
    DASHSCOPE_WORKSPACE_ID: str = Field(default="")
    DASHSCOPE_RERANK_MODEL: str = Field(default="qwen3-rerank")
    # The reranker has a single, scarce free-quota model, so we conserve calls:
    # short queries (fewer than this many words) skip rerank and use raw vector
    # similarity, which is already good enough for a tight lookup. Set to 0 to
    # rerank every allowed query.
    RERANK_MIN_QUERY_WORDS: int = Field(default=6)

    # Debate
    DEBATE_ROUND_CAP: int = Field(default=3)
    # Max tool-call iterations a single debater gets within one turn.
    DEBATE_MAX_TOOL_ROUNDS: int = Field(default=3)
    # How many baseline corpus chunks are pre-fetched for the debaters.
    DEBATE_BASELINE_CHUNKS: int = Field(default=4)
    # Max consecutive [CONTINUES] turns one debater gets before being cut off
    # (e.g. an Auditor working through a couple of claims one at a time). Kept
    # low: each continuation is another LLM round-trip, so a high cap is what
    # turns a debate into a spiral. A hard safety net independent of the
    # overall turn cap below.
    DEBATE_MAX_CONTINUATIONS: int = Field(default=2)
    # Headroom multiplier on the hard turn cap to leave room for continuations
    # and real back-and-forth beyond "one turn per debater per round". The cap
    # is round_cap * debaters * this — keep modest so the debate can't run away.
    DEBATE_TURN_CAP_MULTIPLIER: int = Field(default=2)
    # Hard per-generation output ceiling for a debater turn. One point per turn
    # should never need more than this; a low cap stops a single turn running to
    # thousands of tokens (which then gets re-billed on every later prompt).
    DEBATE_MAX_TURN_TOKENS: int = Field(default=700)
    # The Arbitrator's final ruling carries a scorecard + rationale + drafted
    # reply, so it gets more room than a single debate turn.
    DEBATE_MAX_ARBITER_TOKENS: int = Field(default=1500)

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
