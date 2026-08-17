import time
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

# Include main API router
app.include_router(api_router, prefix="/api/v1")


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
