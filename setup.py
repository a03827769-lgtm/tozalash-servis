#!/usr/bin/env python3
"""
Tozalash Servis — O'rnatish va Sozlash Skripti
Bir marta ishga tushirib, hamma narsani avtomatik sozlaydi
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def print_banner():
    print("""
╔════════════════════════════════════════════════════╗
║   🧹 TOZALASH SERVIS — O'RNATISH DASTURI          ║
║       Barcha narsani avtomatik sozlaydi!           ║
╚════════════════════════════════════════════════════╝
    """)


def check_python():
    """Python versiyasini tekshirish"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ kerak. Sizda: {sys.version}")
        print("   Yuklab oling: https://python.org/downloads")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_requirements():
    """Kutubxonalarni o'rnatish"""
    print("\n📦 Kutubxonalar o'rnatilmoqda...")
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt",
                "--quiet",
                "--no-warn-script-location",
            ],
            check=True,
        )
        print("✅ Barcha kutubxonalar o'rnatildi!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ O'rnatish xatosi: {e}")
        return False


def setup_env():
    """Konfiguratsiya faylini sozlash"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        print("\n✅ .env fayli mavjud")
        return True

    if env_example.exists():
        import shutil

        shutil.copy(env_example, env_file)
        print("\n📝 .env fayli yaratildi!")

    print("\n" + "=" * 60)
    print("MUHIM: Quyidagi ma'lumotlarni kiriting:")
    print("=" * 60)

    config = {}

    # Telegram Bot Token
    print("\n1. TELEGRAM BOT TOKEN")
    print("   - @BotFather ga boring")
    print("   - /newbot yozing")
    print("   - Bot nomini bering")
    print("   - Token olasiz (masalan: 123456789:ABCdef...)")
    config["TELEGRAM_BOT_TOKEN"] = input("\n   Token kiriting: ").strip()

    # Admin Telegram ID
    print("\n2. SIZNING TELEGRAM ID INGIZ")
    print("   - @userinfobot ga yozing")
    print("   - 'Id:' qatoridagi raqamni oling")
    config["ADMIN_TELEGRAM_ID"] = input("\n   Telegram ID: ").strip()

    # Gemini API Key
    print("\n3. GEMINI API KEY (BEPUL)")
    print("   - https://aistudio.google.com/app/apikey")
    print("   - 'Create API key' tugmasini bosing")
    config["GEMINI_API_KEY"] = input("\n   API Key: ").strip()

    # Telegram Channel
    print("\n4. TELEGRAM KANAL USERNAME")
    print("   - Kanalingiz username'i (@belgisisiz)")
    print("   - Masalan: tozalash_servis_kanal")
    config["TELEGRAM_CHANNEL"] = input("\n   Kanal username: ").strip()

    # Biznes telefoni
    print("\n5. BIZNES TELEFON RAQAM")
    config["BUSINESS_PHONE"] = input("\n   Telefon (+998...): ").strip()

    # .env faylini yangilash
    update_env_file(config)

    print("\n✅ Konfiguratsiya saqlandi!")
    return True


def update_env_file(config: dict):
    """ENV faylini yangilash"""
    env_path = Path(".env")

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        with open(".env.example", "r", encoding="utf-8") as f:
            content = f.read()

    for key, value in config.items():
        if value:
            # Mavjud qiymatni almashtirish
            import re

            pattern = rf"^{key}=.*$"
            replacement = f"{key}={value}"

            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                content += f"\n{replacement}"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)


def setup_database():
    """Ma'lumotlar bazasini sozlash"""
    print("\n🗄️ Ma'lumotlar bazasi sozlanmoqda...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from database import db

        print("✅ Ma'lumotlar bazasi tayyor!")
        return True
    except Exception as e:
        print(f"❌ Baza xatosi: {e}")
        return False


def add_workers_interactive():
    """Ishchilarni qo'shish"""
    print("\n👷 ISHCHILAR QO'SHISH")
    print("(Hozir o'tkazib yuborsa bo'ladi, keyinroq qo'shish mumkin)")

    add_now = input("\nHozir ishchilarni qo'shmoqchimisiz? (ha/yo'q): ").strip().lower()

    if add_now in ["ha", "h", "yes", "y"]:
        count = int(input("Nechta ishchi: ").strip() or "0")

        if count > 0:
            try:
                from database import db

                for i in range(1, count + 1):
                    print(f"\nIshchi #{i}:")
                    name = input("  Ismi familiyasi: ").strip()
                    phone = input("  Telefon raqami: ").strip()
                    telegram_id = input("  Telegram ID (@userinfobot dan): ").strip()

                    if name:
                        db.add_worker(name=name, phone=phone, telegram_id=telegram_id)
                        print(f"  ✅ {name} qo'shildi")

            except Exception as e:
                print(f"❌ Ishchi qo'shish xatosi: {e}")


def create_google_sheets_instructions():
    """Google Sheets ko'rsatmalari"""
    print("\n📊 GOOGLE SHEETS CRM SOZLASH")
    print("-" * 40)
    print("""
Google Sheets CRM ni sozlash uchun:

1. https://sheets.google.com ga boring
2. Yangi jadval yarating (+ tugmasi)
3. Jadval nomini bering: "Tozalash Servis CRM"
4. URL dan ID ni oling:
   https://docs.google.com/spreadsheets/d/[ID_SHU_YERDA]/edit
5. .env faylida: GOOGLE_SHEETS_ID=[ID_ni_qo'ying]

Service Account uchun:
1. https://console.cloud.google.com ga boring
2. Yangi project yarating
3. Google Sheets API + Google Drive API ni yoqing
4. Service Account yarating
5. JSON kalitini yuklab oling
6. data/google_credentials.json ga joylashtiring
    """)

    input("Tushundim! (Enter bosing)")


def show_next_steps():
    """Keyingi qadamlar"""
    print("""
╔════════════════════════════════════════════════════╗
║              ✅ O'RNATISH TUGADI!                  ║
╚════════════════════════════════════════════════════╝

🚀 TIZIMNI ISHGA TUSHIRISH:

Windows:
  start.bat faylini ikki marta bosing

yoki:
  python main.py

═══════════════════════════════════════════════════

📋 KEYINGI QADAMLAR:

1. ✅ Telegram botingizni @BotFather da yarating
2. ✅ Gemini API Key oling (bepul)
3. ✅ Bot ni kanalingizga admin qiling
4. ✅ .env faylini to'ldiring
5. 🔄 Ishchilarni qo'shing (admin panel orqali)
6. 📊 Google Sheets CRM ni ulang (ixtiyoriy)
7. 📱 Instagram API ni ulang (ixtiyoriy)

═══════════════════════════════════════════════════

💬 BUYURTMA OLISH TESTI:
  Botingizga /start yozing va buyurtma bering!

═══════════════════════════════════════════════════
    """)


def main():
    """Asosiy o'rnatish jarayoni"""
    print_banner()

    steps = [
        ("Python tekshirish", check_python),
        ("Kutubxonalar o'rnatish", install_requirements),
        ("Konfiguratsiya sozlash", setup_env),
        ("Ma'lumotlar bazasi", setup_database),
    ]

    for step_name, step_func in steps:
        print(f"\n{'='*50}")
        print(f"⚙️  {step_name}...")
        print("=" * 50)

        result = step_func()
        if not result:
            print(f"\n❌ '{step_name}' bosqichida xato!")
            break

    # Qo'shimcha sozlamalar
    create_google_sheets_instructions()
    add_workers_interactive()
    show_next_steps()


if __name__ == "__main__":
    main()
