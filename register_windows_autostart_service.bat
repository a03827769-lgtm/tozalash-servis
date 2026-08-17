@echo off
title Tozalash Servis — 24/7 Avtomatik Windows Xizmatini O'rnatish
chcp 65001 >nul
cd /d "%~dp0"

echo ===================================================================
echo   TOZALASH SERVIS — WINDOWS 24/7 AVTO-START XIZMATINI O'RNATISH   
echo ===================================================================
echo.

set TASK_NAME=TozalashServis247
set SCRIPT_PATH=%~dp0start_24_7_silent.vbs

echo [INFO] Windows Task Scheduler'da doimiy vazifa ro'yxatdan o'tkazilmoqda...
schtasks /create /tn "%TASK_NAME%" /tr "wscript.exe \"%SCRIPT_PATH%\"" /sc onlogon /rl highest /f

if %ERRORLEVEL% equ 0 (
    echo.
    echo ===================================================================
    echo  ✅ 24/7 AVTOMATIK XIZMAT MUVAFFAQIYATLI O'RNATILDI!
    echo  - Kompyuter har safar yoqilganda tizim avtomatik fonda ishga tushadi.
    echo  - Hech qanday oyna ochilmaydi (Silent Background Mode).
    echo ===================================================================
) else (
    echo [WARNING] Administrator ruxsati kerak bo'lishi mumkin.
)

pause
