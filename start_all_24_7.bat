@echo off
title Tozalash Servis — 24/7 Full Stack Launcher
chcp 65001 >nul
cd /d "%~dp0"

echo ===================================================================
echo     TOZALASH SERVIS — 24/7 GLOBAL CLOUD & AI SUPERVISOR           
echo ===================================================================
echo.
echo [1/2] Backend va AI Bot orqa fonda ishga tushirilmoqda...
start /min cmd /c "start_24_7_server.bat"

echo [2/2] Cloudflare 24/7 Global HTTPS Tunnel ishga tushirilmoqda...
start /min cmd /c "start_cloudflare_tunnel.bat"

echo.
echo ===================================================================
echo  ✅ TIZIM 24/7 REJIMDA MUVAFFAQIYATLI ISHGA TUSHIRILDI!
echo  - Backend API: http://localhost:8000
echo  - REST & WebSocket: ws://localhost:8000/ws
echo  - Health Check: http://localhost:8000/health
echo  - Telegram Bot: 24/7 Onlayn
echo  - Cloudflare Tunnel: Global Anycast CDN Edge orqali ulandi
echo ===================================================================
echo.
echo To'xtatish uchun stop_24_7_server.bat faylini ishga tushiring.
timeout /t 5 >nul
