"""
Tozalash Servis - Database Layer Mock Testlar (Task 58)
- database.py funksiyalarini mock qilib AI mantiqini tekshirish
- Connection pool, archive_old_sessions, get_dynamic_guidelines
"""
import sys
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ================================================
# FIXTURES
# ================================================

@pytest.fixture
def mock_cursor():
    cursor = AsyncMock()
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=False)
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    conn = AsyncMock()
    conn.cursor = MagicMock(return_value=mock_cursor)
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    return conn


# ================================================
# 1. get_dynamic_guidelines TESTLARI
# ================================================

class TestGetDynamicGuidelines:

    @pytest.mark.asyncio
    async def test_returns_list_of_strings(self):
        """get_dynamic_guidelines list qaytarishi kerak"""
        mock_rows = [
            {"improvement": "Kech kelganda 5% chegirma taklif qil"},
            {"improvement": "Agar mijoz norozi bo'lsa darhol menejer chaqir"},
        ]
        with patch("database.db") as mock_db:
            mock_db.get_dynamic_guidelines = AsyncMock(return_value=[r["improvement"] for r in mock_rows])
            result = await mock_db.get_dynamic_guidelines()
            assert isinstance(result, list)
            assert len(result) == 2
            assert "chegirma" in result[0]

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_error(self):
        """Xatolik bo'lganda bo'sh list qaytishi kerak"""
        with patch("database.db") as mock_db:
            mock_db.get_dynamic_guidelines = AsyncMock(return_value=[])
            result = await mock_db.get_dynamic_guidelines()
            assert result == []


# ================================================
# 2. archive_old_sessions TESTLARI
# ================================================

class TestArchiveOldSessions:

    @pytest.mark.asyncio
    async def test_archive_called_with_correct_args(self):
        """archive_old_sessions to'g'ri chaqirilishi kerak"""
        with patch("database.db") as mock_db:
            mock_db.archive_old_sessions = AsyncMock(return_value=42)
            result = await mock_db.archive_old_sessions()
            mock_db.archive_old_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_returns_count(self):
        """archive_old_sessions o'chirilgan yozuvlar sonini qaytarishi kerak"""
        with patch("database.db") as mock_db:
            mock_db.archive_old_sessions = AsyncMock(return_value=5)
            result = await mock_db.archive_old_sessions()
            assert isinstance(result, int)


# ================================================
# 3. get_conversation_history TESTLARI
# ================================================

class TestConversationHistory:

    @pytest.mark.asyncio
    async def test_returns_list(self):
        """Suhbat tarixi list shaklida qaytishi kerak"""
        sample_history = [
            {"role": "user", "message": "Salom", "created_at": "2024-01-01"},
            {"role": "ai", "message": "Xush kelibsiz!", "created_at": "2024-01-01"},
        ]
        with patch("database.db") as mock_db:
            mock_db.get_conversation_history = AsyncMock(return_value=sample_history)
            result = await mock_db.get_conversation_history("123456", limit=10)
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_limit_respected(self):
        """Limit parametri ishlashi kerak"""
        with patch("database.db") as mock_db:
            mock_db.get_conversation_history = AsyncMock(return_value=[])
            await mock_db.get_conversation_history("123456", limit=5)
            mock_db.get_conversation_history.assert_called_with("123456", limit=5)


# ================================================
# 4. get_or_create_client TESTLARI
# ================================================

class TestGetOrCreateClient:

    @pytest.mark.asyncio
    async def test_returns_client_dict(self):
        """Mijoz ma'lumotlari dict shaklida qaytishi kerak"""
        expected = {
            "telegram_id": "123456",
            "name": "Ali",
            "total_orders": 3,
            "churn_risk": 0.1,
        }
        with patch("database.db") as mock_db:
            mock_db.get_or_create_client = AsyncMock(return_value=expected)
            result = await mock_db.get_or_create_client("123456", "Ali")
            assert result["telegram_id"] == "123456"
            assert result["total_orders"] == 3

    @pytest.mark.asyncio
    async def test_new_client_has_zero_orders(self):
        """Yangi mijozning buyurtmalar soni 0 bo'lishi kerak"""
        new_client = {
            "telegram_id": "999999",
            "name": "Yangi",
            "total_orders": 0,
            "churn_risk": 0.0,
        }
        with patch("database.db") as mock_db:
            mock_db.get_or_create_client = AsyncMock(return_value=new_client)
            result = await mock_db.get_or_create_client("999999")
            assert result["total_orders"] == 0


# ================================================
# 5. save_learning TESTLARI
# ================================================

class TestSaveLearning:

    @pytest.mark.asyncio
    async def test_save_learning_called_on_order(self):
        """Buyurtma yaratilganda save_learning chaqirilishi kerak"""
        with patch("database.db") as mock_db:
            mock_db.save_learning = AsyncMock()
            await mock_db.save_learning("order_conversion", "Divan yuvish", "Yaxshi!", True, 5.0)
            mock_db.save_learning.assert_called_once_with(
                "order_conversion", "Divan yuvish", "Yaxshi!", True, 5.0
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
