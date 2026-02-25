from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str = "postgresql+asyncpg://varex_user:password@localhost:5432/varex_db"
    SECRET_KEY: str = "insecure-default-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://varextech.com"]
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "ap-south-1"


settings = Settings()
