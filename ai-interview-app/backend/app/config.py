from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "VAREX AI Interview Platform"
    DATABASE_URL: str = "postgresql+psycopg2://ai_interview:ai_interview_password@ai_interview_db:5432/ai_interview_db"
    ALLOWED_ORIGINS: str = "http://localhost:3010,http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:3010"

    # ─── JWT Authentication ────────────────────────────────────
    SECRET_KEY: str = "change-this-to-a-strong-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    INTERVIEW_TOKEN_EXPIRE_MINUTES: int = 180
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@varextech.in"

    # ─── AI Provider settings ──────────────────────────────────
    AI_PROVIDER: str = "gemini"  # openai | gemini | ollama

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Ollama (self-hosted)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"

    # ─── Resume upload ─────────────────────────────────────────
    MAX_RESUME_SIZE_MB: int = 5

    # ─── Interview Timer Defaults ──────────────────────────────
    DEFAULT_TOTAL_TIME_SECONDS: int = 2700       # 45 minutes
    DEFAULT_QUESTION_TIME_SECONDS: int = 300     # 5 minutes per question

    # ─── Anti-cheat thresholds ─────────────────────────────────
    MAX_TAB_SWITCHES_BEFORE_FLAG: int = 3
    PROCTOR_SHARED_SECRET: str = ""
    PROCTOR_REQUIRE_FOR_ENTERPRISE: bool = True
    PROCTOR_HEARTBEAT_MAX_GAP_SECONDS: int = 30
    PROCTOR_START_GRACE_SECONDS: int = 90
    PROCTOR_EVENT_DEDUP_WINDOW_SECONDS: int = 60

    # ─── Question counts per mode ──────────────────────────────
    QUESTIONS_MOCK_FREE: int = 5
    QUESTIONS_MOCK_PAID: int = 8
    QUESTIONS_ENTERPRISE: int = 12

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
