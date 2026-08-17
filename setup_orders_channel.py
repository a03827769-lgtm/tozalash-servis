import asyncio
import os
from pyrogram import Client
from pyrogram.types import ChatPrivileges
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def main():
    if not API_ID or not API_HASH:
        print("API_ID or API_HASH not found in .env")
        return

    import httpx

    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
        bot_info = r.json()
        if not bot_info.get("ok"):
            print("Invalid bot token")
            return
        bot_username = bot_info["result"]["username"]

    print(f"Bot username: @{bot_username}")

    app = Client("userbot", workdir="data", api_id=API_ID, api_hash=API_HASH)

    await app.start()

    print("UserBot started. Creating Orders Channel...")

    # Create Channel
    channel = await app.create_channel(
        "Tozalash Servis Buyurtmalar", "Yangi buyurtmalar uchun maxsus yopiq kanal."
    )
    channel_id = channel.id

    print(f"Channel created with ID: {channel_id}")

    # Add bot as admin
    print("Adding bot as admin...")
    await app.promote_chat_member(
        chat_id=channel_id,
        user_id=bot_username,
        privileges=ChatPrivileges(
            can_manage_chat=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_invite_users=True,
        ),
    )

    print("Bot added as admin successfully.")

    # Append to .env
    with open(".env", "a") as f:
        f.write(f"\nORDERS_CHANNEL_ID={channel_id}\n")
        f.write(f"ADMIN_USERNAME=abdulloh_ai\n")

    print("ORDERS_CHANNEL_ID and ADMIN_USERNAME saved to .env")

    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
