"""
Tozalash Servis — Redis Manager (Async Redis 7)
FSM State Store, Redlock Distributed Lock, Pub/Sub Event Broker & Query Cache
"""

import json
import asyncio
import os
from typing import Optional, Dict, Any, Callable
from loguru import logger

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis.asyncio o'rnatilmagan. In-memory fallback ishlatiladi.")


class MemoryFallback:
    """Redis mavjud bo'lmaganda lokal xotirada ishlash uchun xavfsiz fallback"""
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._subscribers: Dict[str, list] = {}

    async def get(self, key: str) -> Optional[str]:
        val = self._data.get(key)
        return json.dumps(val) if val is not None and not isinstance(val, str) else val

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        return True

    async def delete(self, key: str) -> bool:
        self._data.pop(key, None)
        return True

    async def exists(self, key: str) -> int:
        return 1 if key in self._data else 0

    async def publish(self, channel: str, message: str) -> int:
        callbacks = self._subscribers.get(channel, [])
        for cb in callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(message))
                else:
                    cb(message)
            except Exception as e:
                logger.error(f"Fallback pubsub xatosi: {e}")
        return len(callbacks)

    def subscribe_callback(self, channel: str, callback: Callable):
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)


class RedisManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client: Optional[Any] = None
        self.fallback = MemoryFallback()
        self.pubsub = None
        self._is_connected = False
        self._initialized = True

    async def init(self) -> bool:
        """Redis ulanishini ishga tushirish (Connection Pooling, TLS & Fallback bilan)"""
        if not REDIS_AVAILABLE:
            logger.info("ℹ️ Redis moduli yo'q — In-Memory fallback rejimida ishlamoqda.")
            return False

        try:
            pool_kwargs = {
                "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
                "decode_responses": True,
                "socket_timeout": float(os.getenv("REDIS_TIMEOUT", 0.3)),
                "socket_connect_timeout": float(os.getenv("REDIS_CONNECT_TIMEOUT", 0.3)),
                "health_check_interval": 30,
                "retry_on_timeout": True,
            }
            if self.redis_url.startswith("rediss://"):
                pool_kwargs["ssl_cert_reqs"] = None

            self.pool = aioredis.ConnectionPool.from_url(
                self.redis_url,
                **pool_kwargs
            )
            self.client = aioredis.Redis(connection_pool=self.pool)
            await asyncio.wait_for(self.client.ping(), timeout=0.5)
            self._is_connected = True
            logger.success(f"✅ Redis 7 muvaffaqiyatli ulandi ({'Upstash/TLS' if self.redis_url.startswith('rediss://') else 'Standard'}).")
            return True
        except Exception as e:
            logger.info(f"ℹ️ Redis ulanmadi ({e}). In-Memory fallback rejimiga o'tildi.")
            self._is_connected = False
            self.client = None
            return False

    async def close(self):
        """Ulanishni xavfsiz yopish"""
        if self.client and self._is_connected:
            try:
                await self.client.aclose()
                logger.info("Redis ulanishi yopildi.")
            except Exception as e:
                logger.error(f"Redis yopishda xato: {e}")

    # =========================================================================
    # FSM STATE & CONTEXT MANAGEMENT
    # =========================================================================
    async def get_fsm_state(self, user_id: str) -> Dict[str, Any]:
        """Foydalanuvchi holati va kontekstini Redis dan olish"""
        key = f"fsm:{user_id}"
        if self._is_connected and self.client:
            try:
                data = await self.client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get_fsm_state xatosi: {e}")

        raw = await self.fallback.get(key)
        if raw:
            try:
                return json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                return {"state": "idle", "context": {}}
        return {"state": "idle", "context": {}}

    async def set_fsm_state(
        self, user_id: str, state: str, context: Optional[Dict[str, Any]] = None, ttl: int = 86400
    ) -> bool:
        """Foydalanuvchi holati va kontekstini Redis ga saqlash (Standart TTL: 24 soat)"""
        key = f"fsm:{user_id}"
        payload = {
            "state": state,
            "context": context or {},
        }
        json_str = json.dumps(payload, ensure_ascii=False, default=str)

        if self._is_connected and self.client:
            try:
                await self.client.set(key, json_str, ex=ttl)
                return True
            except Exception as e:
                logger.error(f"Redis set_fsm_state xatosi: {e}")

        await self.fallback.set(key, payload)
        return True

    async def clear_fsm(self, user_id: str) -> bool:
        """Foydalanuvchi FSM holatini tozalash"""
        key = f"fsm:{user_id}"
        if self._is_connected and self.client:
            try:
                await self.client.delete(key)
                return True
            except Exception:
                pass
        await self.fallback.delete(key)
        return True

    # =========================================================================
    # REDLOCK — DISTRIBUTED LOCKING (Atomik blokirovka)
    # =========================================================================
    async def acquire_lock(self, resource_name: str, timeout_seconds: int = 10) -> bool:
        """Resurs ustida taqsimlangan atomik qulf olish"""
        lock_key = f"lock:{resource_name}"
        if self._is_connected and self.client:
            try:
                res = await self.client.set(lock_key, "locked", nx=True, ex=timeout_seconds)
                return bool(res)
            except Exception as e:
                logger.error(f"Redis acquire_lock xatosi: {e}")

        if lock_key in self.fallback._data:
            return False
        self.fallback._data[lock_key] = "locked"
        return True

    async def release_lock(self, resource_name: str):
        """Qulfni bo'shatish"""
        lock_key = f"lock:{resource_name}"
        if self._is_connected and self.client:
            try:
                await self.client.delete(lock_key)
            except Exception:
                pass
        self.fallback._data.pop(lock_key, None)

    # =========================================================================
    # PUB / SUB (Real-time xabarlar va WebSocket kanallari)
    # =========================================================================
    async def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Xabarni kanalga tarqatish"""
        payload = json.dumps(message, ensure_ascii=False, default=str)
        if self._is_connected and self.client:
            try:
                return await self.client.publish(channel, payload)
            except Exception as e:
                logger.error(f"Redis publish xatosi: {e}")

        return await self.fallback.publish(channel, payload)

    # =========================================================================
    # KESH (Query Cache & Audio Cache)
    # =========================================================================
    async def get_cache(self, key: str) -> Optional[Any]:
        """Keshdan ma'lumot olish"""
        if self._is_connected and self.client:
            try:
                val = await self.client.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass
        return self.fallback._data.get(key)

    async def set_cache(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Keshga ma'lumot yozish (TTL sekundlarda)"""
        json_val = json.dumps(value, ensure_ascii=False, default=str)
        if self._is_connected and self.client:
            try:
                await self.client.set(key, json_val, ex=ttl)
                return True
            except Exception:
                pass
        self.fallback._data[key] = value
        return True


# Global Singleton Instance
redis_manager = RedisManager()
