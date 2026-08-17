"""
Tozalash Servis — ASOSIY ISHGA TUSHIRISH FAYLI (Unified Async Process Supervisor)
Barcha AI agentlar, FastAPI Uvicorn server, Telegram Bot va fon jarayonlari shu yerdan boshlanadi
"""

import fix_time
import asyncio
import sys
import os
import signal
import re
import traceback
from pathlib import Path
from typing import Optional, List
from loguru import logger

# Coqui TTS litsenziyasini avtomatik qabul qilish va UTF-8 konsolni sozlash
os.environ["COQUI_TOS_AGREED"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Loyiha papkasini Python path'ga qo'shish
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    TELEGRAM_BOT_TOKEN,
    GEMINI_API_KEY,
    ADMIN_TELEGRAM_ID,
    BUSINESS_NAME,
    GOOGLE_SHEETS_ID,
    LOGS_DIR,
    LOG_LEVEL,
)

import uvicorn
from app.main import app as fastapi_app
from userbot.main_userbot import run_userbot_async
from channel.content_manager import content_manager
from analytics.competitor_analyzer import competitor_analyzer
from reports.daily_reports import daily_report_system, self_learning_system
from workers.workers_manager import workers_manager
from database import db
from ai_brain import ai_brain, _tts_worker
from voice_agent import voice_agent
from iot_manager import iot_manager
from bigdata_predictor import big_data, pricing_engine
from enterprise_b2b import b2b_manager, profit_analytics
from bot.telegram_bot import run_bot_async
from scheduler_manager import start_scheduler
from keepalive_worker import start_keepalive_worker


def mask_pii(record):
    """Loglarda maxfiy ma'lumotlarni (telefon, TG ID) yashirish (PII masking)"""
    if isinstance(record.get("message"), str):
        msg = record["message"]
        # Telefon raqamlarini yashirish: +998901234567 -> +99890*****67
        msg = re.sub(r"(\+998\d{2})\d{5}(\d{2})", r"\1*****\2", msg)
        # Telegram IDlarni yashirish (kamida 8 ta raqam): 123456789 -> 123***89
        msg = re.sub(r"\b(\d{3})\d{3,}(\d{2})\b", r"\1***\2", msg)
        # Bot tokenlarni yashirish
        msg = re.sub(r"\b(\d{8,10}:)[A-Za-z0-9_-]{35}\b", r"\1***", msg)
        # JWT Tokenlarni yashirish
        msg = re.sub(
            r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", r"eyJ***", msg
        )
        record["message"] = msg


# Logger'ga PII patcherni qo'shish
logger.configure(patcher=mask_pii)

# Loguru sozlash
logger.remove()  # Standart konsol loggerni tozalash
logger.add(lambda msg: print(msg, end="", flush=True), serialize=False, level=LOG_LEVEL)

logger.add(
    LOGS_DIR / "bot_{time}.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level=LOG_LEVEL,
    enqueue=True,
    serialize=True,  # JSON format for ELK / Loki
)


def check_configuration() -> bool:
    """Konfiguratsiyani tekshirish (validate_config() bilan birlashtirildi)."""
    try:
        from config import validate_config

        validate_config()
        return True
    except ValueError as e:
        print(f"\n{e}")
        print("\n📋 Qadamlar:")
        print("  1. .env.example faylini .env ga nusxa oling")
        print("  2. .env faylida barcha qiymatlarni to'ldiring")
        print("  3. Qayta ishga tushiring: python main.py")
        return False
    except Exception as e:
        logger.error(f"Konfiguratsiya tekshirishda kutilmagan xato: {e}")
        return False


