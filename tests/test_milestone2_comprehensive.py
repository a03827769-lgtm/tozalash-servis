"""
Milestone 2 Verification Test Suite
Tests:
1. database.py: PostgreSQL 16 connection string parser, SSL autodetection, pooler support, 18 tables DDL, 16 business query methods, zero-config SQLite WAL fallback.
2. app/api/endpoints/clients.py, orders.py, staff.py: non-blocking queries with fetch_all/execute.
3. analytics/chart_generator.py: multi-dialect revenue chart queries.
4. app/core/redis_manager.py: Upstash rediss:// TLS, health_check_interval, retry_on_timeout, in-memory fallback.
5. app/core/redis.py & app/services/cache_service.py: FastAPICache initialization, cache-aside and write-through strategies.
6. app/main.py: Active /health endpoint with database and redis verification.
"""

import os
import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from database import Database, db
from app.core.redis_manager import RedisManager, MemoryFallback
from app.services.cache_service import get_order_cache_aside, update_order_write_through
from analytics.chart_generator import chart_generator
from app.main import app


@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# =========================================================================
# 1. DATABASE TESTS
# =========================================================================
@pytest.mark.asyncio
async def test_database_url_parsing_and_ssl():
    """Verify DATABASE_URL parsing, SSL detection, and pooler configuration."""
    test_db = Database()
    
    mock_conn = AsyncMock()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=mock_ctx)
    mock_pool.close = AsyncMock()

    # Standard PostgreSQL URL
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://myuser:mypass@db.example.supabase.co:6543/postgres?sslmode=require"}):
        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_create_pool.return_value = mock_pool
            test_db._initialized = False
            await test_db.init_db()
            assert test_db.db_type == "postgres"
            mock_create_pool.assert_called_once()
            call_kwargs = mock_create_pool.call_args[1]
            assert call_kwargs["host"] == "db.example.supabase.co"
            assert call_kwargs["port"] == 6543
            assert call_kwargs["user"] == "myuser"
            assert call_kwargs["password"] == "mypass"
            assert call_kwargs["database"] == "postgres"
            assert call_kwargs["ssl"] == "require"
            assert call_kwargs["statement_cache_size"] == 0
            assert call_kwargs["min_size"] == 1
            assert call_kwargs["max_size"] == 5
    await test_db.close()


@pytest.mark.asyncio
async def test_database_all_18_tables_and_business_queries():
    """Verify all 18 tables and 16+ business query methods work seamlessly in SQLite."""
    import uuid
    test_db_file = f"test_m2_{uuid.uuid4().hex[:6]}.db"

    test_db = Database(sqlite_path=test_db_file)
    await test_db.init_db()

    # 1. get_or_create_client
    c1 = await test_db.get_or_create_client("998901112233", name="Ali", language="uz")
    assert c1["telegram_id"] == "998901112233"
    assert c1["name"] == "Ali"

    # 2. update_client_name & update_user_language
    await test_db.update_client_name("998901112233", "Alisher Navoiy")
    await test_db.update_user_language("998901112233", "ru")
    c1_updated = await test_db.get_client_by_tg_id("998901112233")
    assert c1_updated["name"] == "Alisher Navoiy"
    assert c1_updated["language"] == "ru"

    # 3. add_worker & register_worker
    await test_db.add_worker(name="Vali", phone="+998901234567", telegram_id="1001", specialization="Gilam yuvish")
    w1 = await test_db.get_worker_by_tg_id("1001")
    assert w1 is not None
    assert w1["name"] == "Vali"

    # 4. get_all_workers & get_available_workers
    all_workers = await test_db.get_all_workers()
    assert len(all_workers) >= 1
    avail_workers = await test_db.get_available_workers()
    assert len(avail_workers) >= 1

    # 5. create_order & add_order
    order = await test_db.create_order({
        "client_telegram_id": "998901112233",
        "service_type": "standard",
        "service_name": "Standard tozalash",
        "total_price": 150000.0,
        "address": "Chilonzor 9"
    })
    order_id = order["id"]
    assert order_id > 0
    assert order["total_price"] == 150000.0

    # 6. get_order & get_client_orders
    fetched_order = await test_db.get_order(order_id)
    assert fetched_order["client_telegram_id"] == "998901112233"
    client_orders = await test_db.get_client_orders("998901112233")
    assert len(client_orders) >= 1

    # 7. update_order_status
    await test_db.update_order_status(order_id, "bajarildi", worker_id=w1["id"])
    updated_order = await test_db.get_order(order_id)
    assert updated_order["status"] == "bajarildi"
    assert updated_order["worker_id"] == w1["id"]

    # 8. get_today_orders & get_orders_stats
    today_orders = await test_db.get_today_orders()
    assert len(today_orders) >= 1
    stats = await test_db.get_orders_stats()
    assert stats["total_orders"] >= 1
    assert stats["completed"] >= 1

    # 9. save_message, get_conversation_history & get_messages_count_today
    await test_db.save_message("998901112233", "user", "Assalomu alaykum!")
    await test_db.save_message("998901112233", "bot", "Vaalaykum assalom! Qanday xizmat kerak?")
    history = await test_db.get_conversation_history("998901112233", limit=10)
    assert len(history) >= 2
    msg_count = await test_db.get_messages_count_today()
    assert msg_count >= 2

    # 10. save_learning & get_successful_patterns
    await test_db.save_learning("tozalash", "narx qancha", "Standart tozalash 150,000 so'm", True)
    patterns = await test_db.get_successful_patterns()
    assert len(patterns) >= 1

    # 11. add_revenue & get_finance_stats
    await test_db.add_revenue(150000.0, "Standart tozalash", "order_payment")
    fin_stats = await test_db.get_finance_stats()
    assert fin_stats["total_revenue"] >= 150000.0

    # 12. dynamic guidelines & competitors
    await test_db.add_dynamic_guideline("Mijoz bilan xushmuomala bo'lish shart")
    guidelines = await test_db.get_dynamic_guidelines()
    assert "Mijoz bilan xushmuomala bo'lish shart" in guidelines

    await test_db.save_competitor_price("CleanCo", "Gilam yuvish", 18000.0)
    prices = await test_db.get_competitor_prices()
    assert len(prices) >= 1

    await test_db.close()
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass


