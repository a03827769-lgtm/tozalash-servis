import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_deps():
    async def override_get_current_user():
        return {"role": "user"}

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


def test_inventory_warehouse():
    response = client.get("/api/v1/inventory/warehouse")
    assert response.status_code == 200


def test_inventory_pricing():
    response = client.post(
        "/api/v1/inventory/pricing/calculate", json={"base_price": 200000}
    )
    assert response.status_code == 200
    assert response.json()["final_price"] == 200000 * 1.2 * 0.95
