@echo off
chcp 65001 > nul
echo ============================================================
echo   MySQL 8.0 Xizmatini O'rnatish va Ma'lumotlar Bazasini
echo   Sozlash — Tozalash Servis
echo ============================================================

:: Adminstratorlik tekshiruvi
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [XATO] Bu faylni "Administrator sifatida ishga tushiring"!
    echo 1. Bu .bat fayl ustiga o'ng tugma bosing
    echo 2. "Run as administrator" tanlang
    pause
    exit /b 1
)

set MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin
set MYSQL_EXE="%MYSQL_BIN%\mysql.exe"
set MYSQLD_EXE="%MYSQL_BIN%\mysqld.exe"

echo.
echo [1/4] MySQL xizmati o'rnatilmoqda...
sc query MySQL80 >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] MySQL80 xizmati allaqachon mavjud.
) else (
    %MYSQLD_EXE% --install MySQL80 --defaults-file="C:\Program Files\MySQL\MySQL Server 8.0\my.ini"
    if %errorLevel% neq 0 (
        echo [XATO] MySQL xizmatini o'rnatib bo'lmadi!
        pause
        exit /b 1
    )
    echo [OK] MySQL80 xizmati o'rnatildi.
)

echo.
echo [2/4] MySQL xizmati ishga tushirilmoqda...
net start MySQL80 2>nul
if %errorLevel% neq 0 (
    sc start MySQL80 >nul 2>&1
)
timeout /t 3 /nobreak >nul

sc query MySQL80 | findstr "RUNNING" >nul
if %errorLevel% neq 0 (
    echo [XATO] MySQL ishga tushmadi! Qayta urinib ko'ring.
    pause
    exit /b 1
)
echo [OK] MySQL80 ishlayapti!

echo.
echo [3/4] Docker tozalanmoqda (portni bo'shatish uchun)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3306" ^| findstr "LISTENING"') do (
    tasklist /fi "PID eq %%a" 2>nul | findstr /i "docker" >nul
    if not errorlevel 1 (
        echo [*] Docker process %%a 3306 portini egallagan — o'ldirilmoqda...
        taskkill /f /pid %%a >nul 2>&1
    )
)

echo.
echo [4/4] Ma'lumotlar bazasi va foydalanuvchi yaratilmoqda...
echo Iltimos, MySQL root parolini kiriting (o'rnatishda belgilagan parol):
set /p ROOT_PASS="MySQL root paroli: "

%MYSQL_EXE% -u root -p%ROOT_PASS% -e "CREATE DATABASE IF NOT EXISTS tozalash_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
%MYSQL_EXE% -u root -p%ROOT_PASS% -e "CREATE USER IF NOT EXISTS 'tozalash_user'@'localhost' IDENTIFIED BY 'tozalash_password';" 2>nul
%MYSQL_EXE% -u root -p%ROOT_PASS% -e "CREATE USER IF NOT EXISTS 'tozalash_user'@'127.0.0.1' IDENTIFIED BY 'tozalash_password';" 2>nul
%MYSQL_EXE% -u root -p%ROOT_PASS% -e "GRANT ALL PRIVILEGES ON tozalash_db.* TO 'tozalash_user'@'localhost';" 2>nul
%MYSQL_EXE% -u root -p%ROOT_PASS% -e "GRANT ALL PRIVILEGES ON tozalash_db.* TO 'tozalash_user'@'127.0.0.1';" 2>nul
%MYSQL_EXE% -u root -p%ROOT_PASS% -e "FLUSH PRIVILEGES;" 2>nul

echo.
echo [TEKSHIRUV] tozalash_user ulanishi tekshirilmoqda...
%MYSQL_EXE% -u tozalash_user -ptozalash_password -h 127.0.0.1 -e "SELECT 'Ulanish muvaffaqiyatli!' AS status;" tozalash_db 2>nul
if %errorLevel% equ 0 (
    echo.
    echo ============================================================
    echo   MUVAFFAQIYAT! MySQL tayyor.
    echo   Endi start.bat ni ishga tushiring!
    echo ============================================================
) else (
    echo [OGOHLANTIRISH] Ulanish muammosi. Root parol noto'g'ri bo'lishi mumkin.
    echo Quyidagi komandani MySQL Workbench orqali bajaring:
    echo   CREATE DATABASE IF NOT EXISTS tozalash_db CHARACTER SET utf8mb4;
    echo   CREATE USER 'tozalash_user'@'%%' IDENTIFIED BY 'tozalash_password';
    echo   GRANT ALL ON tozalash_db.* TO 'tozalash_user'@'%%';
)

echo.
pause
