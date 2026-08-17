@echo off
title Tozalash Servis — Cloudflare 24/7 Tunnel
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================
echo    TOZALASH SERVIS — CLOUDFLARE 24/7 GLOBAL TUNNEL
echo ======================================================
echo [INFO] Global HTTPS tunnel ishga tushirilmoqda...
cloudflared tunnel --url http://localhost:8000
