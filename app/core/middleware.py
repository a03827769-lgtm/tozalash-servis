"""
Tozalash Servis — Enterprise HTTP Middlewares
1. IdempotencyMiddleware: Takroriy POST/PUT to'lov va buyurtmalarni filtrlash
2. RateLimitingMiddleware: IP bo'yicha so'rovlar sonini me'yorda ushlash (Leaky/Token Bucket)
3. SecurityHeadersMiddleware: OWASP xavfsizlik sarlavhalari (HSTS, CSP, X-Frame-Options)
4. ServerTimingMiddleware: Millisekundlik diagnostika (Server-Timing)
"""

import time
import json
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from loguru import logger
from app.core.redis_manager import redis_manager


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP xavfsizlik sarlavhalari (Telegram Mini App iframe moslashuvchanligi bilan)"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Telegram WebApp iframe ichida ochilishi uchun frame-ancestors ni ochamiz
        path = request.url.path
        if path.startswith("/tma") or path.startswith("/app") or path.startswith("/static"):
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://web.telegram.org https://*.telegram.org https://telegram.org;"
            # X-Frame-Options ni o'chirib tashlaymiz yoki ALLOWALL qilamiz
            if "x-frame-options" in response.headers:
                del response.headers["x-frame-options"]
        else:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            
        return response



class ServerTimingMiddleware(BaseHTTPMiddleware):
    """Serverda so'rovni bajarish vaqtini 'Server-Timing' sarlavhasida qaytarish"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["Server-Timing"] = f"total;dur={process_time_ms}"
        response.headers["X-Process-Time-Ms"] = str(process_time_ms)
        return response


# Lokal in-memory rate limiter zaxirasi
_in_memory_rate_limit: Dict[str, Tuple[int, float]] = {}


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """IP bo'yicha daqiqasiga ruxsat etilgan so'rovlar sonini nazorat qilish (Default: 120 req/min)"""
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Statik va metrics endpointlarni cheklamaymiz
        path = request.url.path
        if path.startswith("/static") or path in ("/metrics", "/health", "/favicon.ico", "/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Redis orqali tekshirish
        rate_key = f"rate_limit:{client_ip}"
        try:
            val = await redis_manager.get(rate_key)
            if val is not None:
                count = int(val)
                if count >= self.max_requests:
                    logger.warning(f"Rate limit oshib ketdi: IP {client_ip} ({count} req/{self.window_seconds}s)")
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Too Many Requests",
                            "message": "So'rovlar limiti oshib ketdi. Iltimos, birozdan so'ng qayta urinib ko'ring.",
                            "retry_after_seconds": self.window_seconds
                        },
                        headers={"Retry-After": str(self.window_seconds)}
                    )
                await redis_manager.set(rate_key, str(count + 1), expire=self.window_seconds)
            else:
                await redis_manager.set(rate_key, "1", expire=self.window_seconds)
        except Exception:
            # Fallback to in-memory rate limiter
            if client_ip in _in_memory_rate_limit:
                count, first_req_time = _in_memory_rate_limit[client_ip]
                if current_time - first_req_time < self.window_seconds:
                    if count >= self.max_requests:
                        return JSONResponse(
                            status_code=429,
                            content={"error": "Too Many Requests", "retry_after_seconds": self.window_seconds}
                        )
                    _in_memory_rate_limit[client_ip] = (count + 1, first_req_time)
                else:
                    _in_memory_rate_limit[client_ip] = (1, current_time)
            else:
                _in_memory_rate_limit[client_ip] = (1, current_time)

        return await call_next(request)


# In-memory idempotency cache fallback
_idempotency_cache: Dict[str, Tuple[int, bytes, Dict[str, str], float]] = {}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    POST/PUT/PATCH so'rovlarida 'X-Idempotency-Key' sarlavhasi berilsa,
    takroriy tranzaksiyalarning oldini oladi va avvalgi javobni qaytaradi.
    """
    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        cache_key = f"idempotency:{idempotency_key}"
        
        # Redisdan tekshirish
        try:
            cached_data = await redis_manager.get(cache_key)
            if cached_data:
                cached = json.loads(cached_data)
                logger.info(f"Idempotency hit: {idempotency_key} — Keshdagi javob qaytarilmoqda.")
                return Response(
                    content=cached["body"].encode("utf-8"),
                    status_code=cached["status_code"],
                    headers={**cached.get("headers", {}), "X-Cache-Lookup": "HIT-IDEMPOTENT"}
                )
        except Exception:
            pass

        # Yangi so'rovni bajarish
        response = await call_next(request)

        # 2xx yoki 4xx bo'lsa keshga yozish (24 soatlik TTL)
        if 200 <= response.status_code < 500:
            try:
                # Body ni o'qish
                resp_body = [section async for section in response.body_iterator]
                response.body_iterator = _iterate_in_chunks(resp_body)
                full_body = b"".join(resp_body).decode("utf-8", errors="ignore")

                cache_payload = json.dumps({
                    "status_code": response.status_code,
                    "body": full_body,
                    "headers": {"Content-Type": response.headers.get("Content-Type", "application/json")}
                })
                await redis_manager.set(cache_key, cache_payload, expire=86400)
            except Exception as e:
                logger.warning(f"Idempotency keshga yozishda xato: {e}")

        return response


async def _iterate_in_chunks(chunks):
    for chunk in chunks:
        yield chunk
