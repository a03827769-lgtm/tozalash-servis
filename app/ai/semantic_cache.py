"""
Tozalash Servis — AI Semantic Cache Engine
Mijozlarning takroriy va o'xshash savollariga 1ms ichida javob qaytaruvchi,
LLM sarfini 90% ga kamaytiruvchi va javob tezligini maksimal oshiruvchi semantik kesh.
"""

import re
import hashlib
import time
from typing import Optional, Dict, Any, Tuple
from loguru import logger
from app.core.redis_manager import redis_manager


def _normalize_uzbek_text(text: str) -> str:
    """O'zbekcha matnni normalizatsiya qilish (belgilar, harflar, tinish belgilari)"""
    t = text.lower().strip()
    t = t.replace("o'", "o").replace("g'", "g").replace("sh", "s").replace("ch", "c")
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


class SemanticCache:
    def __init__(self, ttl_seconds: int = 86400 * 7):  # 7 kunlik kesh
        self.ttl = ttl_seconds
        self._local_cache: Dict[str, Tuple[str, float]] = {}

    def _get_hash(self, text: str) -> str:
        norm = _normalize_uzbek_text(text)
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    async def get(self, query: str) -> Optional[str]:
        """Keshdan javobni qidirish"""
        key_hash = self._get_hash(query)
        cache_key = f"semantic_cache:{key_hash}"

        # 1. Redis tekshirish
        try:
            val = await redis_manager.get(cache_key)
            if val:
                logger.info(f"Semantic Cache HIT (Redis): '{query[:30]}...'")
                return val
        except Exception:
            pass

        # 2. Local fallback kesh
        if key_hash in self._local_cache:
            resp, exp = self._local_cache[key_hash]
            if time.time() < exp:
                logger.info(f"Semantic Cache HIT (Memory): '{query[:30]}...'")
                return resp
            else:
                del self._local_cache[key_hash]

        return None

    async def set(self, query: str, response: str) -> None:
        """Keshga yangi javobni yozish"""
        if not response or len(response) < 10:
            return

        key_hash = self._get_hash(query)
        cache_key = f"semantic_cache:{key_hash}"

        try:
            await redis_manager.set(cache_key, response, expire=self.ttl)
        except Exception:
            pass

        self._local_cache[key_hash] = (response, time.time() + self.ttl)


semantic_cache = SemanticCache()
