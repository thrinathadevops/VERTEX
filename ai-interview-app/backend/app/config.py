from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "VAREX AI Interview App"
    DATABASE_URL: str = "postgresql+psycopg2://ai_interview:ai_interview_password@ai_interview_db:5432/ai_interview_db"
    ALLOWED_ORIGINS: str = "http://localhost:3010,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
