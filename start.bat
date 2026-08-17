@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Tozalash Servis - AI Avtomatizatsiya Tizimi
color 0A

echo.
echo ============================================================
echo    TOZALASH SERVIS - AI AVTOMATIZATSIYA TIZIMI
echo    Powered by Google Gemini AI
echo ============================================================
echo.

:: Loyiha papkasiga o'tish
cd /d "%~dp0"

:: .env faylini tekshirish
if not exist ".env" (
    echo [XATO] .env fayli topilmadi!
    copy ".env.example" ".env" 2>nul
    notepad .env
    pause
    exit /b 1
)

:: Python tekshirish
python --version >nul 2>&1
if errorlevel 1 (
    echo [XATO] Python topilmadi!
    pause
    exit /b 1
)

:: Kutubxonalar
echo [*] Tizimdagi kutubxonalardan foydalaniladi (System Python)

:: ============================================================
:: MySQL Native (Docker kerak emas!)
:: ============================================================
echo.
echo [*] MySQL tekshirilmoqda...

:: Port 3306 da biror narsa tinglayotganmi?
netstat -ano | findstr ":3306.*LISTENING" >nul 2>&1
if %errorLevel% equ 0 (
    :: 3306 band — haqiqiy MySQL mi yoki Docker mi?
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3306.*LISTENING"') do (
        set PROC_PID=%%p
    )
    tasklist /fi "PID eq %PROC_PID%" 2>nul | findstr /i "docker\|com.docker" >nul
    if not errorlevel 1 (
        echo [!] Docker 3306 portini egallagan — o'ldirilmoqda...
        taskkill /f /pid %PROC_PID% >nul 2>&1
        taskkill /f /im "com.docker.backend.exe" /t >nul 2>&1
        taskkill /f /im "wslrelay.exe" /t >nul 2>&1
        timeout /t 2 /nobreak >nul
        goto :start_mysql
    ) else (
        echo [OK] MySQL (yoki boshqa DB) 3306 portida ishlayapti.
        goto :start_bot
    )
) else (
    goto :start_mysql
)

:start_mysql
echo [*] MySQL 8.0 ishga tushirilmoqda...
start /b "" "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini"

:: MySQL tayyor bo'lguncha kutish (max 15 soniya)
set /a COUNTER=0
:wait_mysql
timeout /t 1 /nobreak >nul
netstat -ano | findstr ":3306.*LISTENING" >nul 2>&1
if %errorLevel% equ 0 goto :mysql_ready
set /a COUNTER=%COUNTER%+1
if %COUNTER% lss 15 goto :wait_mysql
echo [XATO] MySQL 15 soniyada ishga tushmadi!
echo setup_mysql.bat ni administrator sifatida ishga tushiring.
pause
exit /b 1

:mysql_ready
echo [OK] MySQL 3306 portida tayyor!

:start_bot
echo.
echo [*] AI tizimi ishga tushirilmoqda...
echo [*] To'xtatish uchun: Ctrl+C
echo.

python main.py

echo.
echo ============================================================
echo    Tizim to'xtatildi. Qayta ishga tushirish uchun
echo    bu faylni qayta oching.
echo ============================================================
pause