async def run_all_systems():
    """Barcha tizimlarni yagona asinxron jarayon boshqaruvchisi (Supervisor) orqali parallel ishga tushirish"""

    logger.info("=" * 60)
    logger.info(f"🚀 {BUSINESS_NAME} — AI Avtomatizatsiya Tizimi (Cloud Supervisor)")
    logger.info("=" * 60)

    # Ma'lumotlar papkalarini yaratish
    os.makedirs(PROJECT_ROOT / "data" / "downloads", exist_ok=True)
    os.makedirs(PROJECT_ROOT / "data" / "audio_cache", exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    logger.info("✅ Ma'lumotlar papkalari tayyor (data/downloads, data/audio_cache, logs)")

    logger.info("📦 Modullar yuklanmoqda...")

    # Tezlikni oshirish uchun TTS modellarini orqa fonda isitish (Pre-Warming)
    try:
        from uzbek_tts import preload_models
        asyncio.create_task(preload_models())
    except Exception as e:
        logger.warning(f"TTS preload ogohlantirish: {e}")

    # 1. Ma'lumotlar bazasini ishga tushirish (PostgreSQL 16 / SQLite WAL)
    await db.init_db()
    try:
        await workers_manager.setup_initial_workers()
    except Exception as e:
        logger.warning(f"Ishchilar sozlashda ogohlantirish: {e}")
    logger.info("✅ Ma'lumotlar bazasi tayyor")

    # 2. Google Sheets CRM (agar sozlangan bo'lsa)
    if GOOGLE_SHEETS_ID and GOOGLE_SHEETS_ID != "your_google_sheets_id_here":
        try:
            from crm.sheets_crm import GoogleSheetsCRM

            crm = GoogleSheetsCRM()
            crm.setup_all_sheets()
            logger.info("✅ Google Sheets CRM tayyor")
        except Exception as e:
            logger.warning(
                f"⚠️ Google Sheets CRM xatosi: {e} (Bot ishlashda davom etadi)"
            )
    else:
        logger.info("ℹ️ Google Sheets CRM o'rnatilmagan (Baza ishlatilmoqda)")

    # 3. Dynamic Port va Uvicorn Server sozlash
    port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn_config = uvicorn.Config(
        app=fastapi_app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(uvicorn_config)

    logger.info(f"🌐 FastAPI & WebSocket server tayyorlandi: http://{host}:{port}")

    # 4. Asinxron vazifalar ro'yxatini yaratish
    tasks: List[asyncio.Task] = []
    stop_event = asyncio.Event()

    # Uvicorn ASGI Server vazifasi
    server_task = asyncio.create_task(server.serve(), name="uvicorn_server")
    tasks.append(server_task)

    # Telegram Bot vazifasi
    bot_task = asyncio.create_task(run_bot_async(), name="telegram_bot")
    tasks.append(bot_task)

    # Telegram UserBot vazifasi
    userbot_task = asyncio.create_task(run_userbot_async(), name="telegram_userbot")
    tasks.append(userbot_task)

    # APScheduler vazifasi
    scheduler_task = asyncio.create_task(
        start_scheduler(
            content_manager,
            competitor_analyzer,
            daily_report_system,
            self_learning_system,
            workers_manager,
            profit_analytics,
            voice_agent,
            stop_event=stop_event,
        ),
        name="apscheduler",
    )
    tasks.append(scheduler_task)

    # TTS Worker vazifasi
    tts_task = asyncio.create_task(_tts_worker(), name="tts_worker")
    tasks.append(tts_task)

    # 24/7 Keepalive Worker vazifasi
    keepalive_task = asyncio.create_task(start_keepalive_worker(), name="keepalive_worker")
    tasks.append(keepalive_task)

    logger.info("🤖 Barcha AI Agentlar va xizmatlar ishga tushirildi:")
    logger.info(f"  ✅ 1. FastAPI Uvicorn Server (Port {port}, REST API, GraphQL, WebSockets, /health)")
    logger.info("  ✅ 2. Telegram Mijoz Boti (24/7 Polling)")
    logger.info("  ✅ 3. Telegram UserBot (Avtomatlashtirilgan DM)")
    logger.info("  ✅ 4. APScheduler (Kontent, Tahlil, P&L, Arxiv)")
    logger.info("  ✅ 5. TTS Audio Queue Worker")
    logger.info("  ✅ 6. 24/7 Keepalive Self-Pinger Worker")
    logger.info(f"📊 Admin ID: {ADMIN_TELEGRAM_ID}")
    logger.info("=" * 60)

    # 5. Graceful Shutdown Signal Handlerlari (POSIX va Windows fallback)
    async def graceful_shutdown(sig_name: Optional[str] = None):
        if sig_name:
            logger.info(f"🛑 Signal {sig_name} qabul qilindi. Tizim xavfsiz to'xtatilmoqda...")
        else:
            logger.info("🛑 Tizim xavfsiz to'xtatilmoqda...")

        stop_event.set()

        # Uvicorn serverni to'xtatish
        server.should_exit = True

        # Boshqa barcha vazifalarni bekor qilish
        for t in tasks:
            if not t.done() and t != asyncio.current_task():
                t.cancel()

        # Ma'lumotlar bazasi pulini yopish
        try:
            if hasattr(db, "close"):
                await db.close()
        except Exception as err:
            logger.warning(f"Baza ulanishini yopishda ogohlantirish: {err}")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(graceful_shutdown(s.name)))
        except (NotImplementedError, AttributeError):
            # Windows OS da loop.add_signal_handler mavjud emas
            pass

    # 6. Barcha vazifalarni nazorat qilish
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, res in enumerate(results):
            task_name = tasks[i].get_name() if hasattr(tasks[i], "get_name") else f"task_{i}"
            if isinstance(res, Exception) and not isinstance(res, asyncio.CancelledError):
                logger.error(f"⚠️ {task_name} xato bilan to'xtadi: {res}")
    except asyncio.CancelledError:
        logger.info("Asosiy supervisor bekor qilindi.")
    finally:
        if not stop_event.is_set():
            await graceful_shutdown()


def main():
    """Asosiy kirish nuqtasi"""
    print(f"""
======================================================
    TOZALASH SERVIS — AI AVTOMATIZATSIYA TIZIMI   
        Powered by Google Gemini AI & FastAPI         
======================================================
    """)

    # Konfiguratsiyani tekshirish
    if not check_configuration():
        sys.exit(1)

    # Sentry integratsiyasi
    from config import SENTRY_DSN

    if SENTRY_DSN and SENTRY_DSN != "your_sentry_dsn_here":
        try:
            import sentry_sdk
            import json

            def sentry_before_send(event, hint):
                try:
                    event_str = json.dumps(event, default=str)
                    event_str = re.sub(
                        r"(\+998\d{2})\d{5}(\d{2})", r"\1*****\2", event_str
                    )
                    event_str = re.sub(
                        r"\b(\d{3})\d{3,}(\d{2})\b", r"\1***\2", event_str
                    )
                    return json.loads(event_str)
                except Exception:
                    return event

            sentry_sdk.init(
                dsn=SENTRY_DSN,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
                before_send=sentry_before_send,
            )
            logger.info("✅ Sentry Monitoring ishga tushdi")
        except ImportError:
            logger.warning(
                "⚠️ sentry-sdk o'rnatilmagan. Sentry monitoringi ishlamaydi."
            )

    logger.info("✅ Konfiguratsiya to'g'ri. Tizim ishga tushirilmoqda...")

    try:
        asyncio.run(run_all_systems())
    except KeyboardInterrupt:
        logger.info("\n👋 Tizim to'xtatildi. Xayr!")
    except Exception as e:
        logger.error(f"💥 Kritik xato: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
