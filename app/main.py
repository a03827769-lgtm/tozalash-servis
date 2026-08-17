import time
import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
import os
import sys

# root directory ni path ga qoshamiz to config.py import qilish uchun
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import SENTRY_DSN
from database import db
from app.core.redis_manager import redis_manager

if SENTRY_DSN and SENTRY_DSN != "your_sentry_dsn_here":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
import uvicorn
from contextlib import asynccontextmanager
from loguru import logger

# Import config, security, routers
from app.api.api_router import api_router
from app.core.redis import init_redis

SERVER_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global SERVER_START_TIME
    SERVER_START_TIME = time.time()
    logger.info("Starting up FastAPI Server...")
    
    # 1. Initialize Redis & Cache
    try:
        await init_redis(app)
    except Exception as e:
        logger.warning(f"init_redis xatosi: {e}")

    try:
        await redis_manager.init()
    except Exception as e:
        logger.warning(f"redis_manager.init xatosi: {e}")

    # 2. Initialize Database connection & tables
    try:
        await db.init_db()
    except Exception as e:
        logger.error(f"db.init_db xatosi: {e}")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI Server...")
    try:
        await db.close()
    except Exception:
        pass
    try:
        await redis_manager.close()
    except Exception:
        pass


app = FastAPI(
    title="Tozalash Servis API",
    version="2.0.0",
    description="FastAPI, GraphQL and Microservices backend",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "https://tozalash.uz,http://localhost:3000"
).split(",")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.graphql import graphql_app
from app.api.websockets import router as ws_router

app.include_router(graphql_app, prefix="/graphql")
app.include_router(ws_router)

from app.core.metrics import metrics_app
from prometheus_fastapi_instrumentator import Instrumentator

# Prometheus metrics endpoint
app.mount("/metrics", metrics_app)
Instrumentator().instrument(app).expose(app, endpoint="/metrics_instrumentator")

from fastapi.responses import HTMLResponse

# Include main API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def root_portal():
    """Tozalash Servis — Asosiy Boshqaruv va Veb Portal (Landing & API Console)"""
    uptime = round(time.time() - SERVER_START_TIME, 1)
    html_content = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tozalash Servis — AI Avtomatizatsiya & 24/7 Bulutli Portal</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #090d16;
            --card-bg: rgba(18, 24, 38, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.35);
            --accent: #10b981;
            --accent-glow: rgba(16, 185, 129, 0.3);
            --text: #f3f4f6;
            --text-muted: #9ca3af;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem 1rem;
            position: relative;
            overflow-x: hidden;
        }}
        .bg-glow {{
            position: absolute;
            top: -20%;
            left: 50%;
            transform: translateX(-50%);
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(16, 185, 129, 0.05) 45%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }}
        .container {{
            max-width: 900px;
            width: 100%;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            backdrop-filter: blur(16px);
            padding: 3rem 2.5rem;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
            position: relative;
            z-index: 1;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.25);
            color: #34d399;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            box-shadow: 0 0 15px var(--accent-glow);
        }}
        .status-dot {{
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.85); }}
        }}
        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.75rem;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        p.subtitle {{
            color: var(--text-muted);
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 2.5rem;
            max-width: 680px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.25s ease;
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .card:hover {{
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(59, 130, 246, 0.4);
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(59, 130, 246, 0.15);
        }}
        .card-icon {{
            font-size: 1.75rem;
            margin-bottom: 0.75rem;
        }}
        .card-title {{
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
            color: #ffffff;
        }}
        .card-desc {{
            font-size: 0.9rem;
            color: var(--text-muted);
            line-height: 1.4;
        }}
        .cta-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 14px 28px;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            border-radius: 12px;
            font-weight: 700;
            font-size: 1rem;
            text-decoration: none;
            box-shadow: 0 4px 20px var(--primary-glow);
            transition: all 0.2s ease;
        }}
        .cta-btn:hover {{
            transform: scale(1.02);
            box-shadow: 0 6px 25px rgba(37, 99, 235, 0.5);
        }}
        .footer {{
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            flex-wrap: wrap;
            gap: 0.75rem;
        }}
    </style>
