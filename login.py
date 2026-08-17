import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Loyiha bazaviy yo'li
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

load_dotenv()

try:
    from pyrogram import Client
except ImportError:
    print(
        "XATO: pyrogram o'rnatilmagan! Iltimos, o'rnating: pip install pyrogram tgcrypto"
    )
    sys.exit(1)

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")

if not api_id or not api_hash:
    print("XATO: .env faylida TELEGRAM_API_ID yoki TELEGRAM_API_HASH kiritilmagan!")
    print(
        "Iltimos, my.telegram.org saytidan ma'lumotlarni oling va .env fayliga kiriting."
    )
    sys.exit(1)

app = Client("userbot", api_id=int(api_id), api_hash=api_hash, workdir=str(DATA_DIR))

print("=" * 50)
print("🔐 Telegram Shaxsiy Akkauntga Kirish")
print("=" * 50)
print(
    "Telefon raqamingiz so'ralganda halqaro formatda (masalan: +998901234567) tering."
)
print("So'ngra Telegram'dan kelgan 5 xonali kodni tering.\n")

try:
    app.start()
    me = app.get_me()
    print("\n" + "=" * 50)
    print(f"✅ Muvaffaqiyatli kirdingiz: {me.first_name} {me.last_name or ''}")
    if me.username:
        print(f"Username: @{me.username}")
    print(f"Akkaunt ID: {me.id}")
    print("=" * 50)
    print("\nSessiya fayli `data/userbot.session` da saqlandi.")
    print("Endi `python main.py` ni ishga tushirishingiz mumkin!")
    app.stop()
except Exception as e:
    print(f"\n❌ Xatolik yuz berdi: {e}")
