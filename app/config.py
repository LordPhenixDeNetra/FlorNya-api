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

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    # starttls (port 587, la plupart des providers) | ssl (port 465) | none (port 25 / dev)
    SMTP_TLS_MODE: str = "starttls"
    EMAIL_FROM: str = "noreply@flornya.app"
    FRONTEND_URL: str = "http://localhost:5173"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60

    # 2FA
    TOTP_ISSUER: str = "FlorNya"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ESSENTIAL: str = ""
    STRIPE_PRICE_BLOOM: str = ""
    STRIPE_PRICE_BLOOM_PRO: str = ""

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    AI_INSIGHTS_MODEL: str = "claude-haiku-4-5-20251001"

    # Rate limiting avancé
    RATE_LIMIT_AI: str = "20/hour"
    RATE_LIMIT_REPORTS: str = "5/day"
    RATE_LIMIT_PASSWORD_RESET: str = "5/minute"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    # Firebase Cloud Messaging (push notifications)
    FIREBASE_CREDENTIALS_PATH: str = ""
    FIREBASE_PROJECT_ID: str = ""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # S3 / Object storage (photo upload)
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "eu-west-3"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AVATAR_MAX_SIZE_MB: int = 5

    # Admin
    ADMIN_API_KEY: str = ""

    # Beta access
    BETA_INVITE_CODE: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
