"""
Tozalash Servis — Asosiy Konfiguratsiya Moduli
Barcha sozlamalar va konstantalar bu yerda saqlanadi (app.core.config.settings dan re-export qilinadi).
"""

import os
import secrets
from pathlib import Path
from loguru import logger as _logger
from app.core.config import settings

# ================================================
# ASOSIY YO'LLAR
# ================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

DATABASE_PATH = str(BASE_DIR / "tozalash.db")
# database.py gets path from env var — set it here for consistency
os.environ.setdefault("DATABASE_PATH", DATABASE_PATH)


# ================================================
# TELEGRAM
# ================================================
TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
ADMIN_TELEGRAM_ID = settings.ADMIN_TELEGRAM_ID
TELEGRAM_CHANNEL = settings.TELEGRAM_CHANNEL

TELEGRAM_API_ID = settings.TELEGRAM_API_ID
TELEGRAM_API_HASH = settings.TELEGRAM_API_HASH

ORDERS_CHANNEL_ID = settings.ORDERS_CHANNEL_ID
ADMIN_USERNAME = settings.ADMIN_USERNAME

# ================================================
# AI (GEMINI)
# ================================================
GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = settings.GEMINI_MODEL
GEMINI_FLASH_MODEL = settings.GEMINI_FLASH_MODEL

# ================================================
# VOICE CLONING (OFFLINE XTTSv2)
# ================================================
OFFLINE_VOICE_CLONING = settings.OFFLINE_VOICE_CLONING
VOICE_REFERENCE_PATH = settings.VOICE_REFERENCE_PATH

# ================================================
# QO'SHIMCHA XIZMATLAR (MONITORING & IZLASH)
# ================================================
SENTRY_DSN = settings.SENTRY_DSN
GOOGLE_SEARCH_API_KEY = settings.GOOGLE_SEARCH_API_KEY
GOOGLE_CX = settings.GOOGLE_CX

# ================================================
# GOOGLE SHEETS
# ================================================
GOOGLE_SHEETS_ID = settings.GOOGLE_SHEETS_ID
GOOGLE_CREDENTIALS_FILE = settings.GOOGLE_CREDENTIALS_FILE

SHEETS = {
    "orders": "Buyurtmalar",
    "clients": "Mijozlar",
    "workers": "Ishchilar",
    "finance": "Moliya",
    "dashboard": "Dashboard",
    "ai_log": "AI_Log",
    "competitors": "Raqiblar",
    "learning": "O'rganish",
}

# ================================================
# INSTAGRAM
# ================================================
INSTAGRAM_ACCESS_TOKEN = settings.INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_BUSINESS_ACCOUNT_ID = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID

# ================================================
# BIZNES MA'LUMOTLARI
# ================================================
BUSINESS_NAME = settings.BUSINESS_NAME
BUSINESS_PHONE = settings.BUSINESS_PHONE
BUSINESS_CITY = settings.BUSINESS_CITY
BUSINESS_TIMEZONE = settings.BUSINESS_TIMEZONE

# ================================================
# NARXLAR (so'mda)
# ================================================
PRICES = {
    "regular_cleaning": {
        "name_uz": "Oddiy/General tozalash",
        "name_ru": "Обычная/Генеральная уборка",
        "name_en": "Regular/Deep Cleaning",
        "price": settings.PRICE_REGULAR_CLEANING,
        "unit": "ishchi",
        "unit_ru": "работник",
        "unit_en": "worker",
    },
    "renovation_cleaning": {
        "name_uz": "Ta'mirdan keyingi tozalash",
        "name_ru": "Уборка после ремонта",
        "name_en": "Post-renovation Cleaning",
        "price": settings.PRICE_RENOVATION_CLEANING,
        "unit": "ishchi",
        "unit_ru": "работник",
        "unit_en": "worker",
    },
    "sofa_cleaning": {
        "name_uz": "Divan yuvish",
        "name_ru": "Мойка дивана",
        "name_en": "Sofa Cleaning",
        "price": settings.PRICE_SOFA_PER_SEAT,
        "unit": "o'rin",
        "unit_ru": "место",
        "unit_en": "seat",
        "minimum": settings.MIN_SOFA_SEATS,
    },
    "chair_cleaning": {
        "name_uz": "Stul yuvish",
        "name_ru": "Мойка стула",
        "name_en": "Chair Cleaning",
        "price": settings.PRICE_CHAIR_PER_UNIT,
        "unit": "dona",
        "unit_ru": "штук",
        "unit_en": "item",
        "minimum": settings.MIN_CHAIRS,
    },
    "carpet_cleaning": {
        "name_uz": "Gilam yuvish",
        "name_ru": "Мойка ковра",
        "name_en": "Carpet Cleaning",
        "price": settings.PRICE_CARPET_PER_SQM,
        "unit": "kv.m",
        "unit_ru": "кв.м",
        "unit_en": "sq.m",
        "minimum": settings.MIN_CARPET_SQM,
    },
    "facade_cleaning": {
        "name_uz": "Fasad tozalash",
        "name_ru": "Чистка фасада",
        "name_en": "Facade Cleaning",
        "price": settings.PRICE_FACADE_PER_SQM,
        "unit": "kv.m",
        "unit_ru": "кв.м",
        "unit_en": "sq.m",
    },
    "tile_cleaning": {
        "name_uz": "Plitka tozalash",
        "name_ru": "Чистка плитки",
        "name_en": "Tile Cleaning",
        "price": settings.PRICE_TILE_PER_SQM,
        "unit": "kv.m",
        "unit_ru": "кв.m",
        "unit_en": "sq.m",
    },
    "window_cleaning": {
        "name_uz": "Oyna tozalash",
        "name_ru": "Мойка окон",
        "name_en": "Window Cleaning",
        "price": 30000,
        "unit": "dona",
        "unit_ru": "штук",
        "unit_en": "item",
    },
    "move_out_cleaning": {
        "name_uz": "Ko'chib ketgandan keyingi tozalash",
        "name_ru": "Уборка после выезда",
        "name_en": "Move-out Cleaning",
        "price": settings.PRICE_RENOVATION_CLEANING,
        "unit": "ishchi",
        "unit_ru": "работник",
        "unit_en": "worker",
    },
}

