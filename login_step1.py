import asyncio
import os
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", 2040))
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")
PHONE = "+959767062747"


async def main():
    app = Client("data/userbot", api_id=API_ID, api_hash=API_HASH)
    await app.connect()
    try:
        sent_code = await app.send_code(PHONE)
        print(f"HASH_RESULT:{sent_code.phone_code_hash}")
    except Exception as e:
        print(f"ERROR:{e}")
    finally:
        await app.disconnect()


asyncio.run(main())
