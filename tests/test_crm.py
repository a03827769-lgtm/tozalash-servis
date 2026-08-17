import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_deps():
    async def override_get_current_user():
        return {"role": "admin"}

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


def test_crm_ltv_cac():
    response = client.get("/api/v1/crm/ltv-cac")
    assert response.status_code == 200


def test_crm_loyalty():
    response = client.get("/api/v1/crm/loyalty")
    assert response.status_code == 200


def test_crm_ltv_cac_unauthorized():
    async def override_get_current_user_user():
        return {"role": "user"}

    app.dependency_overrides[get_current_user] = override_get_current_user_user
    response = client.get("/api/v1/crm/ltv-cac")
    assert response.status_code == 403
