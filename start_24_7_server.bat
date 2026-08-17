@echo off
title Tozalash Servis — 24/7 Watchdog Supervisor
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================
echo    TOZALASH SERVIS — 24/7 DOIMIY ISHGA TUSHIRISH
echo ======================================================
echo [INFO] Muhit tekshirilmoqda...

:LOOP
echo [INFO] (%date% %time%) Tizim ishga tushirilmoqda...
python main.py

echo [WARNING] (%date% %time%) Server to'xtadi yoki qayta yuklandi. 3 soniyadan so'ng qayta ishga tushiriladi...
timeout /t 3 /nobreak >nul
goto LOOP
