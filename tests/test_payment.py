import pytest
from bot.payment import payment_providers


def test_payme_provider():
    provider = payment_providers["payme"]
    url = provider.generate_payment_url("TS-123", 500000)
    assert "checkout.paycom.uz" in url

    result = provider.verify_transaction({"action": 1})
    assert result["status"] == "success"


def test_click_provider():
    provider = payment_providers["click"]
    url = provider.generate_payment_url("TS-456", 300000)
    assert "my.click.uz" in url
    assert "amount=300000" in url
    assert "transaction_param=TS-456" in url

    result = provider.verify_transaction({"action": 1})
    assert result["status"] == "success"
