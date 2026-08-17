"""
Adversarial Stress Test Suite for Milestone 2:
Empirically stress-tests:
1. RedisManager fallback under network failure, socket timeouts, and invalid rediss:// credentials.
2. CacheService Cache-Aside and Write-Through caching patterns with RedisManager.
3. Active /health endpoint in healthy and degraded states (testing for NameErrors, timeouts, and JSON schema).
4. Database Dialect Normalization, SQLite WAL resiliency, and multi-event-loop lock behavior.
5. FastAPI Lifespan and Redis initialization error resilience.
"""

import os
import sys
import json
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport

from database import Database, db
from app.core.redis_manager import RedisManager, MemoryFallback
from app.services.cache_service import get_order_cache_aside, update_order_write_through


# =============================================================================
# 1. REDIS MANAGER RESILIENCE & FALLBACK ADVERSARIAL TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_redis_manager_invalid_rediss_url_fallback():
    """Stress-test: Invalid rediss:// credentials must NOT crash or hang, but fallback to MemoryFallback."""
    rm = RedisManager()
    rm.redis_url = "rediss://invalid_user:fake_token_12345@unreachable-redis-host.upstash.io:6379/0"
    rm._is_connected = False
    rm.client = None

    # Init should catch connection/DNS/auth failure and return False gracefully
    connected = await rm.init()
    assert connected is False
    assert rm._is_connected is False
    assert rm.client is None

    # FSM state operations under fallback
    user_id = "test_user_adv_999"
    set_res = await rm.set_fsm_state(user_id, "ordering", {"service": "cleaning", "price": 100000})
    assert set_res is True

    fsm_state = await rm.get_fsm_state(user_id)
    assert fsm_state["state"] == "ordering"
    assert fsm_state["context"]["service"] == "cleaning"

    # FSM clear
    clear_res = await rm.clear_fsm(user_id)
    assert clear_res is True
    fsm_after = await rm.get_fsm_state(user_id)
    assert fsm_after["state"] == "idle"


@pytest.mark.asyncio
async def test_redis_manager_redlock_concurrency_fallback():
    """Stress-test: Redlock atomic acquire and release under MemoryFallback."""
    rm = RedisManager()
    rm._is_connected = False
    rm.client = None
    resource = "room_assignment_101"

    # First acquire succeeds
    lock1 = await rm.acquire_lock(resource, timeout_seconds=5)
    assert lock1 is True

    # Second concurrent acquire on same resource MUST fail (mutual exclusion)
    lock2 = await rm.acquire_lock(resource, timeout_seconds=5)
    assert lock2 is False

    # Release lock
    await rm.release_lock(resource)

    # Now acquire should succeed again
    lock3 = await rm.acquire_lock(resource, timeout_seconds=5)
    assert lock3 is True
    await rm.release_lock(resource)


@pytest.mark.asyncio
async def test_redis_manager_pubsub_fallback():
    """Stress-test: Pub/Sub message delivery under MemoryFallback."""
    rm = RedisManager()
    rm._is_connected = False
    rm.client = None
    channel = "order_notifications"

    received_messages = []

    def sync_listener(msg):
        received_messages.append(json.loads(msg) if isinstance(msg, str) else msg)

    async def async_listener(msg):
        received_messages.append(json.loads(msg) if isinstance(msg, str) else msg)

    rm.fallback.subscribe_callback(channel, sync_listener)
    rm.fallback.subscribe_callback(channel, async_listener)

    payload = {"event": "order_created", "order_id": 789}
    delivered_count = await rm.publish(channel, payload)
    assert delivered_count == 2

    # Give async task time to execute
    await asyncio.sleep(0.05)
    assert len(received_messages) == 2
    assert received_messages[0]["order_id"] == 789
    assert received_messages[1]["event"] == "order_created"


@pytest.mark.asyncio
async def test_redis_manager_cache_serialization_adversarial():
    """Stress-test: Complex data structures (nested dicts, unicode, ints, booleans) in get_cache/set_cache."""
    rm = RedisManager()
    rm._is_connected = False
    rm.client = None

    complex_data = {
        "user_id": 12345,
        "name": "Тест Очистка Xizmati 🇺🇿",
        "nested": {"level1": {"items": [1, 2, 3], "flag": True}},
        "price": 250000.50
    }

    key = "complex_adv_cache_key"
    await rm.set_cache(key, complex_data, ttl=60)
    cached = await rm.get_cache(key)
    assert cached is not None
    if isinstance(cached, str):
        cached = json.loads(cached)
    assert cached["name"] == "Тест Очистка Xizmati 🇺🇿"
    assert cached["nested"]["level1"]["flag"] is True
    assert cached["price"] == 250000.50


# =============================================================================
# 2. CACHE SERVICE (CACHE-ASIDE & WRITE-THROUGH) TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_cache_aside_hit_miss_and_nonexistent():
    """Stress-test: Cache-Aside strategy on hit, miss, and non-existent records."""
    rm = RedisManager()
    rm._is_connected = False
    rm.client = None
    rm.fallback._data.clear()

    order_id = 901
    mock_session = AsyncMock()

    # Case 1: Cache Miss -> Query DB and Populate Cache
    mock_db_order = MagicMock()
    mock_db_order.id = order_id
    mock_db_order.amount = 350000.0
    mock_db_order.total_price = 350000.0
    mock_db_order.status = "yangi"
    mock_db_order.client_name = "Farxod"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_db_order
    mock_session.execute.return_value = mock_result

    res1 = await get_order_cache_aside(mock_session, order_id)
    assert res1 is not None
    assert res1["id"] == order_id
    assert res1["amount"] == 350000.0
    assert mock_session.execute.call_count == 1

    # Verify item is now in cache
    cached_val = await rm.get_cache(f"order:{order_id}")
    assert cached_val is not None

    # Case 2: Cache Hit -> Read from Cache, DB MUST NOT be queried again
    mock_session.execute.reset_mock()
    res2 = await get_order_cache_aside(mock_session, order_id)
    assert res2 is not None
    assert res2["id"] == order_id
    assert mock_session.execute.call_count == 0  # Zero DB queries on cache hit!

    # Case 3: Non-existent order
    non_existent_id = 99999
    mock_result_none = MagicMock()
    mock_result_none.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result_none

    res3 = await get_order_cache_aside(mock_session, non_existent_id)
    assert res3 is None


