"""
Tozalash Servis — Tizim Test Skripti
O'rnatish to'g'ri bo'lishini tekshirish uchun
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("🧪 Tozalash Servis — Tizim Testi\n")
print("=" * 50)

errors = []
warnings = []

# ================================================
# 1. Python versiyasi
# ================================================
print("1. Python versiyasi...", end=" ")
version = sys.version_info
if version.major >= 3 and version.minor >= 9:
    print(f"✅ {version.major}.{version.minor}.{version.micro}")
else:
    print(f"❌ {version.major}.{version.minor} (3.9+ kerak!)")
    errors.append("Python 3.9+ kerak")

# ================================================
# 2. .env fayli
# ================================================
print("2. .env fayli...", end=" ")
if Path(".env").exists():
    print("✅ Mavjud")
else:
    print("❌ Topilmadi!")
    errors.append(".env fayli yo'q — 'copy .env.example .env' bajaring")

# ================================================
# 3. Konfiguratsiya
# ================================================
print("3. Konfiguratsiya...", end=" ")
try:
    from config import TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, ADMIN_TELEGRAM_ID

    config_ok = True
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_bot_token_here":
        print("❌ TELEGRAM_BOT_TOKEN o'rnatilmagan!")
        errors.append("TELEGRAM_BOT_TOKEN yo'q")
        config_ok = False
    elif not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("❌ GEMINI_API_KEY o'rnatilmagan!")
        errors.append("GEMINI_API_KEY yo'q")
        config_ok = False
    elif not ADMIN_TELEGRAM_ID or ADMIN_TELEGRAM_ID == 0:
        print("⚠️ ADMIN_TELEGRAM_ID o'rnatilmagan")
        warnings.append("ADMIN_TELEGRAM_ID yo'q (hisobotlar yuborilmaydi)")
        print("✅ (ADMIN ID siz)")
    else:
        print("✅ Barcha asosiy tokenlar mavjud")
except Exception as e:
    print(f"❌ Xato: {e}")
    errors.append(f"Konfiguratsiya xatosi: {e}")

# ================================================
# 4. Kutubxonalar
# ================================================
print("4. Kutubxonalar...", end=" ")
required_packages = [
    ("telegram", "python-telegram-bot"),
    ("google.generativeai", "google-generativeai"),
    ("loguru", "loguru"),
    ("dotenv", "python-dotenv"),
    ("httpx", "httpx"),
    ("apscheduler", "APScheduler"),
]

missing = []
for import_name, package_name in required_packages:
    try:
        __import__(import_name)
    except ImportError:
        missing.append(package_name)

if missing:
    print(f"❌ O'rnatilmagan: {', '.join(missing)}")
    errors.append(f"Kutubxonalar: pip install {' '.join(missing)}")
else:
    print("✅ Barcha kutubxonalar mavjud")

# ================================================
# 5. Ma'lumotlar bazasi
# ================================================
print("5. Ma'lumotlar bazasi...", end=" ")
try:
    from database import db

    print("✅ SQLite baza tayyor")
except Exception as e:
    print(f"❌ Xato: {e}")
    errors.append(f"Baza xatosi: {e}")

# ================================================
# 6. AI Miya (Gemini)
# ================================================
print("6. AI Miya (Gemini)...", end=" ")
try:
    from config import GEMINI_API_KEY, GEMINI_FLASH_MODEL

    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_FLASH_MODEL)
        response = model.generate_content("Salom! Faqat 'Ishlayapman!' deb javob ber.")
        print(f"✅ Gemini AI ishlayapti!")
    else:
        print("⚠️ API Key yo'q (test o'tkazilmadi)")
        warnings.append("Gemini API Key o'rnatilmagan")
except Exception as e:
    print(f"❌ Gemini test xatosi: {e}")
    warnings.append(f"Gemini: {str(e)[:50]}")

# ================================================
# 7. Telegram Bot
# ================================================
print("7. Telegram Bot...", end=" ")
try:
    from config import TELEGRAM_BOT_TOKEN

    if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "your_bot_token_here":
        import httpx

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = httpx.get(url, timeout=10)
        data = response.json()

        if data.get("ok"):
            bot_name = data["result"]["first_name"]
            bot_username = data["result"]["username"]
            print(f"✅ Bot: {bot_name} (@{bot_username})")
        else:
            print(f"\u274c Bot xatosi: {data.get('description', 'Nomalum')}")
            errors.append("Telegram Bot Token noto'g'ri")
    else:
        print("⚠️ Token o'rnatilmagan")
except Exception as e:
    print(f"❌ Telegram test xatosi: {e}")
    warnings.append(f"Telegram: {str(e)[:50]}")

# ================================================
# 8. Google Sheets (ixtiyoriy)
# ================================================
print("8. Google Sheets CRM...", end=" ")
try:
    from config import GOOGLE_SHEETS_ID, GOOGLE_CREDENTIALS_FILE

    if (
        GOOGLE_SHEETS_ID
        and GOOGLE_SHEETS_ID != "your_google_sheets_id_here"
        and Path(GOOGLE_CREDENTIALS_FILE).exists()
    ):
        print("✅ Sozlangan")
    else:
        print("⚠️ Sozlanmagan (ixtiyoriy — SQLite ishlatiladi)")
except Exception as e:
    print(f"⚠️ Tekshirib bo'lmadi")

# ================================================
# 9. Instagram (ixtiyoriy)
# ================================================
print("9. Instagram API...", end=" ")
try:
    from config import INSTAGRAM_ACCESS_TOKEN

    if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCESS_TOKEN != "your_instagram_token_here":
        print("✅ Token mavjud")
    else:
        print("⚠️ Sozlanmagan (ixtiyoriy)")
except Exception as e:
    print(f"⚠️ Tekshirib bo'lmadi")

# ================================================
# NATIJA
# ================================================
print("\n" + "=" * 50)

if errors:
    print(f"\n❌ {len(errors)} ta xato topildi:")
    for i, err in enumerate(errors, 1):
        print(f"   {i}. {err}")
    print("\n📋 Bu xatolarni tuzating va qayta test qiling.")
elif warnings:
    print(f"\n⚠️ {len(warnings)} ta ogohlantirish:")
    for w in warnings:
        print(f"   • {w}")
    print("\n✅ Asosiy tizim tayyor! 'python main.py' bilan ishga tushiring.")
else:
    print("\n🎉 BARCHA TESTLAR MUVAFFAQIYATLI!")
    print("✅ Tizim to'liq sozlangan va ishga tayyor!")
    print("\n🚀 Ishga tushirish:")
    print("   python main.py")
    print("   yoki: start.bat (Windows)")

print("=" * 50)
