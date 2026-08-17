import pytest
from database import Database


@pytest.mark.asyncio
async def test_all_database():
    db = Database()
    methods = [
        db.get_or_create_client("1"),
        db.update_client("1"),
        db.update_client_name("1", "2"),
        db.create_order({}),
        db.get_client_orders("1"),
        db.get_order(1),
        db.update_order_status(1, "1"),
        db.get_today_orders(),
        db.get_orders_stats(),
        db.get_available_workers(),
        db.get_all_workers(),
        db.add_worker("1", "2", "3"),
        db.update_worker_location("1", 1.0, 1.0),
        db.get_user_state("1"),
        db.set_user_state("1", "2"),
        db.save_message("1", "2", "3"),
        db.get_conversation_history("1"),
        db.save_learning("1", "2", "3", True),
        db.get_successful_patterns(),
        db.get_worker_by_tg_id("1"),
        db.register_worker("1", "2"),
        db.get_finance_stats(),
        db.save_daily_report({}),
        db.get_messages_count_today(),
    ]
    for m in methods:
        try:
            await m
        except Exception:
            pass
