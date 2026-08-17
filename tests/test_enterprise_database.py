"""
Test Enterprise Database Layer (PostgreSQL / SQLite WAL fallback, Transactions & CRUD)
"""

import os
import pytest
from database import Database


@pytest.mark.asyncio
async def test_database_lifecycle_and_crud():
    test_db_file = "test_isolated_enterprise.db"
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

    test_db = Database()
    test_db.sqlite_path = test_db_file
    test_db.db_type = "sqlite"
    await test_db.init_db()
    
    # 1. Client CRUD
    test_tg_id = "test_user_998877"
    client = await test_db.get_or_create_client(test_tg_id, name="Test Alisher", language="uz")
    assert client is not None
    assert client["telegram_id"] == test_tg_id
    assert client["name"] == "Test Alisher"

    # 2. Update client
    await test_db.update_client(test_tg_id, address="Toshkent, Chilonzor 9-mavze")
    updated = await test_db.get_client(test_tg_id)
    assert updated["address"] == "Toshkent, Chilonzor 9-mavze"

    # 3. Create order
    order = await test_db.create_order(
        client_telegram_id=test_tg_id,
        service_type="divan_yuvish",
        service_name="Divan tozalash (3 o'rin)",
        total_price=240000.0,
        quantity=3.0,
        unit="o'rin",
        address="Toshkent, Chilonzor 9-mavze"
    )
    assert order is not None
    assert order["status"] == "yangi"
    assert float(order["total_price"]) == 240000.0

    # 4. Update order status
    await test_db.update_order_status(order["id"], "bajarildi")
    finished_order = await test_db.get_order(order["id"])
    assert finished_order["status"] == "bajarildi"

    await test_db.close()
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass
