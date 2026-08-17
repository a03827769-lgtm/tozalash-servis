import asyncio
import random
from loguru import logger
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from datetime import datetime
from database import db
from swarm_agents import SwarmOrchestrator

# Global state for anti-ban tracking
class OutreachState:
    def __init__(self):
        self.dms_sent_today = 0
        self.last_reset_date = datetime.now().date()
        self.is_paused = False

state_db = OutreachState()
swarm = SwarmOrchestrator()

async def human_delay(min_sec=300, max_sec=900):
    """Gaussian/Uniform distributed delay between 5 to 15 minutes for cold outreach."""
    delay = random.uniform(min_sec, max_sec)
    logger.info(f"Botuxlayapti (human delay): {int(delay)} soniya...")
    await asyncio.sleep(delay)

async def send_human_message(client: Client, chat_id, text: str):
    # 1. Simulate reading time (1.5 - 3.5s)
    await asyncio.sleep(random.uniform(1.5, 3.5))
    
    # 2. Simulate typing status based on text length
    typing_duration = max(2.0, min(len(text) * 0.06, 12.0))
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(typing_duration)
    
    # 3. Send message
    return await client.send_message(chat_id, text)

async def safe_dispatch(client: Client, target_id, message_text: str):
    from pyrogram.errors import FloodWait, PeerFlood, UserPrivacyRestricted, UserDeactivated, UserBlocked
    try:
        await send_human_message(client, target_id, message_text)
        state_db.dms_sent_today += 1
        logger.success(f"Outreach yuborildi: {target_id}")
        return True

    except FloodWait as e:
        logger.warning(f"FloodWait! {e.value + 30} soniya kutilmoqda...")
        await asyncio.sleep(e.value + 30)
        return False

    except PeerFlood:
        logger.critical("PeerFlood Xatosi! Spam himoyasi ishladi. 48 soatga outreach to'xtatildi.")
        state_db.is_paused = True
        return False

    except (UserPrivacyRestricted, UserDeactivated, UserBlocked) as e:
        logger.info(f"Yuborib bo'lmadi {target_id}: {str(e)}")
        return False

async def monitor_groups_for_leads(client: Client, message):
    """Monitors specific groups for target keywords (e.g. 'gilam yuvish')."""
    if state_db.is_paused:
        return

    current_date = datetime.now().date()
    if current_date > state_db.last_reset_date:
        state_db.dms_sent_today = 0
        state_db.last_reset_date = current_date

    # Max DMs per day (Anti-Ban)
    if state_db.dms_sent_today >= 20:
        return

    # Check Business Hours (09:00 - 19:30)
    hour = datetime.now().hour
    if hour < 9 or hour > 19:
        return

    text = message.text or message.caption or ""
    text_lower = text.lower()
    
    # Target keywords for cleaning services
    keywords = ["gilam yuvish", "tozalash", "karcher", "mebel yuvish", "tozalatish"]
    
    if any(kw in text_lower for kw in keywords):
        user = message.from_user
        if not user or user.is_self or user.is_bot:
            return

        logger.info(f"Target topildi guruhda ({message.chat.title}): {user.first_name} - {text[:50]}")
        
        # Generate Icebreaker using Swarm
        target_agent = swarm.registry.get_agent("icebreaker_agent")
        if target_agent:
            context = {
                "group_name": message.chat.title,
                "target_name": user.first_name,
                "target_message": text
            }
            extra_instructions = "Hech qanday ssilka (link) qo'shmang! 35 ta so'zdan oshmasin. Savol bilan tugating."
            draft = await target_agent.handle(text, context, extra_instructions)
            
            # Add delay before reaching out (10 to 20 minutes)
            logger.info("Human Delay boshlandi...")
            await human_delay(min_sec=600, max_sec=1200) 
            
            # Send message
            await safe_dispatch(client, user.id, draft)

def register_autonomous_handlers(app: Client):
    """Registers the autonomous handlers to the Pyrogram client."""
    # Listen to public groups (supergroups/groups)
    @app.on_message(filters.group & ~filters.me)
    async def group_handler(client, message):
        asyncio.create_task(monitor_groups_for_leads(client, message))
    
    logger.info("✅ Autonomous Outreach tayyor! Guruhlar kuzatilmoqda.")
