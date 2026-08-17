# 🚀 Tozalash Servis — 24/7 Mutlaqo Bepul Bulutli Deploy Qo'llanmasi (100% Free Tier Forever)

Ushbu qo'llanma orqali butun loyihani (FastAPI Backend, Telegram Bot, PostgreSQL 16, Redis 7, va Next.js Admin Panel) **hech qanday to'lovlarsiz**, **eng tezyurar**, **24/7 uzluksiz** bulutli serverlarga joylashtirish mumkin.

---

## 🏗️ 1. Arxitektura Xaritasi (100% Bepul Xizmatlar)

| Xizmat | Tavsiya etilgan Server | Xususiyatlari | Xarajat |
| :--- | :--- | :--- | :--- |
| **Backend & Telegram Bot** | **Render.com** yoki **Koyeb.com** | 512MB RAM, Always-on, Dockerfile, Avtomatik HTTPS | **$0 / oy** (Free) |
| **Baza (PostgreSQL 16)** | **Supabase.com** yoki **Neon.tech** | 500MB DB, PgVector, Connection Pool, Avtomatik Backup | **$0 / oy** (Free) |
| **Kesh & FSM (Redis 7)** | **Upstash.com** | Serverless Redis, 10,000 buyruq/kun, Global Low-Latency | **$0 / oy** (Free) |
| **Frontend (Admin Panel)** | **Vercel.com** | Global CDN Edge, Next.js 14, Bepul SSL domen | **$0 / oy** (Free) |
| **24/7 Keepalive Pinger** | **Cron-Job.org** + `keepalive_worker.py` | Har 8 daqiqada `/health` ni chaqirib uyg'oq ushlab turadi | **$0 / oy** (Free) |

---

## 📋 2. Bosqichma-bosqich Deploy Qilish Qadamlari

### 1-qadam: PostgreSQL 16 ni Supabase'da yaratish (2 daqiqa)
1. [supabase.com](https://supabase.com) ga kiring va bepul hisob oching.
2. Yangi loyiha yarating (`tozalash-db`), parol o'rnating.
3. **Project Settings -> Database** bo'limidan `Connection String` (URI) ni nusxalang.
   *(Masalan: `postgresql://postgres:[PASSWORD]@db.xxxx.supabase.co:5432/postgres`)*

### 2-qadam: Redis 7 ni Upstash'da yaratish (1 daqiqa)
1. [upstash.com](https://upstash.com) ga kiring va bepul ro'yxatdan o'ting.
2. **Create Database** tugmasini bosing, mintaqa sifatida `Frankfurt (eu-central-1)` ni tanlang.
3. **Redis URL** qatoridagi `rediss://default:[PASSWORD]@[HOST]:6379` manzilini nusxalang.

### 3-qadam: Backend & Botni Render / Koyeb'da ishga tushirish (3 daqiqa)
1. Loyihangizni GitHub reponingizga yuklang (`git push origin main`).
2. [render.com](https://render.com) ga kiring -> **New Web Service** -> GitHub reponi tanlang.
3. **Environment Variables** bo'limiga quyidagilarni kiriting:
   - `DB_TYPE` = `postgres`
   - `DB_HOST` = Supabase host manzili
   - `DB_PORT` = `5432`
   - `DB_USERNAME` = `postgres`
   - `DB_PASSWORD` = Supabase parolingiz
   - `DB_DATABASE` = `postgres`
   - `REDIS_URL` = Upstash Redis URL manzili
   - `TELEGRAM_BOT_TOKEN` = BotFather tokeni
   - `ADMIN_TELEGRAM_ID` = Sizning Telegram ID
   - `GEMINI_API_KEY` = Google AI Studio kalitingiz
4. **Deploy Web Service** tugmasini bosing. Render avtomatik ravishda `Dockerfile` orqali tizimni yig'ib ishga tushiradi!

### 4-qadam: Admin Panelni Vercel'da ishga tushirish (1 daqiqa)
1. [vercel.com](https://vercel.com) ga kiring -> **Add New Project** -> `admin_panel` papkasini tanlang.
2. `NEXT_PUBLIC_API_URL` qiymatiga Render'dagi backend URL manzilingizni kiriting (`https://tozalash-servis-api.onrender.com/api/v1`).
3. **Deploy** tugmasini bosing.

---

## 🛡️ 3. 24/7 Doimiy Ishlash Kafolati (Keepalive Monitoring)
Loyihaga o'rnatilgan [`keepalive_worker.py`](file:///c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/keepalive_worker.py) har 8 daqiqada serveringizga o'zi signal yuboradi. Qo'shimcha ravishda [cron-job.org](https://cron-job.org) saytida bepul cron ochib, serveringizning `https://YOUR_APP.onrender.com/health` manziliga har 5 daqiqada HTTP GET so'rovi qo'yib qo'ysangiz, server hech qachon to'xtamaydi va **24/7 faol** bo'ladi!
