import asyncio
from loguru import logger
import redis.asyncio as redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from app.core.config import settings

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)
redis_client = None


async def init_redis(app: FastAPI):
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf8",
            decode_responses=True,
            socket_timeout=float(os.getenv("REDIS_TIMEOUT", 0.3)),
            socket_connect_timeout=float(os.getenv("REDIS_CONNECT_TIMEOUT", 0.3)),
        )
        await asyncio.wait_for(redis_client.ping(), timeout=0.5)
        FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
        logger.success("✅ FastAPICache RedisBackend muvaffaqiyatli ishga tushdi.")
    except Exception as e:
        logger.info(f"ℹ️ Redis ulanmadi ({e}). FastAPICache InMemoryBackend fallback ishga tushirildi.")
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

    # Attach slowapi rate limiter to app
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
