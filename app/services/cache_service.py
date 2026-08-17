import json
from typing import Optional, Dict, Any
from app.core.redis_manager import redis_manager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order


async def get_order_cache_aside(session: AsyncSession, order_id: int) -> Optional[Dict[str, Any]]:
    """
    Task 23: Cache-Aside Strategy
    Checks Redis first (via RedisManager with in-memory fallback). If not found, fetches from DB and stores in cache.
    Good for read-heavy operations.
    """
    cache_key = f"order:{order_id}"

    # 1. Check Cache
    cached_data = await redis_manager.get_cache(cache_key)
    if cached_data:
        return cached_data if isinstance(cached_data, dict) else json.loads(cached_data)

    # 2. Fetch from DB if Cache Miss
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if order:
        order_dict = {
            "id": order.id,
            "amount": getattr(order, "amount", getattr(order, "total_price", 0.0)),
            "status": order.status,
            "client_name": getattr(order, "client_name", "Client"),
        }
        # 3. Store in Cache for next time (TTL 1 hour)
        await redis_manager.set_cache(cache_key, order_dict, ttl=3600)
        return order_dict

    return None


async def update_order_write_through(
    session: AsyncSession, order_id: int, new_status: Any
) -> Optional[Dict[str, Any]]:
    """
    Task 23: Write-Through Strategy
    Updates the Database and immediately updates the Cache.
    Ensures data consistency across DB and Cache.
    """
    # 1. Update Database
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        return None

    order.status = new_status
    await session.commit()

    # 2. Update Cache Immediately
    cache_key = f"order:{order_id}"
    order_dict = {
        "id": order.id,
        "amount": getattr(order, "amount", getattr(order, "total_price", 0.0)),
        "status": order.status,
        "client_name": getattr(order, "client_name", "Client"),
    }
    await redis_manager.set_cache(cache_key, order_dict, ttl=3600)

    return order_dict
