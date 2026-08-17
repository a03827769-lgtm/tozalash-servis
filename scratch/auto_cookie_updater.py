import os
import shutil
import tempfile
import time
from playwright.sync_api import sync_playwright
from loguru import logger

def extract_cookies_from_all_profiles():
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    if not os.path.exists(user_data_dir):
        logger.error("Chrome User Data topilmadi!")
        return []

    local_state_path = os.path.join(user_data_dir, "Local State")
    if not os.path.exists(local_state_path):
        logger.error("Local State topilmadi!")
        return []

    # Barcha profillarni topish
    profiles = []
    for item in os.listdir(user_data_dir):
        profile_path = os.path.join(user_data_dir, item)
        cookie_path = os.path.join(profile_path, "Network", "Cookies")
        if os.path.isdir(profile_path) and os.path.exists(cookie_path):
            profiles.append(item)

    logger.info(f"Topilgan Chrome profillari: {profiles}")

    valid_cookies = []

    with sync_playwright() as p:
        for profile in profiles:
            temp_dir = tempfile.mkdtemp(prefix=f"chrome_temp_{profile}_")
            try:
                # Local State nusxalash (Decryption key uchun kerak)
                shutil.copy2(local_state_path, os.path.join(temp_dir, "Local State"))
                
                # Profilni nusxalash
                dest_profile = os.path.join(temp_dir, "Default")
                os.makedirs(os.path.join(dest_profile, "Network"), exist_ok=True)
                shutil.copy2(
                    os.path.join(user_data_dir, profile, "Network", "Cookies"),
                    os.path.join(dest_profile, "Network", "Cookies")
                )

                # Playwright bilan ochish
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=temp_dir,
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = browser.new_page()
                page.goto("https://gemini.google.com", timeout=30000)
                
                # Cookielarni olish
                cookies = browser.cookies("https://google.com")
                psid = None
                psidts = None
                for c in cookies:
                    if c["name"] == "__Secure-1PSID":
                        psid = c["value"]
                    elif c["name"] == "__Secure-1PSIDTS":
                        psidts = c["value"]
                
                browser.close()

                if psid and psid.startswith("g.a"):
                    logger.success(f"✅ Profil {profile}: Cookie topildi! PSID={psid[:10]}...")
                    valid_cookies.append({"psid": psid, "psidts": psidts or ""})
                else:
                    logger.warning(f"⚠️ Profil {profile}: Cookie topilmadi (Yoki Google'ga kirmagan)")

            except Exception as e:
                logger.error(f"❌ Profil {profile} da xato: {e}")
            finally:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass

    return valid_cookies

if __name__ == "__main__":
    cookies = extract_cookies_from_all_profiles()
    print("ALL COOKIES:", cookies)
