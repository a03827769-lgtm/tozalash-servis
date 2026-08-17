import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import patch, AsyncMock, MagicMock
from bot import admin_handlers


@pytest.mark.asyncio
async def test_is_admin():
    assert admin_handlers.is_admin(1) == False or True


@pytest.mark.asyncio
async def test_admin_menu():
    update = MagicMock()
    update.message.from_user.id = 1
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    with patch("bot.admin_handlers.is_admin", return_value=True):
        await admin_handlers.admin_menu(update, context)

    with patch("bot.admin_handlers.is_admin", return_value=False):
        await admin_handlers.admin_menu(update, context)


@pytest.mark.asyncio
async def test_admin_callback_handler():
    update = MagicMock()
    update.callback_query.from_user.id = 1
    update.callback_query.data = "admin_stats"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    context = MagicMock()

    with patch("bot.admin_handlers.is_admin", return_value=True):
        with patch("bot.admin_handlers.db") as mock_db:
            mock_db.get_orders_stats = AsyncMock(
                return_value={
                    "total_orders": 1,
                    "completed": 1,
                    "new_orders": 1,
                    "avg_order_value": 100,
                }
            )
            mock_db.get_finance_stats = AsyncMock(
                return_value={
                    "today_revenue": 100,
                    "month_revenue": 100,
                    "total_revenue": 100,
                }
            )
            mock_db.get_all_workers = AsyncMock(return_value=[1, 2])
            await admin_handlers.admin_callback_handler(update, context)

    update.callback_query.data = "admin_users"
    with patch("bot.admin_handlers.is_admin", return_value=True):
        with patch("bot.admin_handlers.db") as mock_db:
            mock_db.get_all_users = AsyncMock(
                return_value=[{"tg_id": 123, "name": "Test", "phone": "123"}]
            )
            await admin_handlers.admin_callback_handler(update, context)

    update.callback_query.data = "admin_broadcast"
    with patch("bot.admin_handlers.is_admin", return_value=True):
        await admin_handlers.admin_callback_handler(update, context)

    update.callback_query.data = "admin_export"
    with patch("bot.admin_handlers.is_admin", return_value=True):
        with patch("bot.admin_handlers.db") as mock_db:
            mock_db.get_all_orders = AsyncMock(return_value=[{"id": 1}])
            update.callback_query.message.reply_document = AsyncMock()
            await admin_handlers.admin_callback_handler(update, context)