# ================================================
# TIZIM SOZLAMALARI
# ================================================
LOG_LEVEL = settings.LOG_LEVEL

# Ma'lumotlar bazasi (MySQL)
DB_HOST = settings.DB_HOST
DB_PORT = settings.DB_PORT
DB_USERNAME = settings.DB_USERNAME
DB_PASSWORD = settings.DB_PASSWORD
DB_DATABASE = settings.DB_DATABASE

DAILY_REPORT_TIME = settings.DAILY_REPORT_TIME

# WebSocket va Xavfsizlik
WS_AUTH_TOKEN = settings.WS_AUTH_TOKEN
ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS

# JWT Token konfiguratsiyasi
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

# O'z-o'zini o'rganish
LEARNING_ENABLED = settings.LEARNING_ENABLED
DAILY_IMPROVEMENT_TARGET = settings.DAILY_IMPROVEMENT_TARGET

# ================================================
# KANAL POSTING JADVALI
# ================================================
CHANNEL_POST_TIMES = ["09:00", "12:00", "18:00", "21:00"]
MESSAGES = {}

_INSECURE_WS_TOKENS = {
    "generate_a_strong_token_in_env_file",
    "default_secret_token_change_me",
    "yourwsauthtoken1234567890123456789012345678901234567890",
    "",
}


def validate_config(
    strict: bool = False, raise_on_error: bool = False
) -> tuple[bool, list[str], list[str]]:
    """
    Konfiguratsiyani tekshirish.
    Non-blocking execution: (is_valid, errors, warnings) qaytaradi.
    Loguru orqali ogohlantirishlarni loglaydi.
    Dev rejimida JWT_SECRET_KEY bo'sh yoki placeholder bo'lsa avtomatik hex fallback key yaratadi.
    Faqat strict=True yoki raise_on_error=True ko'rsatilganda va xatolar bor bo'lsa ValueError ko'taradi.
    """
    global JWT_SECRET_KEY
    errors = []
    warnings = []

    # Dev rejimida JWT_SECRET_KEY auto-generation fallback
    if not JWT_SECRET_KEY or JWT_SECRET_KEY in (
        "",
        "your_jwt_secret_key_here",
        "yoursecretkey1234567890123456789012345678901234567890",
    ):
        fallback_key = secrets.token_hex(32)
        JWT_SECRET_KEY = fallback_key
        settings.JWT_SECRET_KEY = fallback_key
        warnings.append(
            "JWT_SECRET_KEY topilmadi yoki standart placeholder. Dev rejimida hex fallback key yaratildi."
        )

    critical_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "ADMIN_TELEGRAM_ID": ADMIN_TELEGRAM_ID,
        "JWT_SECRET_KEY": JWT_SECRET_KEY,
        "WS_AUTH_TOKEN": WS_AUTH_TOKEN,
    }

    for key, value in critical_vars.items():
        if not value or (
            isinstance(value, str)
            and value in ("", "your_bot_token_here", "your_gemini_api_key_here")
        ):
            errors.append(key)
        if isinstance(value, int) and value == 0:
            errors.append(key)

    if WS_AUTH_TOKEN in _INSECURE_WS_TOKENS:
        warnings.append("WS_AUTH_TOKEN (zaif yoki standart qiymat)")

    for w in warnings:
        _logger.warning(f"KONFIGURATSIYA OGOHLANTIRISHI: {w}")

    is_valid = len(errors) == 0

    if (strict or raise_on_error) and errors:
        raise ValueError(
            f"Kritik konfiguratsiya xatoligi! "
            f"Quyidagi .env o'zgaruvchilar yo'q yoki noto'g'ri: {', '.join(errors)}"
        )

    return is_valid, errors, warnings
