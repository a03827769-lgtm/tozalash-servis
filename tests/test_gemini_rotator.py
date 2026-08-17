"""
Unit testlar — gemini_rotator.py (K5 tuzatishlari uchun)

Tekshiriladi:
  - mark_failed() race condition himoyasi (asyncio.Lock)
  - bo'sh cooldowns dict'da _advance_unlocked() crash emas
  - HTTP status asosida to'g'ri cooldown muddatlari
  - get_current_cookies() to'g'ri qaytaradi
  - has_accounts property
  - get_status() to'liq holatni qaytaradi
"""

import asyncio
import time
import pytest
from unittest.mock import patch, MagicMock


# Test vaqtida os.getenv va fayl tizimini mock qilamiz
@pytest.fixture(autouse=True)
def no_env_accounts(monkeypatch):
    """Hech qanday .env akkaunt yo'q — toza holat"""
    for i in range(1, 6):
        monkeypatch.delenv(f"GEMINI_COOKIE_{i}_PSID", raising=False)
        monkeypatch.delenv(f"GEMINI_COOKIE_{i}_PSIDTS", raising=False)


@pytest.fixture()
def rotator_no_accounts():
    """Akkauntlarsiz rotator"""
    from gemini_rotator import GeminiAccountRotator

    r = GeminiAccountRotator()
    r.accounts = []
    r.cooldowns = {}
    r.current_index = 0
    return r


@pytest.fixture()
def rotator_with_accounts():
    """3 ta test akkaunt bilan rotator"""
    from gemini_rotator import GeminiAccountRotator

    r = GeminiAccountRotator()
    r.accounts = [
        {
            "index": 1,
            "source": "test1",
            "__Secure-1PSID": "psid1",
            "__Secure-1PSIDTS": "psidts1",
        },
        {
            "index": 2,
            "source": "test2",
            "__Secure-1PSID": "psid2",
            "__Secure-1PSIDTS": "",
        },
        {
            "index": 3,
            "source": "test3",
            "__Secure-1PSID": "psid3",
            "__Secure-1PSIDTS": "psidts3",
        },
    ]
    r.cooldowns = {}
    r.current_index = 0
    return r


class TestGeminiRotatorNoAccounts:
    """Akkaunt yo'q holatlar"""

    def test_has_accounts_false(self, rotator_no_accounts):
        assert rotator_no_accounts.has_accounts is False

    def test_get_current_cookies_none(self, rotator_no_accounts):
        assert rotator_no_accounts.get_current_cookies() is None

    @pytest.mark.asyncio
    async def test_mark_failed_no_crash_when_empty(self, rotator_no_accounts):
        """K5: Bo'sh accounts list'da mark_failed crash bo'lmasin"""
        await rotator_no_accounts.mark_failed(reason="429")  # Exception ko'tarilmasin

    def test_advance_unlocked_no_crash_empty_cooldowns(self, rotator_no_accounts):
        """K5: Bo'sh cooldowns va bo'sh accounts'da _advance_unlocked crash bo'lmasin"""
        rotator_no_accounts._advance_unlocked()  # Exception ko'tarilmasin

    def test_get_status_empty(self, rotator_no_accounts):
        assert rotator_no_accounts.get_status() == []


class TestGeminiRotatorWithAccounts:
    """3 ta akkaunt bilan holatlar"""

    def test_has_accounts_true(self, rotator_with_accounts):
        assert rotator_with_accounts.has_accounts is True

    def test_get_current_cookies_first_account(self, rotator_with_accounts):
        cookies = rotator_with_accounts.get_current_cookies()
        assert cookies is not None
        assert cookies["__Secure-1PSID"] == "psid1"
        assert cookies["__Secure-1PSIDTS"] == "psidts1"

    def test_get_current_cookies_no_psidts_if_empty(self, rotator_with_accounts):
        """PSIDTS bo'sh bo'lsa — cookie'ga qo'shilmasin"""
        rotator_with_accounts.current_index = 1
        cookies = rotator_with_accounts.get_current_cookies()
        # psid2 bor, lekin psidts2 = "" → qo'shilmasin
        assert "__Secure-1PSID" in cookies
        assert cookies.get("__Secure-1PSIDTS") != ""  # bo'sh string bo'lmasin

    @pytest.mark.asyncio
    async def test_mark_failed_advances_index(self, rotator_with_accounts):
        """mark_failed() joriy indeksni 0 dan 1 ga o'tkazsin"""
        assert rotator_with_accounts.current_index == 0
        await rotator_with_accounts.mark_failed(reason="429")
        assert rotator_with_accounts.current_index != 0  # O'tdi

    @pytest.mark.asyncio
    async def test_mark_failed_sets_cooldown(self, rotator_with_accounts):
        """mark_failed() cooldown vaqtini to'g'ri o'rnatadi"""
        before = time.time()
        await rotator_with_accounts.mark_failed(reason="429")
        after = time.time()
        # Joriy 0 indeks cooldownga tushdi
        assert 0 in rotator_with_accounts.cooldowns
        # 429 → 3600s cooldown
        assert rotator_with_accounts.cooldowns[0] >= before + 3590

    @pytest.mark.asyncio
    async def test_mark_failed_race_condition_safe(self, rotator_with_accounts):
        """K5: Parallel mark_failed() chaqiruvlari xavfsiz ishlaydi"""
        tasks = [
            rotator_with_accounts.mark_failed(reason="429"),
            rotator_with_accounts.mark_failed(reason="500"),
            rotator_with_accounts.mark_failed(reason="401"),
        ]
        await asyncio.gather(*tasks)  # Exception bo'lmasin


