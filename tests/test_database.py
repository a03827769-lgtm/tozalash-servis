import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import patch, AsyncMock, MagicMock
from database import Database


class AsyncContextManagerMock:
    def __init__(self, return_obj):
        self.return_obj = return_obj

    async def __aenter__(self):
        return self.return_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_database_methods():
    db = Database()

    with patch("database.aiomysql.create_pool") as mock_pool:
        # mock pool
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()

        mock_conn.cursor = MagicMock(return_value=AsyncContextManagerMock(mock_cursor))

        mock_pool_obj = MagicMock()
        mock_pool_obj.acquire.return_value = AsyncContextManagerMock(mock_conn)
        mock_pool.return_value = mock_pool_obj

        db.pool = mock_pool.return_value

        # init_db
        with patch("migrations_runner.run_migrations", new=AsyncMock()):
            await db.init_db()

        # get_or_create_client
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "total_orders": 1,
            "referred_by": None,
        }
        await db.get_or_create_client(123, "test", "test")

        # update_client
        await db.update_client(1, phone="phone", address="address", location="loc")

        # create_order
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.return_value = {
            "total_orders": 1,
            "referred_by": "referrer_123",
        }
        await db.create_order(
            {"client_telegram_id": "123", "service_type": "test", "total_price": 100}
        )

        # get_client_orders
        mock_cursor.fetchall.return_value = [{"id": 1}]
        await db.get_client_orders(1)

        # get_order
        mock_cursor.fetchone.return_value = {"id": 1}
        await db.get_order(1)

        # get_all_workers
        mock_cursor.fetchall.return_value = [{"id": 1}]
        await db.get_all_workers()

        # get_worker_by_tg_id
        mock_cursor.fetchone.return_value = {"id": 1}
        await db.get_worker_by_tg_id("123")

        # get_orders_stats
        mock_cursor.fetchone.return_value = {"total_orders": 1}
        await db.get_orders_stats()

        # get_finance_stats
        mock_cursor.fetchone.return_value = {"today_revenue": 1}
        await db.get_finance_stats()

        # get_today_orders
        mock_cursor.fetchall.return_value = [{"id": 1}]
        await db.get_today_orders()

        # get_available_workers
        mock_cursor.fetchall.return_value = [{"id": 1}]
        await db.get_available_workers()

        # update_order_status
        await db.update_order_status(1, "done")

        # save_message
        await db.save_message(123, "user", "msg")

        # get_conversation_history
        mock_cursor.fetchall.return_value = [{"role": "user", "content": "msg"}]
        await db.get_conversation_history(123)

        # save_learning
        await db.save_learning("pattern", "response", "output", True, 0.9)

        # get_successful_patterns
        mock_cursor.fetchall.return_value = [{"pattern": "pat", "response": "res"}]
        await db.get_successful_patterns()

        # register_worker
        await db.register_worker("123", "name", "phone")
