"""
Tozalash Servis - Kanal va Instagram Automation
Telegram kanal va Instagram'da avtomatik kontent (va Rasm) joylashtirish
"""

import asyncio
import json
import random
import urllib.parse
from datetime import datetime, time
from typing import Optional, Dict, List
import httpx
from telegram import Bot
from loguru import logger

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL,
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_BUSINESS_ACCOUNT_ID,
    BUSINESS_NAME,
    BUSINESS_PHONE,
    CHANNEL_POST_TIMES,
)
from ai_brain import ai_brain
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot.services.search_trends import fetch_cleaning_trends, analyze_channel_history


class TelegramChannelManager:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.post_schedule = {
            "09:00": "morning",
            "12:00": "service_showcase",
            "18:00": "tip",
            "21:00": "promo",
        }
        self.services_rotation = [
            ("Uy tozalash", "regular_cleaning"),
            ("Ta'mirdan keyingi tozalash", "renovation_cleaning"),
            ("Divan yuvish", "sofa_cleaning"),
            ("Gilam yuvish", "carpet_cleaning"),
            ("Stul yuvish", "chair_cleaning"),
            ("Fasad tozalash", "facade_cleaning"),
            ("Oyna tozalash", "window_cleaning"),
            ("Plitka tozalash", "tile_cleaning"),
        ]
        self._service_index = 0

    async def post_to_channel(
        self, post_type: str, additional_context: str = None
    ) -> bool:
        try:
            # Internetdan yangi trendlarni qidirish
            trend_context = fetch_cleaning_trends()

            # Kanal tarixini tahlil qilish
            channel_history = await analyze_channel_history(TELEGRAM_CHANNEL)
            trend_context += f"\n\n{channel_history}"

            if additional_context:
                trend_context += f"\nQo'shimcha so'rov: {additional_context}"

            post_data = await ai_brain.generate_channel_post(post_type, trend_context)
            caption = post_data.get("text", "")
            image_prompt = post_data.get("image_prompt", "")

            if not caption:
                caption = self._get_fallback_post(post_type)

            if not image_prompt:
                image_prompt = f"Professional cleaning service, {post_type}, high quality photography, aesthetic"

            # Generate image via Pollinations AI (Free Text-to-Image API) using the AI generated prompt
            prompt = urllib.parse.quote(image_prompt)
            photo_url = f"https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1080&nologo=true"

            await self.bot.send_photo(
                chat_id=f"@{TELEGRAM_CHANNEL}",
                photo=photo_url,
                caption=caption,
            )

            logger.info(f"✅ Kanal rasm+post: {post_type} — muvaffaqiyatli!")
            return True

        except Exception as e:
            logger.error(f"Kanal post xatosi ({post_type}): {e}")
            return False

    async def post_with_photo(self, post_type: str, photo_url: str = None) -> bool:
        try:
            post_data = await ai_brain.generate_channel_post(post_type)
            caption = post_data.get("caption", "")

            if photo_url:
                await self.bot.send_photo(
                    chat_id=f"@{TELEGRAM_CHANNEL}",
                    photo=photo_url,
                    caption=caption,
                )
            else:
                await self.bot.send_message(
                    chat_id=f"@{TELEGRAM_CHANNEL}", text=caption
                )
            return True
        except Exception as e:
            logger.error(f"Rasm bilan post xatosi: {e}")
            return False

    def _get_fallback_post(self, post_type: str) -> str:
        fallbacks = {
            "morning": f"🌅 Xayrli tong!\n\nBugun uyingizni tozalaymiz! 📞 {BUSINESS_PHONE}",
            "service_showcase": f"🧹 {BUSINESS_NAME} xizmatlari\n\nHar qanday tozalash! 📞 {BUSINESS_PHONE}",
            "tip": f"💡 Maslahat\n\nGilamni uzoq saqlash uchun! 📞 {BUSINESS_PHONE}",
            "promo": f"🎁 Maxsus taklif!\n\n10% chegirma! 📞 {BUSINESS_PHONE}",
        }
        return fallbacks.get(post_type, fallbacks["morning"])

    async def get_next_service(self) -> tuple:
        service = self.services_rotation[
            self._service_index % len(self.services_rotation)
        ]
        self._service_index += 1
        return service

    async def run_scheduler(self):
        logger.info("📢 Telegram Kanal Scheduler ishga tushdi")
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            if current_time in self.post_schedule:
                post_type = self.post_schedule[current_time]
                if post_type == "service_showcase":
                    service_name, service_key = await self.get_next_service()
                    await self.post_to_channel(post_type, service_name)
                else:
                    await self.post_to_channel(post_type)
                await asyncio.sleep(61)
            else:
                await asyncio.sleep(30)

    async def send_broadcast(self, message: str):
        try:
            await self.bot.send_message(
                chat_id=f"@{TELEGRAM_CHANNEL}", text=message
            )
            logger.info("✅ Broadcast muvaffaqiyatli yuborildi")
        except Exception as e:
            logger.error(f"Broadcast xatosi: {e}")