</head>
<body>
    <div class="bg-glow"></div>
    <div class="container">
        <div class="header">
            <span class="badge">
                <span class="status-dot"></span> Tizim 24/7 Doimiy Faol
            </span>
            <span style="font-size: 0.85rem; color: var(--text-muted);">Uptime: {uptime}s</span>
        </div>

        <h1>Tozalash Servis AI</h1>
        <p class="subtitle">
            Tozalash xizmatlarini avtomatlashtirish, Telegram AI bot, ovozli xizmat (TTS/STT), 
            real-time buyurtmalar boshqaruvi va mikroservislar markaziy portali.
        </p>

        <div class="grid">
            <a href="https://t.me/fwf32vbot" target="_blank" class="card" style="border-color: rgba(59, 130, 246, 0.35);">
                <div>
                    <div class="card-icon">🤖</div>
                    <div class="card-title">Telegram Mijoz Boti</div>
                    <div class="card-desc">@fwf32vbot — AI orqali tozalash buyurtma berish, narx hisoblash va ovozli suhbat.</div>
                </div>
                <div style="margin-top: 1rem; font-weight: 600; color: #60a5fa; font-size: 0.875rem;">Botni ochish &rarr;</div>
            </a>

            <a href="/docs" target="_blank" class="card">
                <div>
                    <div class="card-icon">⚡</div>
                    <div class="card-title">Interactive API Docs</div>
                    <div class="card-desc">Swagger UI interfeysi orqali barcha REST API va mikroservis endpointlarini sinab ko'rish.</div>
                </div>
                <div style="margin-top: 1rem; font-weight: 600; color: #60a5fa; font-size: 0.875rem;">/docs ochish &rarr;</div>
            </a>

            <a href="/health" target="_blank" class="card">
                <div>
                    <div class="card-icon">🏥</div>
                    <div class="card-title">Health Monitoring</div>
                    <div class="card-desc">Ma'lumotlar bazasi, Redis kesh, xotira va tizim salomatligi holati.</div>
                </div>
                <div style="margin-top: 1rem; font-weight: 600; color: #34d399; font-size: 0.875rem;">/health ko'rish &rarr;</div>
            </a>

            <a href="/graphql" target="_blank" class="card">
                <div>
                    <div class="card-icon">📊</div>
                    <div class="card-title">GraphQL Studio</div>
                    <div class="card-desc">Buyurtmalar, xodimlar va statistika uchun moslashuvchan GraphQL query konsoli.</div>
                </div>
                <div style="margin-top: 1rem; font-weight: 600; color: #60a5fa; font-size: 0.875rem;">/graphql ochish &rarr;</div>
            </a>
        </div>

        <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
            <a href="https://t.me/fwf32vbot" target="_blank" class="cta-btn">
                <span>🚀 Telegram Botni Ishga Tushirish</span>
            </a>
            <a href="/docs" target="_blank" style="color: var(--text-muted); text-decoration: none; font-size: 0.95rem; padding: 12px 18px; border: 1px solid var(--card-border); border-radius: 12px;">
                📚 API Hujjatlari (/docs)
            </a>
        </div>

        <div class="footer">
            <span>&copy; 2026 Tozalash Servis Platform. Barcha huquqlar himoyalangan.</span>
            <span>FastAPI 2.0 &bull; Cloudflare Anycast CDN &bull; Python 3.11</span>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    # 1. DB Health Check
    db_status = "offline"
    try:
        if db:
            row = await asyncio.wait_for(db.fetch_one("SELECT 1 as ping"), timeout=1.0)
            if row and (row.get("ping") == 1 or row.get("?column?") == 1 or 1 in row.values()):
                db_status = "connected"
    except Exception as e:
        logger.warning(f"Health DB ping warning: {e}")
        db_status = "offline"

    # 2. Redis Health Check
    redis_status = "memory_fallback"
    try:
        if getattr(redis_manager, "_is_connected", False) and getattr(redis_manager, "client", None):
            await asyncio.wait_for(redis_manager.client.ping(), timeout=0.5)
            redis_status = "connected"
    except Exception:
        redis_status = "memory_fallback"

    uptime = round(time.time() - SERVER_START_TIME, 2)
    overall_status = "healthy" if db_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "redis": redis_status,
        "uptime_seconds": uptime,
        "version": "2.0.0",
        "message": "Tozalash Servis API is running"
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
