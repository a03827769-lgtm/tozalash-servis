import os
import shutil

base_dir = r'C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis'
desktop_dir = r'C:\Users\victus\Desktop'

manifest_content = '''{
  "manifest_version": 3,
  "name": "Gemini Cookie Sync",
  "version": "1.0",
  "description": "Avtomatik Cookie Sync",
  "permissions": [
    "cookies"
  ],
  "host_permissions": [
    "*://*.google.com/"
  ],
  "background": {
    "service_worker": "background.js"
  }
}'''

background_js_template = '''
const PROFILE_INDEX = {index}; 
const LOCAL_API_URL = "http://127.0.0.1:9090/update_cookie";

async function fetchCookies() {
    let psid = null;
    let psidts = null;
    try {
        const cookies = await chrome.cookies.getAll({ domain: ".google.com" });
        for (let c of cookies) {
            if (c.name === "__Secure-1PSID") psid = c.value;
            if (c.name === "__Secure-1PSIDTS") psidts = c.value;
        }
        if (psid || psidts) {
            await syncToServer(psid, psidts);
        }
    } catch (e) { }
}

async function syncToServer(psid, psidts) {
    try {
        await fetch(LOCAL_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_index: PROFILE_INDEX, psid: psid || "", psidts: psidts || "" })
        });
    } catch (e) { }
}
chrome.alarms.create("syncCookies", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => { if (alarm.name === "syncCookies") fetchCookies(); });
fetchCookies();
'''

# 4 ta extension yaratamiz
for i in range(1, 5):
    ext_dir = os.path.join(base_dir, f'gemini_extension_{i}')
    os.makedirs(ext_dir, exist_ok=True)
    with open(os.path.join(ext_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    with open(os.path.join(ext_dir, 'background.js'), 'w', encoding='utf-8') as f:
        f.write(background_js_template.replace('{index}', str(i)))

print('4 ta extension yaratildi!')

# Desktopda ishga tushirish skripti
bat_path = os.path.join(desktop_dir, 'Avtomat_Bot_Ishga_Tushirish.bat')
bat_content = f'''@echo off
color 0A
echo ==============================================
echo    Tozalash Servis - AI Boshqaruv Markazi
echo    (Cookie Sync va Bot)
echo ==============================================

:: Python botni alohida oynada ishga tushirish
start "Tozalash Servis Bot" cmd /c "cd /d {base_dir} && python main.py"

echo 10 soniya kutamiz (Bot to'liq ishga tushishi uchun)...
timeout /t 10 /nobreak >nul

echo Kengaytmalar ulanib Gemini brauzerlari ochilmoqda...
:: Chrome profillarini kerakli kengaytmalar bilan ochish
start chrome --profile-directory="Default" --load-extension="{base_dir}\\gemini_extension_1" "https://gemini.google.com/"
start chrome --profile-directory="Profile 1" --load-extension="{base_dir}\\gemini_extension_2" "https://gemini.google.com/"
start chrome --profile-directory="Profile 2" --load-extension="{base_dir}\\gemini_extension_3" "https://gemini.google.com/"
start chrome --profile-directory="Profile 3" --load-extension="{base_dir}\\gemini_extension_4" "https://gemini.google.com/"

echo.
echo Barcha jarayonlar ishga tushirildi!
echo Ushbu oynani yopishingiz mumkin (Bot alohida qora oynada ishlayapti).
pause
'''

with open(bat_path, 'w', encoding='utf-8') as f:
    f.write(bat_content)
print('Bat fayl yaratildi!')
