from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME:    str  = "VAREX Production Calculators"
    APP_VERSION: str  = "2.0.0"
    DEBUG:       bool = False
    LOG_LEVEL:   str  = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
