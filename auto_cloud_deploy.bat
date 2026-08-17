@echo off
chcp 65001 >nul
title TOZALASH SERVIS — AVTOMATIK BULUTGA (24/7 SERVERGA) YUKLASH
color 0b

echo ==============================================================================
echo        TOZALASH SERVIS — 24/7 BULUTLI SERVERGA AVTOMATIK YUKLOVCHI
echo ==============================================================================
echo.
echo Ushbu dastur loyihani 100%% Bepul Bulutli Serverga (Render / Koyeb) yuklaydi.
echo Noutbukingiz o'chiq turganda ham server 24/7/365 uzluksiz ishlaydi!
echo.
echo ------------------------------------------------------------------------------
echo [1/3] GitHub hisobiga ulanish tekshirilmoqda...
echo ------------------------------------------------------------------------------

"C:\Users\victus\gh-cli\bin\gh.exe" auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] GitHub akkauntingiz bilan brauzer orqali avtorizatsiya qilinmoqda...
    echo [!] Bir martalik tasdiqlash kodi buferga (clipboard) avtomatik ko'chiriladi.
    echo.
    "C:\Users\victus\gh-cli\bin\gh.exe" auth login --web --clipboard -p https -h github.com
) else (
    echo [OK] GitHub hisobi ulangan!
)

echo.
echo ------------------------------------------------------------------------------
echo [2/3] GitHub'da 'tozalash-servis' repozitoriysi yaratilmoqda va kod yuklanmoqda...
echo ------------------------------------------------------------------------------

git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    "C:\Users\victus\gh-cli\bin\gh.exe" repo create tozalash-servis --public --source=. --push
) else (
    git add .
    git commit -m "feat: complete 24/7 cloud configuration with docker and keepalive" >nul 2>&1
    git push -u origin main
)

echo.
echo ------------------------------------------------------------------------------
echo [3/3] 24/7 Bepul Server (Render / Koyeb) boshqaruv paneli ochilmoqda...
echo ------------------------------------------------------------------------------
echo.
echo [OK] Loyiha GitHub'ga to'liq yuklandi!
echo [OK] Endi brauzeringizda Render.com ochiladi.
echo [OK] Faqat 'Connect' tugmasini bosing — Render 'render.yaml' va Dockerfile orqali
echo      barcha bot, API va xizmatlarni 24/7 bepul yoqib beradi!
echo.

start https://dashboard.render.com/select-repo?type=web
start https://app.koyeb.com/services/deploy

echo ==============================================================================
echo [SUCCESS] BARCHA BOSQICHLAR TAYYOR!
echo ==============================================================================
pause
