@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Tozalash Servis - AI Avtomatizatsiya Tizimi (FAST START)
color 0B

echo.
echo ============================================================
echo    TOZALASH SERVIS - AI AVTOMATIZATSIYA TIZIMI (FAST START)
echo    Powered by Google Gemini AI
echo ============================================================
echo.

cd /d "%~dp0"

if not exist "new_venv\Scripts\python.exe" (
    echo [XATO] Virtual muhit (new_venv) topilmadi!
    pause
    exit /b 1
)

echo [*] Kerakli kutubxonalar yuklanmoqda...
call new_venv\Scripts\python.exe -m pip install aiosqlite >nul 2>&1
call new_venv\Scripts\python.exe -m pip install loguru >nul 2>&1

echo [*] MySQL talab qilinmaydi (SQLite tizimi faol).
echo [*] AI tizimi ishga tushirilmoqda...
echo [*] To'xtatish uchun: Ctrl+C
echo.

call new_venv\Scripts\python.exe main.py

echo.
echo ============================================================
echo    Tizim to'xtatildi. Qayta ishga tushirish uchun
echo    bu faylni qayta oching.
echo ============================================================
pause
