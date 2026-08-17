import asyncio
import os
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", 2040))
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")
PHONE = "+959767062747"
PHONE_CODE_HASH = "014edcd2c21feecd7c"
PHONE_CODE = "36824"


async def main():
    app = Client("data/userbot", api_id=API_ID, api_hash=API_HASH)
    await app.connect()
    try:
        signed_in = await app.sign_in(PHONE, PHONE_CODE_HASH, PHONE_CODE)
        print(f"SUCCESS: Signed in as {signed_in.first_name}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await app.disconnect()


asyncio.run(main())
