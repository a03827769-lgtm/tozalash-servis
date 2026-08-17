import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import hmac
import hashlib
from unittest.mock import patch, AsyncMock

client = TestClient(app)


def test_watermark_image_invalid_type():
    response = client.post(
        "/api/v1/media/watermark/image",
        files={"image": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


def test_watermark_image_success():
    from PIL import Image
    import io

    img = Image.new("RGB", (100, 100), color="white")
    output = io.BytesIO()
    img.save(output, format="JPEG")
    output.seek(0)

    response = client.post(
        "/api/v1/media/watermark/image",
        files={"image": ("test.jpg", output.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200


def test_telephony_call_event():
    response = client.post(
        "/api/v1/media/telephony/call-event",
        json={"call_id": "123", "caller": "+998901234567", "duration_seconds": 60},
    )
    assert response.status_code == 200


@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_messaging_whatsapp(mock_post):
    mock_post.return_value.status_code = 200
    response = client.post(
        "/api/v1/messaging/whatsapp/send", json={"to": "998901234567", "body": "test"}
    )
    assert response.status_code == 200


@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_messaging_sms(mock_post):
    mock_post.return_value = MockResponse({"data": {"token": "test"}}, 200)
    response = client.post(
        "/api/v1/messaging/sms/send",
        json={"mobile_phone": "998901234567", "message": "test"},
    )
    assert response.status_code == 200


@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_abandoned_cart(mock_post):
    mock_post.return_value.status_code = 200
    response = client.post("/api/v1/messaging/abandoned-cart/trigger?user_id=123")
    assert response.status_code == 200


@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_birthday_trigger(mock_post):
    mock_post.return_value.status_code = 200
    response = client.post(
        "/api/v1/messaging/birthday/trigger?user_id=123&name=Ali&phone=998901234567"
    )
    assert response.status_code == 200


def test_bigdata_scrape():
    response = client.post("/api/v1/data/competitors/scrape")
    assert response.status_code == 200


def test_bigdata_price_alert():
    response = client.post(
        "/api/v1/data/alerts/price",
        json={"service": "Gilam", "threshold_price": 50000, "notify_channel": "sms"},
    )
    assert response.status_code == 200


def test_bigdata_iot():
    response = client.post(
        "/api/v1/data/iot/karcher/event",
        json={"device_id": "k1", "status": "active", "water_usage_liters": 10},
    )
    assert response.status_code == 200


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
def test_bigdata_weather(mock_get):
    mock_get.return_value = MockResponse({"weather": [{"main": "Rain"}]})
    response = client.get("/api/v1/data/weather/dynamic-pricing?city=Tashkent")
    assert response.status_code == 200


@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
def test_bigdata_air_quality(mock_get):
    mock_get.return_value = MockResponse(
        {"data": {"current": {"pollution": {"aqius": 50}}}}
    )
    response = client.get("/api/v1/data/air-quality?city=Tashkent&country=Uzbekistan")
    assert response.status_code == 200


def test_bigdata_heatmap():
    response = client.get("/api/v1/data/heatmap/orders")
    assert response.status_code == 200


def test_bigdata_forecasting():
    response = client.get("/api/v1/data/forecasting/demand")
    assert response.status_code == 200


def test_bigdata_marketing():
    response = client.post(
        "/api/v1/data/marketing/campaigns",
        json={"name": "test", "variant_a": "A", "variant_b": "B"},
    )
    assert response.status_code == 200


def test_bigdata_recommendations():
    response = client.get("/api/v1/data/recommendations/123")
    assert response.status_code == 200


def test_bigdata_feature_flags():
    response = client.get("/api/v1/data/feature-flags/new_dashboard?user_id=123")
    assert response.status_code == 200


def test_instagram_webhook_verify_success():
    token = os.getenv("INSTAGRAM_VERIFY_TOKEN", "tozalash_ig_token")
    response = client.get(
        f"/api/v1/bot/instagram/instagram/webhook?hub.mode=subscribe&hub.verify_token={token}&hub.challenge=123"
    )
    assert response.status_code == 200


def test_instagram_webhook_verify_fail():
    response = client.get(
        "/api/v1/bot/instagram/instagram/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=123"
    )
    assert response.status_code == 403


def test_instagram_webhook_post_success():
    body = b'{"object": "instagram"}'
    secret = os.getenv("INSTAGRAM_APP_SECRET", "")
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/bot/instagram/instagram/webhook",
        content=body,
        headers={"X-Hub-Signature-256": signature},
    )
    assert response.status_code == 200


def test_instagram_webhook_post_fail():
    body = b'{"object": "instagram"}'
    response = client.post(
        "/api/v1/bot/instagram/instagram/webhook",
        content=body,
        headers={"X-Hub-Signature-256": "wrong"},
    )
    assert response.status_code == 400
