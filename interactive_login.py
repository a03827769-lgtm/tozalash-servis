import asyncio
import os
import sys
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", 2040))
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")

# Pyrogram has its own print outputs which are buffered.
# Force unbuffered output for the whole script:
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


async def main():
    app = Client("data/userbot", api_id=API_ID, api_hash=API_HASH)
    print("Starting pyrogram interactive login...")
    await app.start()
    print("SUCCESS: Session created!")
    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
