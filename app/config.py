from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "FlorNya API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change_me"

    DATABASE_URL: str = "postgresql+asyncpg://flornya:flornya@localhost:5432/flornya"
    DATABASE_URL_SYNC: str = "postgresql://flornya:flornya@localhost:5432/flornya"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ENCRYPTION_KEY: str = "EtnUvLd6ix-EUMSARmYglXWYthhSsiYAXGUFT8Q5apk="

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    MINIMUM_AGE: int = 13
    ADULT_CONTENT_AGE: int = 18

    AUTH_LOCKOUT_MAX_ATTEMPTS: int = 10
    AUTH_LOCKOUT_SECONDS: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()
