"""
Tozalash Servis — Enterprise Circuit Breaker Pattern
Tashqi xizmatlar (Gemini AI, G4F, Click, Payme, TTS) uzilganda yoki sekinlashganda
tizim qotib qolmasligi va tezkor fallback ishlashini ta'minlovchi asinxron avtomatik uzgich.
"""

import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional
from loguru import logger


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal holat: so'rovlar bemalol o'tadi
    OPEN = "OPEN"            # Uzilgan holat: xatolar ko'paygan, to'g'ridan-to'g'ri fallback
    HALF_OPEN = "HALF_OPEN"  # Qisman ochiq: tiklanishni tekshirish uchun bitta so'rov yuboriladi


class CircuitBreakerOpenException(Exception):
    """Circuit breaker ochiq bo'lganda otiladigan xatolik"""
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: tuple = (Exception,)
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.last_state_change: float = time.time()
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Asinxron funksiyani Circuit Breaker himoyasida chaqirish"""
        async with self._lock:
            current_time = time.time()

            # Agar OPEN holatida bo'lsa va timeout o'tgan bo'lsa -> HALF_OPEN ga o'tkazish
            if self.state == CircuitState.OPEN:
                if current_time - self.last_state_change > self.recovery_timeout:
                    logger.info(f"CircuitBreaker [{self.name}] HALF_OPEN holatiga o'tdi. Sinov so'rovi yuborilmoqda...")
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = current_time
                else:
                    raise CircuitBreakerOpenException(
                        f"CircuitBreaker [{self.name}] Ochiq (OPEN). Qolgan kutish vaqti: "
                        f"{round(self.recovery_timeout - (current_time - self.last_state_change), 1)} soniya"
                    )

        # Funksiyani bajarish
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Muvaffaqiyatli bo'lsa -> CLOSED holatiga qaytarish
            async with self._lock:
                if self.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
                    logger.info(f"CircuitBreaker [{self.name}] muvaffaqiyatli tiklandi -> CLOSED")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.last_state_change = time.time()
            return result

        except self.expected_exceptions as e:
            async with self._lock:
                self.failure_count += 1
                logger.warning(f"CircuitBreaker [{self.name}] xatolik qayd etildi ({self.failure_count}/{self.failure_threshold}): {e}")

                if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.last_state_change = time.time()
                    logger.error(f"CircuitBreaker [{self.name}] nosozliklar tufayli OPEN holatiga o'tdi! Timeout: {self.recovery_timeout}s")

            raise e


# Global Circuit Breakers
gemini_breaker = CircuitBreaker(name="GeminiAI", failure_threshold=3, recovery_timeout=20.0)
payment_breaker = CircuitBreaker(name="PaymentGateway", failure_threshold=4, recovery_timeout=30.0)
tts_breaker = CircuitBreaker(name="TTSService", failure_threshold=3, recovery_timeout=15.0)