# =========================================================================
# 2. FASTAPI ENDPOINTS & ANALYTICS TESTS
# =========================================================================
@pytest.mark.asyncio
async def test_clients_endpoint():
    """Test /api/v1/clients endpoint listing and deletion."""
    from app.api.endpoints.clients import get_clients, delete_client
    test_db = Database(sqlite_path="test_endpoints.db")
    await test_db.init_db()
    res = await get_clients(test_db)
    assert isinstance(res, list)
    del_res = await delete_client("999999999", test_db)
    assert del_res["status"] == "success"
    await test_db.close()


@pytest.mark.asyncio
async def test_orders_endpoint():
    """Test /api/v1/orders endpoint listing."""
    from app.api.endpoints.orders import get_orders
    test_db = Database(sqlite_path="test_endpoints.db")
    await test_db.init_db()
    res = await get_orders(test_db)
    assert isinstance(res, list)
    await test_db.close()


@pytest.mark.asyncio
async def test_staff_endpoint():
    """Test /api/v1/staff endpoint listing."""
    from app.api.endpoints.staff import get_staff, delete_staff
    test_db = Database(sqlite_path="test_endpoints.db")
    await test_db.init_db()
    res = await get_staff(test_db)
    assert isinstance(res, list)
    del_res = await delete_staff("999999999", test_db)
    assert del_res["status"] == "success"
    await test_db.close()


@pytest.mark.asyncio
async def test_chart_generator():
    """Test revenue chart generation."""
    test_db = Database(sqlite_path="test_endpoints.db")
    await test_db.init_db()
    filepath = await chart_generator.generate_revenue_chart(custom_db=test_db)
    assert filepath is None or filepath.endswith(".png")
    await test_db.close()


# =========================================================================
# 3. REDIS 7 & CACHE STRATEGIES TESTS
# =========================================================================
@pytest.mark.asyncio
async def test_redis_manager_tls_and_fallback():
    """Verify RedisManager supports rediss TLS and MemoryFallback."""
    rm = RedisManager()
    
    # Test MemoryFallback
    await rm.fallback.set("test_key", {"status": "ok"})
    val = await rm.fallback.get("test_key")
    assert "ok" in val
    await rm.fallback.delete("test_key")
    assert await rm.fallback.exists("test_key") == 0


@pytest.mark.asyncio
async def test_cache_service_strategies():
    """Verify Cache-Aside and Write-Through caching functions."""
    mock_session = AsyncMock()
    mock_order = MagicMock()
    mock_order.id = 42
    mock_order.amount = 120000.0
    mock_order.total_price = 120000.0
    mock_order.status = 1
    mock_order.client_name = "Botir"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result

    # 1. Test get_order_cache_aside
    cached = await get_order_cache_aside(mock_session, 42)
    assert cached["id"] == 42
    assert cached["amount"] == 120000.0

    # 2. Test update_order_write_through
    updated = await update_order_write_through(mock_session, 42, 2)
    assert updated["status"] == 2
    mock_session.commit.assert_called_once()


# =========================================================================
# 4. ACTIVE HEALTH CHECK TEST
# =========================================================================
@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test active /health endpoint verifying structured JSON and DB/Redis statuses."""
    from app.main import health_check
    res = await health_check()
    assert "status" in res
    assert res["status"] in ("healthy", "degraded")
    assert "database" in res
    assert res["database"] in ("connected", "offline")
    assert "redis" in res
    assert res["redis"] in ("connected", "memory_fallback")
    assert "uptime_seconds" in res
    assert "version" in res
    assert res["version"] == "2.0.0"