class InstagramManager:
    def __init__(self):
        self.access_token = INSTAGRAM_ACCESS_TOKEN
        self.account_id = INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.api_base = "https://graph.instagram.com/v17.0"
        self.post_times = ["10:00", "14:00", "19:00"]
        self._last_post_times = {}

    async def get_unread_messages(self) -> List[Dict]:
        try:
            url = f"https://graph.facebook.com/v18.0/{self.account_id}/conversations"
            params = {
                "fields": "messages{message,from,created_time}",
                "access_token": self.access_token,
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()
                conversations = data.get("data", [])
                messages = []
                for conv in conversations:
                    conv_messages = conv.get("messages", {}).get("data", [])
                    for msg in conv_messages:
                        messages.append(
                            {
                                "conversation_id": conv.get("id"),
                                "message": msg.get("message", ""),
                                "from": msg.get("from", {}),
                                "created_time": msg.get("created_time", ""),
                            }
                        )
                return messages
        except Exception as e:
            logger.error(f"Instagram DM olish xatosi: {e}")
            return []

    async def reply_to_dm(self, conversation_id: str, message: str) -> bool:
        try:
            url = f"https://graph.facebook.com/v18.0/{self.account_id}/messages"
            payload = {
                "recipient": {"id": conversation_id},
                "message": {"text": message},
                "access_token": self.access_token,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info(f"✅ Instagram DM javobi yuborildi")
                    return True
                else:
                    logger.error(f"Instagram DM javob xatosi: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Instagram DM xatosi: {e}")
            return False

    async def process_dms(self):
        messages = await self.get_unread_messages()
        for msg in messages:
            try:
                user_message = msg.get("message", "")
                conv_id = msg.get("conversation_id")
                if not user_message or not conv_id:
                    continue
                ai_reply = await ai_brain.respond_to_instagram_dm(
                    message=user_message, user_info=msg.get("from", {})
                )
                await self.reply_to_dm(conv_id, ai_reply)
            except Exception as e:
                logger.error(f"DM qayta ishlash xatosi: {e}")

    async def post_to_instagram(self, caption: str, image_url: str = None) -> bool:
        try:
            if image_url:
                create_url = f"https://graph.facebook.com/v18.0/{self.account_id}/media"
                create_payload = {
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self.access_token,
                }
                async with httpx.AsyncClient() as client:
                    create_response = await client.post(create_url, data=create_payload)
                    create_data = create_response.json()
                    if "id" not in create_data:
                        logger.error(f"Instagram media yaratish xatosi: {create_data}")
                        return False
                    media_id = create_data["id"]

                    publish_url = f"https://graph.facebook.com/v18.0/{self.account_id}/media_publish"
                    publish_payload = {
                        "creation_id": media_id,
                        "access_token": self.access_token,
                    }
                    publish_response = await client.post(
                        publish_url, data=publish_payload
                    )
                    if publish_response.status_code == 200:
                        logger.info("✅ Instagram post muvaffaqiyatli!")
                        return True
            return False
        except Exception as e:
            logger.error(f"Instagram post xatosi: {e}")
            return False

    async def run_dm_handler(self):
        logger.info("📱 Instagram DM Handler ishga tushdi")
        while True:
            try:
                await self.process_dms()
            except Exception as e:
                logger.error(f"DM handler xatosi: {e}")
            await asyncio.sleep(300)

    async def run_post_scheduler(self):
        logger.info("📸 Instagram Post Scheduler ishga tushdi")
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            if current_time in self.post_times:
                time_key = f"{now.strftime('%Y-%m-%d')}-{current_time}"
                if time_key not in self._last_post_times:
                    self._last_post_times[time_key] = True
                    post_data = await ai_brain.generate_instagram_post()
                    caption = post_data.get("caption", "")
                    hashtags = post_data.get("hashtags", "")
                    full_caption = f"{caption}\n\n{hashtags}"

                    # Generate aesthetic image
                    prompt = urllib.parse.quote(
                        f"Aesthetic professional cleaning service, clean modern home interior, highly detailed"
                    )
                    photo_url = f"https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1080&nologo=true"

                    await self.post_to_instagram(full_caption, photo_url)
                    logger.info(
                        f"📸 Instagram post generatsiya qilindi: {current_time}"
                    )
                await asyncio.sleep(61)
            else:
                await asyncio.sleep(30)


class ContentManager:
    def __init__(self):
        self.telegram = TelegramChannelManager()
        self.instagram = InstagramManager()

    async def run_all(self):
        await asyncio.gather(
            self.telegram.run_scheduler(),
            self.instagram.run_dm_handler(),
            self.instagram.run_post_scheduler(),
        )


content_manager = ContentManager()
