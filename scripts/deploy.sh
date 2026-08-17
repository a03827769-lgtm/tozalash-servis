#!/bin/bash
set -e

echo "🚀 Deploy jarayoni boshlanmoqda..."

# 1. Kodni tortib olish (agar git repo bo'lsa)
# git pull origin main

# 2. Eskirgan konteynerlarni to'xtatish
docker-compose -f docker-compose.prod.yml down

# 3. Yangi Docker image build qilish
docker-compose -f docker-compose.prod.yml build

# 4. Konteynerlarni ishga tushirish
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Deploy muvaffaqiyatli yakunlandi!"
docker-compose -f docker-compose.prod.yml ps
