import os
import shutil
import tempfile
from playwright.sync_api import sync_playwright

def get_chrome_cookies():
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    if not os.path.exists(user_data_dir):
        print("Chrome User Data not found")
        return
        
    temp_dir = tempfile.mkdtemp(prefix="chrome_temp_profile")
    print(f"Copying Chrome profile to {temp_dir}...")
    
    # We need 'Local State' for the decryption key
    try:
        shutil.copy2(os.path.join(user_data_dir, "Local State"), os.path.join(temp_dir, "Local State"))
    except Exception as e:
        print("Could not copy Local State:", e)
        
    # We need the Default profile cookies
    default_dest = os.path.join(temp_dir, "Default")
    os.makedirs(os.path.join(default_dest, "Network"), exist_ok=True)
    try:
        shutil.copy2(os.path.join(user_data_dir, "Default", "Network", "Cookies"), 
                     os.path.join(default_dest, "Network", "Cookies"))
    except Exception as e:
        print("Could not copy Cookies:", e)

    print("Launching Playwright...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser.new_page()
            # Navigate to google so cookies are loaded for the domain
            page.goto("https://google.com", timeout=30000)
            
            cookies = browser.cookies("https://google.com")
            psid = None
            psidts = None
            for c in cookies:
                if c["name"] == "__Secure-1PSID":
                    psid = c["value"]
                elif c["name"] == "__Secure-1PSIDTS":
                    psidts = c["value"]
                    
            print("Found PSID:", bool(psid))
            print("Found PSIDTS:", bool(psidts))
            if psid:
                print("PSID starts with:", psid[:10])
            
            browser.close()
    except Exception as e:
        print("Playwright error:", e)
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

get_chrome_cookies()
