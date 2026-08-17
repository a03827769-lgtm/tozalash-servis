import secrets
from pathlib import Path
from typing import List, Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"


class Settings(BaseSettings):
    # Core Metadata
    PROJECT_NAME: str = "Tozalash Servis"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_ID: int = 0
    TELEGRAM_CHANNEL: str = ""
    TELEGRAM_API_ID: str = ""
    TELEGRAM_API_HASH: str = ""
    ORDERS_CHANNEL_ID: str = ""
    ADMIN_USERNAME: str = "abdulloh_ai"

    # AI (Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GEMINI_FLASH_MODEL: str = "gemini-1.5-flash"

    # Voice Cloning
    OFFLINE_VOICE_CLONING: bool = False
    VOICE_REFERENCE_PATH: str = str(DATA_DIR / "mening_ovozim.wav")

    # Services & Monitoring & Search
    SENTRY_DSN: str = ""
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_CX: str = ""

    # Google Sheets & Instagram
    GOOGLE_SHEETS_ID: str = ""
    GOOGLE_CREDENTIALS_FILE: str = str(DATA_DIR / "google_credentials.json")
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""

    # Business Info
    BUSINESS_NAME: str = "Tozalash Servis"
    BUSINESS_PHONE: str = "+998901234567"
    BUSINESS_CITY: str = "Toshkent"
    BUSINESS_TIMEZONE: str = "Asia/Tashkent"

    # Prices (so'mda)
    PRICE_REGULAR_CLEANING: int = 500000
    PRICE_RENOVATION_CLEANING: int = 600000
    PRICE_SOFA_PER_SEAT: int = 80000
    MIN_SOFA_SEATS: int = 5
    PRICE_CHAIR_PER_UNIT: int = 50000
    MIN_CHAIRS: int = 5
    PRICE_CARPET_PER_SQM: int = 27000
    MIN_CARPET_SQM: int = 10
    PRICE_FACADE_PER_SQM: int = 22000
    PRICE_TILE_PER_SQM: int = 15000

    # System & Database (MySQL)
    LOG_LEVEL: str = "INFO"
    DB_HOST: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("DB_HOST", "MYSQL_HOST"),
    )
    DB_PORT: int = Field(
        default=3306,
        validation_alias=AliasChoices("DB_PORT", "MYSQL_PORT"),
    )
    DB_USERNAME: str = Field(
        default="tozalash_user",
        validation_alias=AliasChoices("DB_USERNAME", "MYSQL_USER"),
    )
    DB_PASSWORD: str = Field(
        default="tozalash_password",
        validation_alias=AliasChoices("DB_PASSWORD", "MYSQL_PASSWORD"),
    )
    DB_DATABASE: str = Field(
        default="tozalash_db",
        validation_alias=AliasChoices("DB_DATABASE", "MYSQL_DATABASE"),
    )
    DAILY_REPORT_TIME: str = "21:00"

    # Postgres Legacy (retained for backward compatibility)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "tozalash"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security & Tokens
    JWT_SECRET_KEY: str = ""
    SECRET_KEY: str = "super_secret_key_change_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days (60 * 24 * 8)
    WS_AUTH_TOKEN: str = ""
    ALLOWED_ORIGINS: str = (
        "https://tozalash.uz,https://staging.tozalash.uz,http://localhost:3000"
    )
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Learning
    LEARNING_ENABLED: bool = True
    DAILY_IMPROVEMENT_TARGET: float = 0.05

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def model_post_init(self, __context):
        if (
            self.JWT_SECRET_KEY
            and self.SECRET_KEY == "super_secret_key_change_in_production_1234567890"
        ):
            self.SECRET_KEY = self.JWT_SECRET_KEY

    @property
    def get_database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"mysql+aiomysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"


settings = Settings()
