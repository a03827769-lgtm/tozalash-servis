# Handoff Report — Milestone M1: Config & Secrets Hygiene Investigation

## 1. Observation
Direct, evidence-backed findings from inspection of the codebase:

1. **Root `config.py` vs `app/core/config.py` Discrepancy**:
   - `config.py` (lines 26–218) uses legacy procedural `os.getenv()` calls for Telegram, Gemini AI, MySQL DB (`DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE`), Google Sheets, Instagram, Business Info, Prices, JWT, and WS tokens.
   - `app/core/config.py` (lines 5–38) defines a Pydantic `Settings(BaseSettings)` class that contains outdated Postgres parameters (`POSTGRES_SERVER`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`), `SECRET_KEY`, Redis, and Celery parameters. It does NOT contain Telegram, Gemini, MySQL, or Business settings.
   - `get_database_url` in `app/core/config.py` (lines 35–38) constructs a `postgresql+asyncpg://` URI, whereas the actual database throughout the project (`database.py` lines 8, 23–27) is MySQL via `aiomysql`.

2. **Codebase Import Patterns**:
   - Over 30 files (`main.py`, `ai_agents.py`, `ai_brain.py`, `ws_server.py`, `database.py`, `bot/telegram_bot.py`, `userbot/main_userbot.py`, `crm/sheets_crm.py`, `reports/daily_reports.py`, `bot/handlers/*.py`, etc.) import configuration directly from root `config` (e.g. `from config import TELEGRAM_BOT_TOKEN`, `from config import DB_HOST`).
   - 9 files (`app/core/security.py`, `app/db/session.py`, `app/api/webhooks.py`, `app/core/redis.py`, `app/services/encryption.py`, `app/services/search.py`, `app/workers/celery_app.py`, `alembic/env.py`, `tests/test_core_config_security.py`) import `from app.core.config import settings`.

3. **`validate_config()` Exception Handling & Boot Behavior**:
   - `config.py` (lines 238–275) defines `validate_config()` which raises an unhandled `ValueError` when critical variables (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `ADMIN_TELEGRAM_ID`, `JWT_SECRET_KEY`, `WS_AUTH_TOKEN`) are missing, set to `0`, or match placeholder values.
   - In `main.py` (lines 79–96), `check_configuration()` wraps `validate_config()` in a `try...except ValueError` block.
   - However, if `validate_config()` were executed during module import or inside Pydantic model initialization at import time, placeholder settings in `.env` or missing environment variables cause immediate import-time crashes, preventing tests or CLI utilities from executing in non-production environments.

4. **`.env` Duplication & Format Issues**:
   - `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.env` contains duplicate `WS_AUTH_TOKEN` entries on lines 117 and 118:
     ```env
     117: WS_AUTH_TOKEN=yourwsauthtoken1234567890123456789012345678901234567890
     118: WS_AUTH_TOKEN=super_secure_ws_token_1234567890987654321_strong_enough
     ```
     Line 117 is a duplicate placeholder token, while line 118 is the active secure token.
   - `.env` line 87 contains legacy `DATABASE_PATH=data/tozalash.db` (SQLite path) alongside MySQL credentials (`DB_HOST=127.0.0.1`, `DB_PORT=3306`, etc.).

---

## 2. Logic Chain
1. **Fact**: `app/core/config.py` contains Pydantic `BaseSettings` for Postgres/Celery/Redis, while root `config.py` contains procedural `os.getenv()` calls for MySQL, Telegram, Gemini, and business logic.
   **Inference**: Configuration is split between two incompatible paradigms. The Pydantic model in `app/core/config.py` is stale and doesn't represent the full project settings, while `config.py` lacks Pydantic validation and type safety.
   **Deduction**: We must consolidate all configuration parameters into a unified Pydantic `Settings(BaseSettings)` class in `app/core/config.py`.

2. **Fact**: Over 30 files depend on direct imports from root `config` (`from config import TELEGRAM_BOT_TOKEN`, etc.), while 9 files depend on `from app.core.config import settings`.
   **Inference**: Rewriting 30+ files across the codebase to change import paths risks introducing breaking bugs across multiple modules.
   **Deduction**: `app/core/config.py` should serve as the Pydantic Single Source of Truth (`settings = Settings()`), and root `config.py` should import `settings` from `app.core.config` and re-export top-level constants (`TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN`, `DB_HOST = settings.DB_HOST`, etc.). This achieves 100% backward compatibility without modifying 30+ dependent files.

3. **Fact**: `validate_config()` raises `ValueError` when placeholders are detected. In `main.py`, `check_configuration()` handles `ValueError`, but if `validate_config()` runs at import time or strict mode is mandatory on import, non-production test environments fail.
   **Inference**: Hard crashes on import prevent unit tests, seed scripts, and dev tools from running when default placeholders exist in `.env`.
   **Deduction**: `validate_config()` must support safe, non-blocking execution by default (returning `(is_valid, errors, warnings)` and logging warnings via Loguru), raising `ValueError` only when `strict=True` or `raise_on_error=True` is explicitly passed (e.g. during `main.py` startup). Furthermore, `JWT_SECRET_KEY` should auto-generate a fallback 32-byte hex key in dev mode if missing/blank.

4. **Fact**: `.env` line 117 contains a placeholder `WS_AUTH_TOKEN` immediately followed by line 118 with a strong token.
   **Inference**: Duplicate keys in `.env` cause ambiguity depending on parser load order (e.g. `python-dotenv` vs `pydantic-settings`).
   **Deduction**: Remove line 117 from `.env`. Retain line 118 as the single `WS_AUTH_TOKEN`. Update `.env.example` to document key formats.

---

## 3. Caveats
- **Postgres vs MySQL**: `app/core/config.py` currently defines `POSTGRES_SERVER`, `POSTGRES_USER`, etc. Although the active system uses MySQL (`aiomysql`), `POSTGRES_*` fields should be kept as optional/deprecated in `Settings` or aliased to avoid breaking any legacy external scripts.
- **`SECRET_KEY` vs `JWT_SECRET_KEY`**: `app/core/security.py` accesses `settings.SECRET_KEY`, while `ws_server.py` accesses `JWT_SECRET_KEY`. In `Settings`, `SECRET_KEY` should default to `JWT_SECRET_KEY` if not explicitly provided, keeping both synchronized.
- **Environment Variables**: No actual secrets were modified or exposed during this investigation.

---

## 4. Conclusion & Actionable Recommendations for Worker

### Recommendation 1: Consolidate Configuration in `app/core/config.py`
Rewrite `app/core/config.py` to define a single comprehensive Pydantic `Settings(BaseSettings)` class:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
from typing import List, Dict, Any, Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

class Settings(BaseSettings):
    # Core Metadata
    PROJECT_NAME: str = "Tozalash Servis"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"))
    
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
    
    # Services & Sheets & Instagram
    SENTRY_DSN: str = ""
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_CX: str = ""
    GOOGLE_SHEETS_ID: str = ""
    GOOGLE_CREDENTIALS_FILE: str = str(DATA_DIR / "google_credentials.json")
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    
    # Business Info & Prices
    BUSINESS_NAME: str = "Tozalash Servis"
    BUSINESS_PHONE: str = "+998901234567"
    BUSINESS_CITY: str = "Toshkent"
    BUSINESS_TIMEZONE: str = "Asia/Tashkent"
    
    # System & Database (MySQL)
    LOG_LEVEL: str = "INFO"
    DB_HOST: str = Field(default="127.0.0.1", validation_alias=AliasChoices("DB_HOST", "MYSQL_HOST"))
    DB_PORT: int = Field(default=3306, validation_alias=AliasChoices("DB_PORT", "MYSQL_PORT"))
    DB_USERNAME: str = Field(default="tozalash_user", validation_alias=AliasChoices("DB_USERNAME", "MYSQL_USER"))
    DB_PASSWORD: str = Field(default="tozalash_password", validation_alias=AliasChoices("DB_PASSWORD", "MYSQL_PASSWORD"))
    DB_DATABASE: str = Field(default="tozalash_db", validation_alias=AliasChoices("DB_DATABASE", "MYSQL_DATABASE"))
    DAILY_REPORT_TIME: str = "21:00"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Security & Tokens
    JWT_SECRET_KEY: str = ""
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520 # 8 days
    WS_AUTH_TOKEN: str = ""
    ALLOWED_ORIGINS: str = "https://tozalash.uz,https://staging.tozalash.uz,http://localhost:3000"
    
    # Learning
    LEARNING_ENABLED: bool = True
    DAILY_IMPROVEMENT_TARGET: float = 0.05
    
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    @property
    def get_database_url(self) -> str:
        return f"mysql+aiomysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"

settings = Settings()
```

### Recommendation 2: Refactor Root `config.py` for Backward Compatibility & Non-Blocking Boot
In `config.py`:
1. Import `settings` from `app.core.config`.
2. Re-export constants: `TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN`, `DB_HOST = settings.DB_HOST`, etc.
3. Update `validate_config(strict: bool = False, raise_on_error: bool = False) -> tuple[bool, list[str], list[str]]`:
   - Auto-generate fallback `JWT_SECRET_KEY` via `secrets.token_hex(32)` if empty/placeholder in development mode.
   - Collect errors and warnings into lists.
   - Log warnings using `loguru.logger.warning`.
   - Do NOT raise `ValueError` at module import time.
   - If `strict=True` or `raise_on_error=True`, log errors and raise `ValueError`.

### Recommendation 3: Clean Up `.env` and `.env.example`
1. Open `.env` and remove line 117 (`WS_AUTH_TOKEN=yourwsauthtoken...`), leaving only line 118 (`WS_AUTH_TOKEN=super_secure_ws_token_1234567890987654321_strong_enough`).
2. Add header documentation in `.env.example` specifying key requirements (e.g. minimum 32 characters for `JWT_SECRET_KEY` and `WS_AUTH_TOKEN`).

---

## 5. Verification Method

To independently verify the implementation after Worker execution:

1. **Syntax & Unit Test Verification**:
   Run core configuration and security tests:
   ```pwsh
   python -m pytest tests/test_core_config_security.py tests/test_core.py
   ```
   *Expected Result*: 100% pass with 0 errors.

2. **Non-Blocking Boot Verification**:
   Execute a dry import of `config.py`:
   ```pwsh
   python -c "import config; print('Config loaded successfully:', config.BUSINESS_NAME)"
   ```
   *Expected Result*: Outputs `Config loaded successfully: Tozalash Servis` without raising `ValueError`.

3. **`.env` Duplicate Check**:
   Run PowerShell query to check for duplicate keys in `.env`:
   ```pwsh
   powershell -Command "Get-Content .env | Select-String -Pattern '^WS_AUTH_TOKEN='"
   ```
   *Expected Result*: Exactly 1 line returned.

4. **Backward Compatibility Verification**:
   Verify that `from config import TELEGRAM_BOT_TOKEN, DB_HOST` still resolves correctly across the application.
