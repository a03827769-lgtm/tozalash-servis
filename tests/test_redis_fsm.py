"""
Test Redis Manager: FSM State, Redlock Distributed Lock & Cache
"""

import pytest
from app.core.redis_manager import redis_manager


@pytest.mark.asyncio
async def test_fsm_state_set_and_get():
    user_id = "test_tg_12345"
    await redis_manager.set_fsm_state(user_id, "collecting_address", {"service": "divan_yuvish"})
    
    state_data = await redis_manager.get_fsm_state(user_id)
    assert state_data["state"] == "collecting_address"
    assert state_data["context"]["service"] == "divan_yuvish"

    await redis_manager.clear_fsm(user_id)
    cleared = await redis_manager.get_fsm_state(user_id)
    assert cleared["state"] == "idle"


@pytest.mark.asyncio
async def test_redlock_acquire_and_release():
    resource = "order_slot_2026_09_01_10_00"
    
    # 1. First acquire should succeed
    locked = await redis_manager.acquire_lock(resource, timeout_seconds=5)
    assert locked is True

    # 2. Second acquire on same resource should fail
    locked_again = await redis_manager.acquire_lock(resource, timeout_seconds=5)
    assert locked_again is False

    # 3. Release lock
    await redis_manager.release_lock(resource)

    # 4. Now acquire should succeed again
    locked_after = await redis_manager.acquire_lock(resource, timeout_seconds=5)
    assert locked_after is True
    await redis_manager.release_lock(resource)


@pytest.mark.asyncio
async def test_query_cache():
    cache_key = "pricing:sofa"
    data = {"name": "Divan yuvish", "price": 80000}
    
    await redis_manager.set_cache(cache_key, data, ttl=10)
    cached = await redis_manager.get_cache(cache_key)
    
    assert cached is not None
    assert cached["price"] == 80000
