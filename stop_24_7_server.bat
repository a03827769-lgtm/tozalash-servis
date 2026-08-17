@echo off
title Tozalash Servis — To'xtatish
chcp 65001 >nul
echo [INFO] Tozalash Servis jarayonlari to'xtatilmoqda...

taskkill /F /FI "WINDOWTITLE eq Tozalash Servis — 24/7 Watchdog Supervisor*" /T >nul 2>&1
taskkill /F /IM cloudflared.exe >nul 2>&1

echo [SUCCESS] Barcha xizmatlar xavfsiz to'xtatildi.
pause
