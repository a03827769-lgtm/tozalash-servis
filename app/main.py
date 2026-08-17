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

from app.core.middleware import (
    SecurityHeadersMiddleware,
    ServerTimingMiddleware,
    RateLimitingMiddleware,
    IdempotencyMiddleware
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ServerTimingMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(IdempotencyMiddleware)


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


@app.get("/tma", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
async def tma_app():
    """Tozalash Servis — TMA 2.0 Next-Gen Luxury WebApp"""
    html_content = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Tozalash Servis — Premium Cleaning Ecosystem</title>
    <!-- Telegram WebApp SDK -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #07090e;
            --surface-1: #0f131d;
            --surface-2: #161c2b;
            --surface-3: #1f273d;
            --border: rgba(255, 255, 255, 0.08);
            --border-active: rgba(59, 130, 246, 0.6);
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.35);
            --emerald: #10b981;
            --emerald-glow: rgba(16, 185, 129, 0.25);
            --amber: #f59e0b;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --text-dim: #64748b;
            --radius-xl: 20px;
            --radius-lg: 14px;
            --radius-md: 10px;
        }
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            padding: 1rem 1rem calc(5.5rem + env(safe-area-inset-bottom, 20px)) 1rem;
            position: relative;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.15), transparent 60%),
                radial-gradient(circle at 100% 100%, rgba(16, 185, 129, 0.08), transparent 50%);
        }

        /* Top Header */
        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.25rem;
            padding-bottom: 0.85rem;
            border-bottom: 1px solid var(--border);
        }
        .brand-group {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .brand-icon {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 14px var(--primary-glow);
        }
        .brand-icon svg { width: 22px; height: 22px; fill: white; }
        .brand-title { font-weight: 800; font-size: 1.05rem; letter-spacing: -0.02em; }
        .brand-status { font-size: 0.72rem; color: var(--emerald); font-weight: 600; display: flex; align-items: center; gap: 4px; }
        .brand-status::before { content: ""; width: 6px; height: 6px; background: var(--emerald); border-radius: 50%; box-shadow: 0 0 8px var(--emerald); }
        .user-pill {
            background: var(--surface-2);
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            color: #93c5fd;
        }

        /* Stepper Progress */
        .stepper {
            display: flex;
            justify-content: space-between;
            position: relative;
            margin-bottom: 1.5rem;
            padding: 0 0.5rem;
        }
        .stepper::before {
            content: "";
            position: absolute;
            top: 14px;
            left: 24px;
            right: 24px;
            height: 2px;
            background: var(--surface-3);
            z-index: 1;
        }
        .step-progress-bar {
            position: absolute;
            top: 14px;
            left: 24px;
            height: 2px;
            background: var(--primary);
            z-index: 2;
            transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 8px var(--primary);
        }
        .step-node {
            position: relative;
            z-index: 3;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            cursor: pointer;
        }
        .step-dot {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: var(--surface-2);
            border: 2px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-dim);
            transition: all 0.3s ease;
        }
        .step-node.active .step-dot {
            background: var(--primary);
            border-color: #60a5fa;
            color: white;
            box-shadow: 0 0 12px var(--primary-glow);
            transform: scale(1.1);
        }
        .step-node.completed .step-dot {
            background: var(--emerald);
            border-color: #34d399;
            color: white;
        }
        .step-label {
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--text-dim);
            transition: color 0.3s;
        }
        .step-node.active .step-label { color: var(--text-main); font-weight: 700; }

        /* Step View Containers */
        .step-view { display: none; animation: fadeIn 0.3s ease forwards; }
        .step-view.active { display: block; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .heading-xl { font-size: 1.15rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 0.35rem; }
        .heading-sub { font-size: 0.82rem; color: var(--text-sub); margin-bottom: 1.1rem; }

        /* Service Cards Grid */
        .services-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        .service-tile {
            background: var(--surface-1);
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            padding: 1.1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .service-tile:active { transform: scale(0.98); }
        .service-tile.selected {
            background: linear-gradient(135deg, rgba(30, 58, 138, 0.35) 0%, rgba(15, 23, 42, 0.8) 100%);
            border-color: var(--primary);
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.2), inset 0 0 0 1px rgba(96, 165, 250, 0.3);
        }
        .service-media {
            width: 52px;
            height: 52px;
            border-radius: 14px;
            background: var(--surface-2);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform 0.3s;
        }
        .service-tile.selected .service-media {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            transform: rotate(-4deg);
        }
        .service-media svg { width: 26px; height: 26px; stroke: #93c5fd; fill: none; }
        .service-tile.selected .service-media svg { stroke: white; }
        .service-details { flex: 1; min-width: 0; }
        .service-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 3px; }
        .service-name { font-weight: 700; font-size: 0.95rem; }
        .service-badge {
            font-size: 0.68rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 8px;
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .service-desc { font-size: 0.77rem; color: var(--text-sub); margin-bottom: 6px; line-height: 1.3; }
        .service-meta { display: flex; align-items: center; justify-content: space-between; }
        .service-rate { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.9rem; color: #60a5fa; }
        .check-indicator {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 2px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .service-tile.selected .check-indicator {
            background: var(--primary);
            border-color: var(--primary);
        }
        .check-indicator svg { width: 12px; height: 12px; stroke: white; fill: none; stroke-width: 3; display: none; }
        .service-tile.selected .check-indicator svg { display: block; }

        /* Step 2: Customization */
        .glass-card {
            background: var(--surface-1);
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            padding: 1.25rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(12px);
        }
        .counter-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        .counter-label { font-size: 0.9rem; font-weight: 700; }
        .counter-sub { font-size: 0.75rem; color: var(--text-sub); }
        .counter-ctrl {
            display: flex;
            align-items: center;
            gap: 12px;
            background: var(--surface-2);
            padding: 4px;
            border-radius: 14px;
            border: 1px solid var(--border);
        }
        .counter-btn {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            background: var(--surface-3);
            border: none;
            color: white;
            font-size: 1.2rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background 0.2s;
        }
        .counter-btn:active { background: var(--primary); }
        .counter-val { font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 800; min-width: 36px; text-align: center; color: #93c5fd; }

        .slider-wrap { margin-top: 1rem; }
        .slider-meta { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.82rem; }
        .slider-meta strong { color: #60a5fa; font-family: 'Space Grotesk', sans-serif; }
        input[type=range] {
            width: 100%;
            height: 6px;
            border-radius: 4px;
            background: var(--surface-3);
            outline: none;
            accent-color: var(--primary);
            cursor: pointer;
        }

        /* Add-ons checkbox tiles */
        .addon-tile {
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 0.9rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.6rem;
            cursor: pointer;
            transition: border 0.2s;
        }
        .addon-tile:last-child { margin-bottom: 0; }
        .addon-tile.checked { border-color: rgba(59, 130, 246, 0.5); background: rgba(30, 58, 138, 0.2); }
        .addon-left { display: flex; align-items: center; gap: 10px; }
        .addon-left input[type=checkbox] {
            width: 18px;
            height: 18px;
            accent-color: var(--primary);
            cursor: pointer;
        }
        .addon-name { font-weight: 600; font-size: 0.85rem; }
        .addon-price { font-size: 0.8rem; font-weight: 700; color: #60a5fa; font-family: 'Space Grotesk', sans-serif; }

        /* Step 3: Slots & Inputs */
        .scroller-row {
            display: flex;
            gap: 0.5rem;
            overflow-x: auto;
            padding-bottom: 4px;
            margin-bottom: 0.85rem;
            scrollbar-width: none;
        }
        .scroller-row::-webkit-scrollbar { display: none; }
        .date-chip, .time-chip {
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 8px 14px;
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-sub);
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.2s;
        }
        .date-chip.active, .time-chip.active {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            border-color: #60a5fa;
            color: white;
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .input-group { margin-bottom: 0.85rem; }
        .input-label { font-size: 0.8rem; font-weight: 600; color: var(--text-sub); margin-bottom: 5px; display: block; }
        .text-input {
            width: 100%;
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 12px 14px;
            color: white;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }
        .text-input:focus { border-color: var(--primary); }

        .location-btn {
            background: rgba(59, 130, 246, 0.12);
            border: 1px dashed rgba(59, 130, 246, 0.4);
            color: #93c5fd;
            border-radius: var(--radius-lg);
            padding: 10px;
            width: 100%;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        /* Payment Selector */
        .payment-segments {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.6rem;
            margin-top: 0.5rem;
        }
        .pay-card {
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 12px 6px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .pay-card.active {
            border-color: var(--emerald);
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            box-shadow: 0 4px 14px var(--emerald-glow);
        }
        .pay-card .p-name { font-weight: 700; font-size: 0.82rem; margin-top: 4px; }

        /* Floating Bottom Bar */
        .bottom-dock {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(11, 14, 23, 0.94);
            backdrop-filter: blur(24px);
            border-top: 1px solid var(--border);
            padding: 0.85rem 1.25rem calc(0.85rem + env(safe-area-inset-bottom, 0px)) 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 100;
        }
        .price-summary { display: flex; flex-direction: column; }
        .price-summary .tag { font-size: 0.72rem; color: var(--text-dim); font-weight: 600; text-transform: uppercase; }
        .price-summary .val {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 800;
            font-size: 1.4rem;
            color: white;
            letter-spacing: -0.03em;
        }
        .action-dock-btn {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            border: none;
            color: white;
            padding: 13px 26px;
            border-radius: 14px;
            font-weight: 700;
            font-size: 0.95rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 6px 20px var(--primary-glow);
            transition: transform 0.15s;
        }
        .action-dock-btn:active { transform: scale(0.96); }

        /* Success Screen */
        .success-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(5, 7, 12, 0.92);
            backdrop-filter: blur(20px);
            z-index: 200;
            padding: 1.5rem;
            align-items: center;
            justify-content: center;
        }
        .success-box {
            background: var(--surface-1);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 28px;
            padding: 2rem 1.5rem;
            width: 100%;
            max-width: 380px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
        }
        .check-circle {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: linear-gradient(135deg, #10b981, #059669);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.25rem auto;
            box-shadow: 0 0 24px var(--emerald-glow);
        }
        .check-circle svg { width: 32px; height: 32px; stroke: white; fill: none; stroke-width: 3; }
        .receipt-card {
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1rem;
            margin: 1.25rem 0;
            text-align: left;
            font-size: 0.82rem;
        }
        .receipt-row { display: flex; justify-content: space-between; margin-bottom: 6px; }
        .receipt-row:last-child { margin-bottom: 0; padding-top: 6px; border-top: 1px dashed var(--border); font-weight: 700; color: #60a5fa; }
    </style>
</head>
<body>

    <!-- 1. Top Navigation -->
    <div class="top-nav">
        <div class="brand-group">
            <div class="brand-icon">
                <svg viewBox="0 0 24 24"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/></svg>
            </div>
            <div>
                <div class="brand-title">Tozalash Servis</div>
                <div class="brand-status">24/7 AI Smart Dispatch</div>
            </div>
        </div>
        <div class="user-pill" id="userNamePill">Mijoz</div>
    </div>

    <!-- 2. Stepper Wizard -->
    <div class="stepper">
        <div class="step-progress-bar" id="progressBar" style="width: 0%;"></div>
        <div class="step-node active" id="node1" onclick="goToStep(1)">
            <div class="step-dot">1</div>
            <div class="step-label">Xizmat</div>
        </div>
        <div class="step-node" id="node2" onclick="goToStep(2)">
            <div class="step-dot">2</div>
            <div class="step-label">Hajm</div>
        </div>
        <div class="step-node" id="node3" onclick="goToStep(3)">
            <div class="step-dot">3</div>
            <div class="step-label">To'lov</div>
        </div>
    </div>

    <!-- STEP 1: XIZMAT TANLASH -->
    <div class="step-view active" id="step1">
        <div class="heading-xl">Xizmat Turini Tanlang</div>
        <div class="heading-sub">Barcha xizmatlarimiz professional Kärcher uskunalari bilan kafolatlangan</div>

        <div class="services-list">
            <div class="service-tile selected" onclick="selectServiceCard(this, 'regular_cleaning', 500000, 'xona')">
                <div class="service-media">
                    <svg viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
                </div>
                <div class="service-details">
                    <div class="service-header">
                        <span class="service-name">Oddiy / General Tozalash</span>
                        <span class="service-badge">Top Tanlov</span>
                    </div>
                    <div class="service-desc">Xonalar, oshxona va sanuzellarni chuqur changsizlantirish va dezinfeksiya</div>
                    <div class="service-meta">
                        <span class="service-rate">500 000 so'm / usta</span>
                        <div class="check-indicator"><svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg></div>
                    </div>
                </div>
            </div>

            <div class="service-tile" onclick="selectServiceCard(this, 'renovation_cleaning', 600000, 'xona')">
                <div class="service-media">
                    <svg viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
                </div>
                <div class="service-details">
                    <div class="service-header">
                        <span class="service-name">Ta'mirdan Keyingi Tozalash</span>
                        <span class="service-badge">Chuqur Tozalash</span>
                    </div>
                    <div class="service-desc">Qurilish changi, bo'yoq dog'lari va sement qoldiqlarini 100% yo'qotish</div>
                    <div class="service-meta">
                        <span class="service-rate">600 000 so'm / usta</span>
                        <div class="check-indicator"><svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg></div>
                    </div>
                </div>
            </div>

            <div class="service-tile" onclick="selectServiceCard(this, 'sofa_cleaning', 60000, 'o\'rin')">
                <div class="service-media">
                    <svg viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                </div>
                <div class="service-details">
                    <div class="service-header">
                        <span class="service-name">Divan & Mebel Ximchistkasi</span>
                        <span class="service-badge">Ekstraktor</span>
                    </div>
                    <div class="service-desc">Yumshoq mebel matosiga zarar yetkazmasdan dog' va hidlarni ketkazish</div>
                    <div class="service-meta">
                        <span class="service-rate">60 000 so'm / o'rin</span>
                        <div class="check-indicator"><svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg></div>
                    </div>
                </div>
            </div>

            <div class="service-tile" onclick="selectServiceCard(this, 'carpet_cleaning', 20000, 'kv.m')">
                <div class="service-media">
                    <svg viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"/></svg>
                </div>
                <div class="service-details">
                    <div class="service-header">
                        <span class="service-name">Gilam & Kovrolin Yuvish</span>
                    </div>
                    <div class="service-desc">Maxsus antibakterial shampunlar bilan gilamlarni yangidek yuvish</div>
                    <div class="service-meta">
                        <span class="service-rate">20 000 so'm / m²</span>
                        <div class="check-indicator"><svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- STEP 2: HAJM VA QO'SHIMCHA XIZMATLAR -->
    <div class="step-view" id="step2">
        <div class="heading-xl">Hajm va Moslashtirish</div>
        <div class="heading-sub">Xonalar soni va qo'shimcha xizmatlarni belgilang</div>

        <div class="glass-card">
            <div class="counter-row">
                <div>
                    <div class="counter-label" id="counterLabelTitle">Xonalar Soni</div>
                    <div class="counter-sub">Xonadon yoki obyekt bo'yicha</div>
                </div>
                <div class="counter-ctrl">
                    <button class="counter-btn" onclick="adjustCount(-1)">−</button>
                    <span class="counter-val" id="unitsNumber">2</span>
                    <button class="counter-btn" onclick="adjustCount(1)">+</button>
                </div>
            </div>

            <div class="slider-wrap">
                <div class="slider-meta">
                    <span>Taxminiy maydon:</span>
                    <strong id="areaDisplay">60 m²</strong>
                </div>
                <input type="range" id="areaSlider" min="30" max="300" step="5" value="60" oninput="onAreaChange(this.value)">
            </div>
        </div>

        <div class="heading-xl" style="font-size: 1rem; margin-top: 1.25rem;">Aksiyadagi Qo'shimcha Xizmatlar</div>
        <div class="heading-sub">Birgalikda buyurtma qilib 20% gacha tejang</div>

        <div class="addon-tile" onclick="toggleAddon('addonWindows')">
            <div class="addon-left">
                <input type="checkbox" id="addonWindows" onchange="recalculatePrice()">
                <div>
                    <div class="addon-name">Derazalarni 2 tomonlama yuvish</div>
                    <div style="font-size: 0.72rem; color: var(--text-dim);">Maxsus Kärcher bug' mashinasida</div>
                </div>
            </div>
            <div class="addon-price">+80 000</div>
        </div>

        <div class="addon-tile" onclick="toggleAddon('addonOzone')">
            <div class="addon-left">
                <input type="checkbox" id="addonOzone" onchange="recalculatePrice()">
                <div>
                    <div class="addon-name">Antibakterial Ozonatsiya</div>
                    <div style="font-size: 0.72rem; color: var(--text-dim);">Barcha bakteriya va hidlarni yo'qotish</div>
                </div>
            </div>
            <div class="addon-price">+100 000</div>
        </div>

        <div class="addon-tile" onclick="toggleAddon('addonOven')">
            <div class="addon-left">
                <input type="checkbox" id="addonOven" onchange="recalculatePrice()">
                <div>
                    <div class="addon-name">Duxovka & Plitani yog'dan tozalash</div>
                    <div style="font-size: 0.72rem; color: var(--text-dim);">Eski kuygan yog'larni eritish</div>
                </div>
            </div>
            <div class="addon-price">+60 000</div>
        </div>
    </div>

    <!-- STEP 3: VAQT, MANZIL VA TO'LOV -->
    <div class="step-view" id="step3">
        <div class="heading-xl">Vaqt, Manzil & To'lov</div>
        <div class="heading-sub">Oxirgi bosqich: usta kelish vaqtini va manzilni kiriting</div>

        <div class="glass-card" style="padding: 1rem;">
            <div style="font-size: 0.82rem; font-weight: 700; margin-bottom: 6px;">Qulay Kun:</div>
            <div class="scroller-row">
                <div class="date-chip active" onclick="pickDate(this, 'Bugun')">Bugun (17-avg)</div>
                <div class="date-chip" onclick="pickDate(this, 'Ertaga')">Ertaga (18-avg)</div>
                <div class="date-chip" onclick="pickDate(this, 'Indinga')">Indinga (19-avg)</div>
                <div class="date-chip" onclick="pickDate(this, '20-avgust')">20-avgust</div>
            </div>

            <div style="font-size: 0.82rem; font-weight: 700; margin-bottom: 6px;">Boshlanish Vaqti:</div>
            <div class="scroller-row">
                <div class="time-chip active" onclick="pickTime(this, '09:00')">09:00</div>
                <div class="time-chip" onclick="pickTime(this, '11:30')">11:30</div>
                <div class="time-chip" onclick="pickTime(this, '14:00')">14:00</div>
                <div class="time-chip" onclick="pickTime(this, '16:30')">16:30</div>
                <div class="time-chip" onclick="pickTime(this, '19:00')">19:00</div>
            </div>
        </div>

        <div class="glass-card" style="padding: 1rem;">
            <div class="input-group">
                <label class="input-label">Telefon Raqamingiz:</label>
                <input type="tel" id="inpPhone" class="text-input" placeholder="+998 (90) 123-45-67">
            </div>
            <div class="input-group" style="margin-bottom: 0;">
                <label class="input-label">Aniq Manzil (Tuman, ko'cha, uy, kv):</label>
                <input type="text" id="inpAddress" class="text-input" placeholder="Masalan: Chilonzor 9, 24-uy, 12-xonadon">
                <button class="location-btn" onclick="detectGPS()">
                    <svg style="width:16px;height:16px;stroke:currentColor;fill:none;" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                    Joriy lokatsiyamni aniqlash
                </button>
            </div>
        </div>

        <div class="glass-card" style="padding: 1rem;">
            <div class="input-group" style="margin-bottom: 8px;">
                <label class="input-label">Promo-kod (Aksiya):</label>
                <input type="text" id="inpPromo" class="text-input" placeholder="Masalan: VIP2026 (-15%)" oninput="recalculatePrice()">
            </div>

            <div style="font-size: 0.82rem; font-weight: 700; margin: 10px 0 6px 0;">To'lov Usuli:</div>
            <div class="payment-segments">
                <div class="pay-card active" onclick="pickPayment(this, 'click')">
                    <span style="font-size: 1.2rem;">🔹</span>
                    <div class="p-name">Click</div>
                </div>
                <div class="pay-card" onclick="pickPayment(this, 'payme')">
                    <span style="font-size: 1.2rem;">🟢</span>
                    <div class="p-name">Payme</div>
                </div>
                <div class="pay-card" onclick="pickPayment(this, 'cash')">
                    <span style="font-size: 1.2rem;">💵</span>
                    <div class="p-name">Joyida</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Sticky Bottom Dock -->
    <div class="bottom-dock">
        <div class="price-summary">
            <span class="tag">Jami Summa:</span>
            <span class="val" id="dockPrice">1 000 000 so'm</span>
        </div>
        <button class="action-dock-btn" id="dockBtn" onclick="handleDockAction()">
            <span>Davom etish</span>
            <svg style="width:18px;height:18px;stroke:currentColor;fill:none;" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
        </button>
    </div>

    <!-- Success Confirmation Overlay -->
    <div class="success-overlay" id="successScreen">
        <div class="success-box">
            <div class="check-circle">
                <svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>
            </div>
            <h2 style="font-size: 1.25rem; font-weight: 800; margin-bottom: 6px;">Buyurtma Qabul Qilindi!</h2>
            <p style="font-size: 0.8rem; color: var(--text-sub);">Smart Dispatcher buyurtmangizga eng yuqori reytingli ustani biriktirdi.</p>

            <div class="receipt-card">
                <div class="receipt-row"><span>Buyurtma ID:</span><strong id="rcptId">#1024</strong></div>
                <div class="receipt-row"><span>Biriktirilgan Usta:</span><strong id="rcptWorker">Rustam Aliyev (⭐️ 4.98)</strong></div>
                <div class="receipt-row"><span>Vaqt:</span><strong id="rcptTime">Bugun 09:00</strong></div>
                <div class="receipt-row"><span>Yakuniy To'lov:</span><strong id="rcptTotal">1 000 000 so'm</strong></div>
            </div>

            <div id="directPayContainer"></div>
            <button class="action-dock-btn" style="width:100%; justify-content:center; background: var(--surface-3);" onclick="finishAndClose()">Botga Qaytish</button>
        </div>
    </div>

    <script>
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
            if (tg.initDataUnsafe?.user) {
                const u = tg.initDataUnsafe.user;
                document.getElementById('userNamePill').innerText = u.first_name || 'Mijoz';
            }
        }

        let currentStep = 1;
        let selectedService = 'regular_cleaning';
        let unitPrice = 500000;
        let unitCount = 2;
        let selectedDate = 'Bugun';
        let selectedTime = '09:00';
        let selectedPayment = 'click';

        function selectServiceCard(el, type, price, unit) {
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
            document.querySelectorAll('.service-tile').forEach(t => t.classList.remove('selected'));
            el.classList.add('selected');
            selectedService = type;
            unitPrice = price;
            document.getElementById('counterLabelTitle').innerText = unit === 'xona' ? 'Xonalar Soni' : (unit === 'o\'rin' ? 'O\'rindiqlar Soni' : 'Maydon Hajmi');
            recalculatePrice();
        }

        function adjustCount(delta) {
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
            unitCount = Math.max(1, Math.min(10, unitCount + delta));
            document.getElementById('unitsNumber').innerText = unitCount;
            document.getElementById('areaSlider').value = unitCount * 30;
            document.getElementById('areaDisplay').innerText = (unitCount * 30) + ' m²';
            recalculatePrice();
        }

        function onAreaChange(val) {
            document.getElementById('areaDisplay').innerText = val + ' m²';
            unitCount = Math.max(1, Math.round(val / 30));
            document.getElementById('unitsNumber').innerText = unitCount;
            recalculatePrice();
        }

        function toggleAddon(id) {
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
            const chk = document.getElementById(id);
            if (event.target !== chk) chk.checked = !chk.checked;
            chk.closest('.addon-tile').classList.toggle('checked', chk.checked);
            recalculatePrice();
        }

        function pickDate(el, d) {
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
            document.querySelectorAll('.date-chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            selectedDate = d;
        }

        function pickTime(el, t) {
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
            document.querySelectorAll('.time-chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            selectedTime = t;
        }

        function pickPayment(el, method) {
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
            document.querySelectorAll('.pay-card').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            selectedPayment = method;
        }

        function detectGPS() {
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition((pos) => {
                    document.getElementById('inpAddress').value = "📍 Toshkent (" + pos.coords.latitude.toFixed(4) + ", " + pos.coords.longitude.toFixed(4) + ")";
                }, () => {
                    alert("Lokatsiyani aniqlab bo'lmadi. Iltimos, manzilni qo'lda yozing.");
                });
            }
        }

        function recalculatePrice() {
            let total = unitPrice * unitCount;
            if (document.getElementById('addonWindows')?.checked) total += 80000;
            if (document.getElementById('addonOzone')?.checked) total += 100000;
            if (document.getElementById('addonOven')?.checked) total += 60000;

            const promo = document.getElementById('inpPromo')?.value.trim().toUpperCase();
            if (promo === 'VIP2026') {
                total = total * 0.85; // 15% VIP discount
            }

            document.getElementById('dockPrice').innerText = Math.round(total).toLocaleString('uz-UZ') + " so'm";
        }

        function goToStep(s) {
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
            currentStep = s;
            document.querySelectorAll('.step-view').forEach(v => v.classList.remove('active'));
            document.getElementById('step' + s).classList.add('active');

            document.querySelectorAll('.step-node').forEach((n, idx) => {
                n.classList.remove('active', 'completed');
                if (idx + 1 === s) n.classList.add('active');
                else if (idx + 1 < s) n.classList.add('completed');
            });

            document.getElementById('progressBar').style.width = ((s - 1) / 2 * 100) + '%';
            
            const btn = document.getElementById('dockBtn');
            if (s === 3) {
                btn.innerHTML = `<span>Tasdiqlash & Buyurtma</span><svg style="width:18px;height:18px;stroke:currentColor;fill:none;" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>`;
                btn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
            } else {
                btn.innerHTML = `<span>Davom etish</span><svg style="width:18px;height:18px;stroke:currentColor;fill:none;" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>`;
                btn.style.background = 'linear-gradient(135deg, #2563eb, #1d4ed8)';
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function handleDockAction() {
            if (currentStep < 3) {
                goToStep(currentStep + 1);
            } else {
                executeBooking();
            }
        }

        async function executeBooking() {
            if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
            const phone = document.getElementById('inpPhone').value.trim() || "+998 (90) 123-45-67";
            const addr = document.getElementById('inpAddress').value.trim() || "Toshkent shahar";
            const promo = document.getElementById('inpPromo').value.trim();

            const payload = {
                telegram_id: tg?.initDataUnsafe?.user?.id || 88812345,
                client_name: tg?.initDataUnsafe?.user?.first_name || "Mijoz",
                client_phone: phone,
                service_type: selectedService,
                scheduled_time: selectedDate + " " + selectedTime,
                address: addr,
                area_sqm: unitCount * 30.0,
                promo_code: promo,
                notes: "To'lov usuli: " + selectedPayment
            };

            try {
                const resp = await fetch('/api/v1/tma/book', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();

                document.getElementById('rcptId').innerText = '#' + (data.order_id || 1024);
                document.getElementById('rcptWorker').innerText = (data.assigned_worker || "Rustam Aliyev") + " (⭐️ 4.98)";
                document.getElementById('rcptTime').innerText = selectedDate + " " + selectedTime;
                document.getElementById('rcptTotal').innerText = (data.final_price || 1000000).toLocaleString('uz-UZ') + " so'm";

                const payArea = document.getElementById('directPayContainer');
                if (selectedPayment === 'click' && data.payment_links?.click) {
                    payArea.innerHTML = `<a href="${data.payment_links.click}" target="_blank" class="action-dock-btn" style="width:100%; justify-content:center; text-decoration:none; margin-bottom:0.75rem; background:#0284c7;">Click Orqali To'lash 💳</a>`;
                } else if (selectedPayment === 'payme' && data.payment_links?.payme) {
                    payArea.innerHTML = `<a href="${data.payment_links.payme}" target="_blank" class="action-dock-btn" style="width:100%; justify-content:center; text-decoration:none; margin-bottom:0.75rem; background:#059669;">Payme Orqali To'lash 💳</a>`;
                } else {
                    payArea.innerHTML = '';
                }

                document.getElementById('successScreen').style.display = 'flex';
            } catch (err) {
                alert("Buyurtma yuborishda xatolik: " + err);
            }
        }

        function finishAndClose() {
            document.getElementById('successScreen').style.display = 'none';
            if (tg) tg.close();
        }

        recalculatePrice();
    </script>
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
