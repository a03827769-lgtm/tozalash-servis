@echo off
echo ========================================================
echo   TOZALASH SERVIS - PROFESSIONAL DOCKER ISHGA TUSHIRISH
echo ========================================================
echo.

echo [1/3] Eski konteynerlarni tozalash (agar mavjud bo'lsa)...
docker-compose down

echo.
echo [2/3] Yangi Docker image'larni qurish va ishga tushirish...
docker-compose up -d --build

echo.
echo [3/3] Tizim jurnallarini kuzatish (chiqish uchun Ctrl+C bosing)...
docker-compose logs -f
