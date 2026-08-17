import fix_time
from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")

app = Client("my_account", api_id=api_id, api_hash=api_hash)

if __name__ == "__main__":
    print("Pyrogram Client started. Waiting for auth...")
    app.run()
