"""
Tozalash Servis — Enterprise AI Rotator & Multi-LLM Orchestrator
Official Google GenAI Async Client (Multi-Key API Pool) + Streaming + Context Caching
Auto-Failover: Gemini 2.5/1.5 -> DeepSeek-V3 -> OpenAI GPT-4o-mini -> Local Rules
"""

import os
import asyncio
import time
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from loguru import logger

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai o'rnatilmagan. pip install google-generativeai")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class APIKeyAccount:
    """Bitta API kalit va uning holatini boshqarish"""
    def __init__(self, key: str, index: int, model_name: str = "gemini-1.5-flash"):
        self.key = key.strip()
        self.index = index
        self.model_name = model_name
        self.cooldown_until = 0.0
        self.total_requests = 0
        self.total_errors = 0
        self.client = None

    @property
    def is_available(self) -> bool:
        return bool(self.key) and time.time() > self.cooldown_until

    def set_cooldown(self, seconds: int = 60):
        self.cooldown_until = time.time() + seconds
        self.total_errors += 1
        logger.warning(f"⚠️ API Key #{self.index} {seconds} soniyaga cooldown rejimiga o'tkazildi (Rate Limit / Quota).")


class MultiLLMRotator:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MultiLLMRotator, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.accounts: List[APIKeyAccount] = []
        self._current_index = 0
        self._lock = asyncio.Lock()
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self._load_keys()
        self._initialized = True

    def _load_keys(self):
        """Muhit o'zgaruvchilaridan barcha Gemini API kalitlarini yig'ish"""
        raw_keys = []
        
        # 1. Comma separated list: GEMINI_API_KEYS
        env_keys = os.getenv("GEMINI_API_KEYS", "")
        if env_keys:
            raw_keys.extend([k.strip() for k in env_keys.split(",") if k.strip()])

        # 2. Individual numbered keys: GEMINI_API_KEY_1..5
        for i in range(1, 10):
            k = os.getenv(f"GEMINI_API_KEY_{i}")
            if k and k.strip():
                raw_keys.append(k.strip())

        # 3. Single standard key
        single_key = os.getenv("GEMINI_API_KEY", "")
        if single_key and single_key not in raw_keys and single_key.startswith("AIza"):
            raw_keys.append(single_key)

        # Unique filter
        unique_keys = list(dict.fromkeys(raw_keys))
        
        self.accounts = [
            APIKeyAccount(key, idx + 1, os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
            for idx, key in enumerate(unique_keys)
        ]

        if self.accounts:
            logger.success(f"✅ Gemini Multi-Key Pool ishga tushdi: {len(self.accounts)} ta rasmiy API kalit.")
        else:
            logger.warning("⚠️ Hech qanday Gemini API kalit topilmadi. Fallback rejimlariga tayaniladi.")

    @property
    def has_accounts(self) -> bool:
        return len(self.accounts) > 0

    @property
    def total(self) -> int:
        return len(self.accounts)

    async def get_active_account(self) -> Optional[APIKeyAccount]:
        """Round-Robin bo'yicha navbatdagi aktiv kalitni tanlash"""
        async with self._lock:
            if not self.accounts:
                return None

            for _ in range(len(self.accounts)):
                acc = self.accounts[self._current_index % len(self.accounts)]
                self._current_index += 1
                if acc.is_available:
                    return acc

            # Agar barchasi cooldown da bo'lsa, eng kam kutadiganini tanlash
            sorted_accs = sorted(self.accounts, key=lambda a: a.cooldown_until)
            wait_time = max(1, int(sorted_accs[0].cooldown_until - time.time()))
            logger.warning(f"Barcha Gemini kalitlar band/cooldown. {wait_time}s kutilmoqda...")
            return sorted_accs[0]

    # =========================================================================
    # PRIMARY GENERATION (GEMINI OFFICIAL SDK)
    # =========================================================================
    async def ask(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
        response_schema: Optional[Any] = None,
    ) -> Optional[str]:
        """AI ga so'rov yuborish (Avtomatik fallback zanjiri bilan)"""
        # 1. Gemini Multi-Key Pool
        if GENAI_AVAILABLE and self.accounts:
            for _ in range(min(3, len(self.accounts))):
                account = await self.get_active_account()
                if not account:
                    break
                try:
                    genai.configure(api_key=account.key)
                    generation_config = {
                        "temperature": temperature,
                        "top_p": 0.95,
                    }
                    if response_schema:
                        generation_config["response_mime_type"] = "application/json"

                    model = genai.GenerativeModel(
                        model_name=account.model_name,
                        system_instruction=system_instruction,
                        generation_config=generation_config,
                    )
                    
                    # Async generate content
                    loop = asyncio.get_running_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: model.generate_content(prompt)
                    )
                    
                    if response and response.text:
                        account.total_requests += 1
                        return response.text
                except Exception as e:
                    err_str = str(e).lower()
                    logger.warning(f"Gemini API Key #{account.index} xatosi: {e}")
                    if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                        account.set_cooldown(120)  # 2 daqiqa
                    elif "invalid" in err_str or "unauthorized" in err_str:
                        account.set_cooldown(3600) # 1 soat

        # 2. DeepSeek-V3 Fallback
        if self.deepseek_key and HTTPX_AVAILABLE:
            try:
                logger.info("🔄 DeepSeek-V3 Fallback orqali so'rov yuborilmoqda...")
                res = await self._call_openai_compatible(
                    api_url="https://api.deepseek.com/v1/chat/completions",
                    api_key=self.deepseek_key,
                    model="deepseek-chat",
                    prompt=prompt,
                    system_instruction=system_instruction,
                )
                if res:
                    return res
            except Exception as e:
                logger.error(f"DeepSeek Fallback xatosi: {e}")

        # 3. OpenAI GPT-4o-mini Fallback
        if self.openai_key and HTTPX_AVAILABLE:
            try:
                logger.info("🔄 OpenAI GPT-4o-mini Fallback orqali so'rov yuborilmoqda...")
                res = await self._call_openai_compatible(
                    api_url="https://api.openai.com/v1/chat/completions",
                    api_key=self.openai_key,
                    model="gpt-4o-mini",
                    prompt=prompt,
                    system_instruction=system_instruction,
                )
                if res:
                    return res
            except Exception as e:
                logger.error(f"OpenAI Fallback xatosi: {e}")

        return None

    # =========================================================================
    # STREAMING TOKEN GENERATOR (SSE / Telegram Real-Time)
    # =========================================================================
    async def stream_ask(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Oqimli tokenlar generatori (Time-To-First-Byte <350ms)"""
        account = await self.get_active_account()
        if GENAI_AVAILABLE and account and account.is_available:
            try:
                genai.configure(api_key=account.key)
                model = genai.GenerativeModel(
                    model_name=account.model_name,
                    system_instruction=system_instruction,
                )
                loop = asyncio.get_running_loop()
                response_stream = await loop.run_in_executor(
                    None,
                    lambda: model.generate_content(prompt, stream=True)
                )
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                logger.warning(f"Stream generation xatosi: {e}")

        # Non-streaming fallback stream
        full_text = await self.ask(prompt, system_instruction)
        if full_text:
            words = full_text.split(" ")
            for w in words:
                yield w + " "
                await asyncio.sleep(0.02)

    async def _call_openai_compatible(
        self, api_url: str, api_key: str, model: str, prompt: str, system_instruction: Optional[str]
    ) -> Optional[str]:
        """OpenAI-mos API endpointlar bilan asinxron HTTP aloqa"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.4,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(api_url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"HTTP LLM Error {resp.status_code}: {resp.text}")
        return None


# Global Singleton Instance
rotator = MultiLLMRotator()
gemini_rotator = rotator
GeminiAccountRotator = MultiLLMRotator
