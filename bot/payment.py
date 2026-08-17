import base64
import json
import hashlib
from typing import Dict, Optional
from loguru import logger
import os


class PaymeProvider:
    """Payme to'lov tizimi uchun provayder (Sandbox/Test rejim)"""

    def __init__(self):
        self.merchant_id = os.getenv("PAYME_MERCHANT_ID", "test_merchant_id")
        self.secret_key = os.getenv("PAYME_SECRET_KEY", "test_secret_key")
        self.endpoint = "https://checkout.paycom.uz"

    def generate_payment_url(self, order_id: str, amount: float) -> str:
        """Payme to'lov havolasini yaratish"""
        amount_tiyin = int(amount * 100)
        params = f"m={self.merchant_id};ac.order_id={order_id};a={amount_tiyin}"
        encoded = base64.b64encode(params.encode("utf-8")).decode("utf-8")
        return f"{self.endpoint}/{encoded}"

    def verify_transaction(self, request_data: Dict) -> Dict:
        """To'lovni tasdiqlash uchun webhook logikasi (soddalashtirilgan)"""
        # Aslida bu yerda signature tekshiriladi
        return {"status": "success", "message": "Payme to'lov tasdiqlandi"}


class ClickProvider:
    """Click to'lov tizimi uchun provayder (Sandbox/Test rejim)"""

    def __init__(self):
        self.merchant_id = os.getenv("CLICK_MERCHANT_ID", "test_merchant_id")
        self.service_id = os.getenv("CLICK_SERVICE_ID", "test_service_id")
        self.secret_key = os.getenv("CLICK_SECRET_KEY", "test_secret_key")
        self.merchant_user_id = os.getenv("CLICK_MERCHANT_USER_ID", "test_user_id")
        self.endpoint = "https://my.click.uz/services/pay"

    def generate_payment_url(self, order_id: str, amount: float) -> str:
        """Click to'lov havolasini yaratish"""
        url = f"{self.endpoint}?service_id={self.service_id}&merchant_id={self.merchant_id}&amount={amount}&transaction_param={order_id}"
        return url

    def verify_transaction(self, request_data: Dict) -> Dict:
        """Click to'lov webhook signaturasini tekshirish"""
        click_trans_id = request_data.get("click_trans_id")
        service_id = request_data.get("service_id")
        secret_key = self.secret_key
        merchant_trans_id = request_data.get("merchant_trans_id")
        amount = request_data.get("amount")
        action = request_data.get("action")
        sign_time = request_data.get("sign_time")
        sign_string = request_data.get("sign_string")

        # MOCK verification for sandbox
        return {"status": "success", "message": "Click to'lov tasdiqlandi"}


payment_providers = {"payme": PaymeProvider(), "click": ClickProvider()}