class TestCooldownDurations:
    """HTTP status asosida cooldown muddatlari"""

    @pytest.fixture()
    def rotator(self):
        from gemini_rotator import (
            GeminiAccountRotator,
            COOLDOWN_RATE_LIMIT,
            COOLDOWN_AUTH_ERROR,
            COOLDOWN_SERVER_ERROR,
            COOLDOWN_DEFAULT,
        )

        r = GeminiAccountRotator()
        r.accounts = [
            {"index": 1, "source": "t", "__Secure-1PSID": "x", "__Secure-1PSIDTS": ""}
        ]
        r.cooldowns = {}
        r.current_index = 0
        return (
            r,
            COOLDOWN_RATE_LIMIT,
            COOLDOWN_AUTH_ERROR,
            COOLDOWN_SERVER_ERROR,
            COOLDOWN_DEFAULT,
        )

    def test_cooldown_rate_limit(self, rotator):
        r, rl, ae, se, de = rotator
        assert r._get_cooldown_duration("429 Too Many Requests") == rl

    def test_cooldown_auth_error(self, rotator):
        r, rl, ae, se, de = rotator
        assert r._get_cooldown_duration("401 Unauthorized") == ae
        assert r._get_cooldown_duration("403 Forbidden") == ae

    def test_cooldown_server_error(self, rotator):
        r, rl, ae, se, de = rotator
        assert r._get_cooldown_duration("500 Internal Server Error") == se
        assert r._get_cooldown_duration("502 Bad Gateway") == se

    def test_cooldown_default(self, rotator):
        r, rl, ae, se, de = rotator
        assert r._get_cooldown_duration("Unknown error") == de

    def test_cooldown_quota_keyword(self, rotator):
        r, rl, ae, se, de = rotator
        assert r._get_cooldown_duration("quota exceeded") == rl

    def test_cooldown_rate_keyword(self, rotator):
        r, rl, ae, se, de = rotator
        assert r._get_cooldown_duration("rate limit hit") == rl


class TestAdvanceUnlocked:
    """_advance_unlocked() holatlari"""

    @pytest.fixture()
    def r3(self):
        from gemini_rotator import GeminiAccountRotator

        r = GeminiAccountRotator()
        r.accounts = [
            {
                "index": i,
                "source": f"t{i}",
                "__Secure-1PSID": f"p{i}",
                "__Secure-1PSIDTS": "",
            }
            for i in range(3)
        ]
        r.cooldowns = {}
        r.current_index = 0
        return r

    def test_advance_to_next_available(self, r3):
        r3._advance_unlocked()
        assert r3.current_index == 1

    def test_advance_skips_cooldown_accounts(self, r3):
        """Cooldowndagi hisoblar o'tkazib yuboriladi"""
        r3.cooldowns[1] = time.time() + 9999  # 1-indeks cooldownda
        r3._advance_unlocked()
        # 0 → 1 (cooldown) → 2 ga o'tishi kerak
        assert r3.current_index == 2

    def test_advance_all_in_cooldown_picks_earliest(self, r3):
        """K5 FIX: Hammasi cooldownda — eng tez tugaydigan tanlanadi"""
        now = time.time()
        r3.cooldowns[0] = now + 9999
        r3.cooldowns[1] = now + 100  # Eng tez tugaydi
        r3.cooldowns[2] = now + 5000
        r3._advance_unlocked()
        assert r3.current_index == 1  # Eng tez tugaydigan

    def test_advance_wraps_around(self, r3):
        """Oxirgi akkauntdan keyin birinchisiga qaytadi"""
        r3.current_index = 2
        r3._advance_unlocked()
        assert r3.current_index == 0
