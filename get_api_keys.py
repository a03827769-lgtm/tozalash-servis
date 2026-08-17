"""
Tozalash Servis — API Kalitlari Olish Qo'llanmasi
Har bir API ni qanday olishni bosqichma-bosqich tushuntiradi
"""

API_GUIDE = """
╔══════════════════════════════════════════════════════════╗
║    TOZALASH SERVIS — API KALITLARI OLISH QO'LLANMASI    ║
╚══════════════════════════════════════════════════════════╝

Bu skript sizga barcha kerakli API kalitlarini qanday olishni
bosqichma-bosqich ko'rsatadi.

Bosing Enter va ko'rsatmalarga amal qiling...
"""


def guide_telegram_bot():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 1-QISM: TELEGRAM BOT TOKEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Qadamlar:
  1. Telegram'ni oching
  2. Qidiruvga "@BotFather" yozing va boring
  3. /start yozing (agar birinchi marta bo'lsa)
  4. /newbot yozing
  5. Bot nomini kiriting: "Tozalash Servis"
  6. Bot username kiriting: "tozalash_servis_bot" 
     (yagona bo'lishi kerak — "bot" bilan tugashi shart)
  7. Token olasiz, masalan:
     1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi

Token'ni nusxalab oling va .env faylida:
  TELEGRAM_BOT_TOKEN=1234567890:ABCDEF...

⚠️ Token'ni hech kimga bermang!

Bot kanalni boshqarishi uchun:
  1. Telegram kanalingizni oching
  2. Channel Info → Administrators → Add Administrator
  3. Botingizni qo'shing (username bilan izlang)
  4. Barcha ruxsatlarni bering
""")
    input("  → Telegram Bot Token oldingizmi? Enter bosing:")


def guide_gemini_api():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 2-QISM: GEMINI API KEY (BEPUL!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Google AI Studio (BEPUL, karta kerak emas!):

  1. Brauzerda oching:
     https://aistudio.google.com/app/apikey
  
  2. Google akkauntingiz bilan kiring
     (5ta Google Pro akkauntingizdan birini ishlating)
  
  3. "Create API key" tugmasini bosing
  
  4. "Create API key in new project" tanlang
  
  5. Key nusxalab oling, masalan:
     AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  
  6. .env faylida:
     GEMINI_API_KEY=AIzaSyB...

BEPUL LIMIT:
  • 15 so'rov/daqiqa
  • 1,500 so'rov/kun
  • Bu bizning bot uchun yetarli!
""")
    input("  → Gemini API Key oldingizmi? Enter bosing:")


def guide_admin_id():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 3-QISM: SIZNING TELEGRAM ID INGIZ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Telegram'da @userinfobot ga /start yozing
  
  2. Javobda "Id:" qatorini toping:
     Your user ID: 987654321
  
  3. .env faylida:
     ADMIN_TELEGRAM_ID=987654321

Bu ID sizga:
  ✅ Kunlik hisobotlar yuboriladi
  ✅ Yangi buyurtmalar haqida xabar keladi
  ✅ Admin komandalar ishlaydi
""")
    input("  → Telegram ID oldingizmi? Enter bosing:")


def guide_telegram_channel():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📢 4-QISM: TELEGRAM KANAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Agar kanal yo'q bo'lsa, yaratish:
  1. Telegram → "yangi kanal yaratish"
  2. Kanal nomini bering: "Tozalash Servis"
  3. Tavsif qo'shing
  4. Public qiling va username bering:
     Masalan: tozalash_servis_tashkent

Bot'ni kanalga admin qilish:
  1. Kanal → Info → Administrators → Add
  2. Botingiz username'ini kiriting
  3. Barcha ruxsatlarni bering ✅

.env faylida (@ belgisisiz):
  TELEGRAM_CHANNEL=tozalash_servis_tashkent
""")
    input("  → Kanal tayyor? Enter bosing:")


def guide_instagram():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 5-QISM: INSTAGRAM API (IXTIYORIY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Instagram API o'rnatish murakkabroq. Agar hozir kerak bo'lmasa
Enter bosib o'tkazib yuboring.

Qadamlar:
  1. https://developers.facebook.com ga boring
  2. "My Apps" → Create App
  3. "Business" turini tanlang
  4. Instagram Basic Display API qo'shing
  5. Token oling

Bu keyinroq ham qo'shilishi mumkin.
Instagram DM'larga manual javob bering ayni paytda.
""")
    input("  → Tushundim, Enter bosing:")


def guide_google_sheets():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 6-QISM: GOOGLE SHEETS CRM (IXTIYORIY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Agar Google Sheets kerak bo'lmasa, tizim SQLite ishlatadi.
Bot baribir ishlaydi. Sheets keyinroq ulanishi mumkin.

Agar ulashni istasangiz:

  1. Yangi Sheets yarating: https://sheets.new
  2. URL dan ID oling
  3. Google Cloud Console:
     https://console.cloud.google.com
  4. Yangi project → Sheets API + Drive API yoqing
  5. Service Account → JSON key yuklab oling
  6. Key faylini: data/google_credentials.json ga joylashtiring
  7. .env da:
     GOOGLE_SHEETS_ID=1BxiMVs0XRA5...

Keyinroq ham sozlanishi mumkin!
""")
    input("  → Tushundim, Enter bosing:")


def final_steps():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 BARCHA TAYYORLANISH TUGADI!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Endi qilish kerak:

  1. .env faylini to'ldiring:
     notepad .env

  2. Tizimni test qiling:
     python test_system.py

  3. Ishga tushiring:
     python main.py
     yoki: start.bat

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MUVAFFAQIYAT! 🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


def main():
    print(API_GUIDE)
    input("Boshlash uchun Enter bosing...")

    guide_telegram_bot()
    guide_gemini_api()
    guide_admin_id()
    guide_telegram_channel()
    guide_instagram()
    guide_google_sheets()
    final_steps()


if __name__ == "__main__":
    main()
