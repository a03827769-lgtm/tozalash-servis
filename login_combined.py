import asyncio
import os
import sys
import time
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", 2040))
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ff607e10a989891a5462e627")
PHONE = "+959767062747"

sys.stdout.reconfigure(line_buffering=True)


async def main():
    app = Client("data/userbot", api_id=API_ID, api_hash=API_HASH)
    print("Connecting to Telegram...")
    await app.connect()
    try:
        sent_code = await app.send_code(PHONE)
        print(f"Code sent! Hash: {sent_code.phone_code_hash}")

        # Now wait for code.txt
        print("Waiting for code.txt to be created with the 5-digit code...")
        while not os.path.exists("code.txt"):
            await asyncio.sleep(1)

        with open("code.txt", "r") as f:
            code = f.read().strip()
        os.remove("code.txt")

        print(f"Read code: {code}. Attempting to sign in...")
        try:
            signed_in = await app.sign_in(PHONE, sent_code.phone_code_hash, code)
            print(f"SUCCESS: Signed in as {signed_in.first_name}")
        except SessionPasswordNeeded:
            print("2FA Password needed. Attempting to sign in with password...")
            signed_in = await app.check_password("12345678")
            print(f"SUCCESS: Signed in as {signed_in.first_name}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await app.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
