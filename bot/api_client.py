import httpx
from typing import Dict, Any, List
from config import BASE_DIR
import os
from loguru import logger

API_BASE_URL = os.getenv("API_BASE_URL", "http://php:8000/api")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "tozalash_super_secret_key_2026")


class APIClient:
    def __init__(self):
        self.headers = {"X-API-KEY": API_SECRET_KEY, "Accept": "application/json"}

    async def get_customers(self, telegram_id: str = None) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            params = {}
            if telegram_id:
                params["telegram_id"] = telegram_id
            response = await client.get(
                f"{API_BASE_URL}/customers", headers=self.headers, params=params
            )
            response.raise_for_status()
            return response.json()

    async def create_customer(self, data: Dict) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/customers", headers=self.headers, json=data
            )
            if response.status_code not in (200, 201):
                logger.error(f"Failed to create customer: {response.text}")
            response.raise_for_status()
            return response.json()

    async def update_customer(self, id: int, data: Dict) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_BASE_URL}/customers/{id}", headers=self.headers, json=data
            )
            response.raise_for_status()
            return response.json()

    async def get_orders(self, telegram_id: str = None) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            params = {}
            if telegram_id:
                params["telegram_id"] = telegram_id
            response = await client.get(
                f"{API_BASE_URL}/orders", headers=self.headers, params=params
            )
            response.raise_for_status()
            return response.json()

    async def create_order(self, data: Dict) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/orders", headers=self.headers, json=data
            )
            if response.status_code not in (200, 201):
                logger.error(f"Failed to create order: {response.text}")
            response.raise_for_status()
            return response.json()


api_client = APIClient()
