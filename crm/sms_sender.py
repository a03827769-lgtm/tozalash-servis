import aiohttp
import os
import json
from loguru import logger


class EskizSMS:
    def __init__(self):
        self.email = os.getenv("ESKIZ_EMAIL")
        self.password = os.getenv("ESKIZ_PASSWORD")
        self.base_url = "https://notify.eskiz.uz/api"
        self.token = None

    async def authenticate(self):
        """Eskiz API orqali autentifikatsiya qilish va token olish"""
        if not self.email or not self.password:
            logger.warning(
                "ESKIZ_EMAIL yoki ESKIZ_PASSWORD .env faylida ko'rsatilmagan. SMS yuborish simulyatsiya qilinadi."
            )
            return False

        try:
            async with aiohttp.ClientSession() as session:
                payload = {"email": self.email, "password": self.password}
                async with session.post(
                    f"{self.base_url}/auth/login", data=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.token = data["data"]["token"]
                        return True
                    else:
                        logger.error(
                            f"Eskiz autentifikatsiya xatosi: {await response.text()}"
                        )
                        return False
        except Exception as e:
            logger.error(f"Eskiz ulanish xatosi: {e}")
            return False

    async def send_sms(self, phone: str, message: str) -> bool:
        """Mijozga SMS xabar yuborish"""
        # Telefon raqamini formatlash (+998901234567 -> 998901234567)
        phone = "".join(filter(str.isdigit, phone))

        if not self.token:
            if not await self.authenticate():
                logger.info(f"[SIMULATSIYA] {phone} raqamiga SMS yuborildi: {message}")
                return True  # Simulyatsiya muvaffaqiyatli deb hisoblaymiz

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.token}"}
                payload = {
                    "mobile_phone": phone,
                    "message": message,
                    "from": "4546",  # Eskiz default sender
                }
                async with session.post(
                    f"{self.base_url}/message/sms/send", headers=headers, data=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"SMS muvaffaqiyatli yuborildi: {phone}")
                        return True
                    else:
                        logger.error(f"SMS yuborishda xato: {await response.text()}")
                        return False
        except Exception as e:
            logger.error(f"SMS API xatosi: {e}")
            return False


sms_sender = EskizSMS()