@pytest.mark.asyncio
async def test_write_through_consistency():
    """Stress-test: Write-Through updates DB and immediately synchronizes Cache."""
    rm = RedisManager()
    rm._is_connected = False
    rm.client = None
    rm.fallback._data.clear()

    order_id = 902
    mock_session = AsyncMock()

    mock_db_order = MagicMock()
    mock_db_order.id = order_id
    mock_db_order.amount = 400000.0
    mock_db_order.total_price = 400000.0
    mock_db_order.status = "jarayonda"
    mock_db_order.client_name = "Zulayho"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_db_order
    mock_session.execute.return_value = mock_result

    # 1. Update status via Write-Through
    new_status = "bajarildi"
    updated_res = await update_order_write_through(mock_session, order_id, new_status)
    assert updated_res is not None
    assert updated_res["status"] == "bajarildi"
    assert mock_db_order.status == "bajarildi"
    mock_session.commit.assert_called_once()

    # 2. Verify cache has the updated status immediately
    mock_session.execute.reset_mock()
    cached_fetch = await get_order_cache_aside(mock_session, order_id)
    assert cached_fetch is not None
    assert cached_fetch["status"] == "bajarildi"
    assert mock_session.execute.call_count == 0  # Served from cache without DB trip


# =============================================================================
# 3. ACTIVE /HEALTH ENDPOINT & RUNTIME DEFECT VERIFICATION
# =============================================================================

@pytest.mark.asyncio
async def test_health_check_healthy_and_degraded_live():
    """Stress-test: Test /health endpoint directly to check for NameErrors (asyncio/os) and valid schema."""
    import app.main as main_module
    from app.main import app

    # Verify if asyncio is accessible in main_module
    assert hasattr(main_module, "asyncio") or "asyncio" in main_module.__dict__, (
        "CRITICAL DEFECT: 'asyncio' is not imported in app/main.py!"
    )

    # Initialize DB for healthy check
    test_db = Database(sqlite_path="test_adv_health.db")
    await test_db.init_db()

    with patch("app.main.db", test_db):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["database"] == "connected", f"Expected database 'connected', got {data['database']}"
            assert data["status"] == "healthy", f"Expected overall status 'healthy', got {data['status']}"
            assert "redis" in data
            assert data["redis"] in ("connected", "memory_fallback")
            assert data["version"] == "2.0.0"
            assert "uptime_seconds" in data

    # Degraded state test (DB offline)
    mock_offline_db = AsyncMock()
    mock_offline_db.fetch_one.side_effect = Exception("Connection refused / database unreachable")

    with patch("app.main.db", mock_offline_db):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["database"] == "offline"
            assert data["status"] == "degraded"

    await test_db.close()
    if os.path.exists("test_adv_health.db"):
        try:
            os.remove("test_adv_health.db")
        except Exception:
            pass


@pytest.mark.asyncio
async def test_redis_init_runtime_defect_check():
    """Verify app.core.redis.init_redis does not fail with NameError ('os' missing)."""
    import app.core.redis as redis_module
    from fastapi import FastAPI

    assert hasattr(redis_module, "os") or "os" in redis_module.__dict__, (
        "CRITICAL DEFECT: 'os' is not imported in app/core/redis.py!"
    )

    test_app = FastAPI()
    # Call init_redis with unreachable redis - should fallback cleanly without NameError
    with patch("app.core.config.settings.REDIS_URL", "redis://invalid-host-999:6379"):
        await redis_module.init_redis(test_app)
        assert hasattr(test_app.state, "limiter")


# =============================================================================
# 4. DATABASE ENGINE NORMALIZATION & RECOVERY TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_database_dialect_query_normalization():
    """Stress-test: Normalization of Postgres vs SQLite placeholders and dates."""
    sqlite_db = Database(sqlite_path=":memory:")
    sqlite_db.db_type = "sqlite"

    q_sqlite = sqlite_db._normalize_query("SELECT * FROM orders WHERE status = %s AND created_at >= CURDATE()")
    assert "%s" not in q_sqlite
    assert "?" in q_sqlite
    assert "DATE('now')" in q_sqlite

    pg_db = Database()
    pg_db.db_type = "postgres"

    q_pg = pg_db._normalize_query("SELECT * FROM orders WHERE status = %s AND amount > %s AND created_at >= CURDATE()")
    assert "%s" not in q_pg
    assert "$1" in q_pg
    assert "$2" in q_pg
    assert "CURRENT_DATE" in q_pg


@pytest.mark.asyncio
async def test_database_idempotent_init_and_locks():
    """Stress-test: Calling init_db multiple times concurrently must be safe and idempotent."""
    test_db = Database(sqlite_path="test_adv_idempotent.db")

    # Run 5 concurrent init_db calls
    tasks = [test_db.init_db() for _ in range(5)]
    await asyncio.gather(*tasks)

    assert test_db._initialized is True
    # Verify table works
    client = await test_db.get_or_create_client("998909998877", name="Sobir")
    assert client["name"] == "Sobir"

    await test_db.close()
    if os.path.exists("test_adv_idempotent.db"):
        try:
            os.remove("test_adv_idempotent.db")
        except Exception:
            pass
