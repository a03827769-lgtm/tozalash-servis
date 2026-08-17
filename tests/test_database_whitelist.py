"""
Unit testlar — database.py update_client() (M3 SQL injection whitelist)

Tekshiriladi:
  - Whitelist'dan tashqari ustunlar rad etiladi
  - Whitelist'dagi ustunlar qabul qilinadi
  - Bo'sh kwargs — hech narsa qilmaydi
  - SQL injection urinishlari bloklangan
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock


def make_db_with_mock_pool():
    """Database instansiyasini mock pool bilan yaratish."""
    from database import Database

    db = Database.__new__(Database)
    db._lock = asyncio.Lock()

    # cursor mock
    mock_cursor = AsyncMock()

    # Async context manager uchun to'g'ri setup
    cursor_cm = MagicMock()
    cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
    cursor_cm.__aexit__ = AsyncMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cursor_cm
    mock_conn.begin = AsyncMock()
    mock_conn.commit = AsyncMock()
    mock_conn.rollback = AsyncMock()

    # Pool acquire async context manager
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.acquire.return_value = acquire_cm
    db.pool = mock_pool

    return db, mock_cursor


class TestUpdateClientWhitelist:
    """M3: SQL injection whitelist testlari"""

    @pytest.mark.asyncio
    async def test_valid_column_accepted(self):
        """Whitelist'dagi ustun qabul qilinadi"""
        db, mock_cursor = make_db_with_mock_pool()
        await db.update_client("123456", name="Ali", language="uz")

        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        assert "`name`" in sql or "`language`" in sql
        assert "WHERE telegram_id = %s" in sql

    @pytest.mark.asyncio
    async def test_invalid_column_rejected(self):
        """Whitelist'dan tashqari ustun rad etiladi"""
        db, mock_cursor = make_db_with_mock_pool()

        # SQL injection urinishi
        await db.update_client("123456", **{"DROP TABLE clients--": "evil"})

        # execute chaqirilmagan bo'lishi kerak
        mock_cursor.execute.assert_not_called()

    def test_whitelist_contains_expected_columns(self):
        """Whitelist kutilgan ustunlarni o'z ichiga oladi"""
        from database import Database

        wl = Database._CLIENT_UPDATABLE_COLUMNS
        for col in ["name", "language", "churn_risk", "gender", "loyalty_points"]:
            assert col in wl, f"{col} whitelist'da bo'lishi kerak"

    def test_whitelist_excludes_dangerous_columns(self):
        """Xavfli ustunlar whitelist'da yo'q"""
        from database import Database

        wl = Database._CLIENT_UPDATABLE_COLUMNS
        for col in ["id", "telegram_id", "created_at", "DROP TABLE", "1=1"]:
            assert col not in wl, f"{col} whitelist'dan chiqarilgan bo'lishi kerak"

    def test_whitelist_is_frozenset(self):
        """Whitelist o'zgartirilmaydigan frozenset"""
        from database import Database

        assert isinstance(Database._CLIENT_UPDATABLE_COLUMNS, frozenset)


class TestUpdateClientEdgeCases:
    """Chegaraviy holatlar"""

    @pytest.mark.asyncio
    async def test_empty_kwargs_returns_early(self):
        """Bo'sh kwargs — execute chaqirilmaydi"""
        db, mock_cursor = make_db_with_mock_pool()
        await db.update_client("123456")
        mock_cursor.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_mixed_valid_invalid_columns(self):
        """Valid va invalid aralash — faqat valid qabul qilinadi"""
        db, mock_cursor = make_db_with_mock_pool()

        await db.update_client(
            "123456", name="Ali", evil_col="hack", language="uz"  # valid ✓  # invalid ✗
        )  # valid ✓

        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        assert "evil_col" not in sql
        assert "`name`" in sql or "`language`" in sql

    @pytest.mark.asyncio
    async def test_column_names_backtick_quoted(self):
        """Ustun nomlari backtick bilan himoyalangan"""
        db, mock_cursor = make_db_with_mock_pool()
        await db.update_client("123456", name="Test")

        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        assert "`name`" in sql

    @pytest.mark.asyncio
    async def test_values_are_parameterized(self):
        """Qiymatlar SQL'ga to'g'ridan-to'g'ri kirmaydi, parametrlanadi"""
        db, mock_cursor = make_db_with_mock_pool()
        await db.update_client("123456", name="Haxxor'; DROP TABLE clients;--")

        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        # SQL'da qiymat yo'q, faqat %s
        assert "Haxxor" not in sql
        assert "Haxxor'; DROP TABLE clients;--" in params
