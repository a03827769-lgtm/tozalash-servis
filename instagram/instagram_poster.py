"""
Tozalash Servis — Instagram Automation System
Instagram Graph API va avtomatik kontent posting
"""

import os
import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import httpx
from loguru import logger

from config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_BUSINESS_ACCOUNT_ID,
    BUSINESS_NAME,
    BUSINESS_PHONE,
    PRICES,
)

# ================================================
# INSTAGRAM KONTENT SHABLONLARI
# ================================================
CONTENT_TEMPLATES = {
    "promo": [
        """✨ {service_name}!

🏆 Toshkentdagi eng yaxshi tozalash kompaniyasi

💰 Narx: {price} so'mdan
⏱️ Vaqt: 2-4 soat
✅ Kafolat: 100%

📲 Buyurtma: @tozalash_servis_toshkent
📞 Tel: {phone}

#tozalash #cleaning #toshkent #tozalashservis #professional""",
        """🧹 {service_name} — Faqat bugun!

Uyingizni professional tozalash kerakmi?
Biz yordam beramiz! 🌟

✅ Tajribali mutaxassislar
✅ Eco-friendly tozalash vositalari  
✅ Kafoljat va sug'urta

💰 {price} so'mdan boshlab
📲 @tozalash_servis_toshkent yoki Tel: {phone}

#cleaningservice #tashkent #уборка #профессиональная""",
    ],
    "tip": [
        """💡 Foydali maslahat:

Divaningizni qanday yangiday saqlash mumkin?

1️⃣ Haftalik vakuum tozalash
2️⃣ Dog'larni zudlik bilan olib tashlang
3️⃣ Yiliga 1-2 marta professional tozalash

🔹 Professional tozalash uchun biz hozir tayyor!
📲 @tozalash_servis_toshkent | Tel: {phone}

#divanyuvish #sofa #cleaning #tip #tozalash""",
    ],
    "showcase": [
        """🌟 BEFORE & AFTER — Ko'ring!

Bizning professional tozalash xizmatimiz qanday natija beradi?

⬅️ OLDIN: Chang, dog', eski qo'lanish
➡️ KEYIN: Yangiday, tip-top toza!

💪 Biz har doim natija ko'rsatamiz!
📲 Buyurtma: @tozalash_servis_toshkent
📞 {phone}

#beforeafter #tozalash #cleaning #результат #Ташкент""",
    ],
    "seasonal": [
        """🏠 Bahor tozaligi vaqti keldi!

Uyingiz Navro'z bayramiga tayyor bo'lsin! 🌸

🧹 General tozalash paketi:
✅ Barcha xonalar
✅ Balkon va derazalar
✅ Mebellar
✅ Oshxona va hammom

📦 Paket narxi: 1,500,000 so'mdan
📲 @tozalash_servis_toshkent | Tel: {phone}

#navruz #bahor #tozalash #generalcleaning #tashkent""",
    ],
}


# ================================================
# INSTAGRAM POSTER
# ================================================
class InstagramPoster:
    """Instagram Graph API orqali kontent joylashtirish"""

    BASE_URL = "https://graph.instagram.com/v19.0"

    def __init__(self):
        self.access_token = INSTAGRAM_ACCESS_TOKEN
        self.account_id = INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.enabled = bool(
            self.access_token
            and self.account_id
            and self.access_token != "your_instagram_token_here"
        )
        if not self.enabled:
            logger.info(
                "ℹ️ Instagram API token o'rnatilmagan — posting o'tkazib yuboriladi"
            )

    async def post_image(self, image_url: str, caption: str) -> Optional[str]:
        """Instagram'ga rasm + caption joylash"""
        if not self.enabled:
            logger.info(f"[Instagram MOCK] Post qilindi:\n{caption[:80]}...")
            return "mock_post_id"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # 1. Media container yaratish
                r = await client.post(
                    f"{self.BASE_URL}/{self.account_id}/media",
                    params={
                        "image_url": image_url,
                        "caption": caption,
                        "access_token": self.access_token,
                    },
                )
                r.raise_for_status()
                container_id = r.json().get("id")

                if not container_id:
                    logger.error("Instagram: container_id olinmadi")
                    return None

                # 2. Media'ni publish qilish
                await asyncio.sleep(2)
                r2 = await client.post(
                    f"{self.BASE_URL}/{self.account_id}/media_publish",
                    params={
                        "creation_id": container_id,
                        "access_token": self.access_token,
                    },
                )
                r2.raise_for_status()
                post_id = r2.json().get("id")
                logger.info(f"✅ Instagram post: {post_id}")
                return post_id
        except Exception as e:
            logger.error(f"Instagram post xatosi: {e}")
            return None

    async def post_text_only(self, caption: str) -> bool:
        """Faqat matn (caption) joylash — test/mock uchun"""
        logger.info(f"[Instagram] Matn post:\n{caption[:100]}...")
        return True

    async def get_account_insights(self) -> Dict:
        """Akkaunt statistikasini olish"""
        if not self.enabled:
            return {"followers": 0, "reach": 0, "impressions": 0}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"{self.BASE_URL}/{self.account_id}/insights",
                    params={
                        "metric": "reach,impressions,profile_views,follower_count",
                        "period": "day",
                        "access_token": self.access_token,
                    },
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.warning(f"Instagram insights xatosi: {e}")
            return {}


# ================================================
# AUTO CONTENT MANAGER
# ================================================
class InstagramContentManager:
    """Instagram kontent tizimi — avtomatik post generatsiya va joylashtirish"""

    def __init__(self):
        self.poster = InstagramPoster()
        self._service_index = 0
        self.services = list(PRICES.keys())

    def _get_next_service(self) -> tuple:
        """Navbatdagi xizmatni olish (round-robin)"""
        service_key = self.services[self._service_index % len(self.services)]
        self._service_index += 1
        service = PRICES[service_key]
        return service_key, service

    def _format_price(self, price: int) -> str:
        """Narxni chiroyli formatlash"""
        return f"{price:,}".replace(",", " ")

    async def generate_post(self, post_type: str = "promo") -> str:
        """AI yordamida yoki shablon asosida post matnini yaratish"""
        service_key, service = self._get_next_service()
        service_name = service.get("name_uz", service_key)
        price = service.get("price", 0)

        templates = CONTENT_TEMPLATES.get(post_type, CONTENT_TEMPLATES["promo"])
        template = random.choice(templates)

        caption = template.format(
            service_name=service_name,
            price=self._format_price(price),
            phone=BUSINESS_PHONE,
            business_name=BUSINESS_NAME,
        )
        return caption

    async def schedule_daily_posts(self):
        """Kunlik Instagram postlarini rejalashtirish (APScheduler bilan ishlatiladi)"""
        post_types = ["promo", "tip", "showcase", "seasonal"]
        post_type = random.choice(post_types)

        caption = await self.generate_post(post_type)

        # Mock image URL (haqiqiy loyihada o'z rasmlaringizni ishlating)
        image_url = "https://via.placeholder.com/1080x1080.jpg?text=Tozalash+Servis"

        await self.poster.post_image(image_url, caption)
        logger.info(f"✅ Instagram kunlik post ({post_type}): muvaffaqiyatli!")


# Global singleton
instagram_manager = InstagramContentManager()
