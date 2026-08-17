"""
Test Smart Dispatcher: Geospatial Cleaner Scoring & Assignment
"""

import pytest
from smart_dispatch import smart_dispatcher, haversine_distance


def test_haversine_distance():
    # Toshkent markazi va Chilonzor orasidagi masofa ~6-8 km
    lat1, lon1 = 41.311081, 69.240562
    lat2, lon2 = 41.285833, 69.203611
    dist = haversine_distance(lat1, lon1, lat2, lon2)
    assert 3.0 < dist < 10.0


@pytest.mark.asyncio
async def test_worker_scoring():
    worker = {
        "id": 1,
        "name": "Rustam",
        "rating": 4.9,
        "completed_orders": 25,
        "current_lat": 41.310000,
        "current_lon": 69.240000,
        "skills": "divan_yuvish,gilam_yuvish,universal",
    }
    order = {
        "lat": 41.311081,
        "lon": 69.240562,
        "service_type": "divan_yuvish",
    }

    score = await smart_dispatcher.calculate_worker_score(worker, order)
    # Rustam yaqin, yuqori reytingli va ko'nikmali bo'lgani uchun 80+ ball olishi kerak
    assert score >= 75.0
