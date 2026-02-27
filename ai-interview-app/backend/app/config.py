from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "VAREX AI Interview App"
    DATABASE_URL: str = "postgresql+psycopg2://ai_interview:ai_interview_password@ai_interview_db:5432/ai_interview_db"
    ALLOWED_ORIGINS: str = "http://localhost:3010,http://localhost:3000"

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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
