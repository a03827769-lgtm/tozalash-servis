# Original User Request

## Initial Request — 2026-08-17T09:51:15Z

Tozalash Servis (AI-powered Cleaning Automation Platform with FastAPI, Telegram Customer Bot, UserBot, Redis, PostgreSQL, and Next.js Admin Panel) loyihasini 24/7 uzluksiz, eng yuqori tezlikda va mutlaqo bepul (100% Free Forever / Tier) bulutli arxitekturaga (Koyeb / Render + Supabase PostgreSQL + Upstash Redis + Vercel Next.js) to'liq professional joylashtirish (deploy), sozlash va ishga tushirish.

Working directory: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis
Integrity mode: development

## Requirements

### R1. Cloud-Ready Backend & Telegram Bot Konteynerizatsiyasi
FastAPI API va Telegram Bot uchun maxsus ishlab chiqilgan Dockerfile va koyeb.yaml / render.yaml konfiguratsiyasini yaratish. Barcha portlar (8000, 80), health check endpointlari va asinxron fonda ishlovchi bot jarayonlarini xavfsiz boshqarish.

### R2. Bepul Cloud PostgreSQL 16 & Serverless Redis 7 Integratsiyasi
Loyiha ma'lumotlar bazasini Supabase / Neon.tech (Managed PostgreSQL 16) va Upstash Redis 7 xizmatlariga ulash. Barcha sxemalar va jadvallarni avtomatik migratsiya qilish (init_db() / Alembic).

### R3. Next.js Admin Panel & CRM ni Vercel / Cloudflare Edge'ga Joylash
admin_panel loyihasini Vercel orqali bepul joylashtirish uchun vercel.json va env konfiguratsiyasini tayyorlash. Real-time WebSocket (WSS) orqali backend bilan uzluksiz integratsiyani ta'minlash.

### R4. 24/7 Uxlab Qolishdan Himoya (Keepalive Self-Ping & Health Monitoring)
Bepul serverlarning inaktivlik sababli uxlab qolishini (sleep/idle shutdown) oldini olish uchun har 10 daqiqada /health endpointiga avtomatik keepalive ping yuboruvchi ichki va tashqi (Cron-Job.org / UptimeRobot) mexanizmni o'rnatish.

## Acceptance Criteria

### Infratuzilma va Xavfsizlik
- [ ] Barcha xizmatlar (API, Telegram Bot, PostgreSQL, Redis, Admin Panel) 100% bepul tier'larda to'liq ishlaydi.
- [ ] Backend va bot 24/7 uzluksiz faol bo'lib, uyqu rejimiga (sleep) ketmaydi.
- [ ] Telegram bot har doim onlayn, mijoz xabarlariga <500ms da javob beradi va audio/TTS keshidan foydalanadi.
- [ ] Webhooklar va API endpointlari HTTPS va WSS (Secure WebSocket) orqali himoyalangan.
- [ ] Barcha konfiguratsiya va .env fayllari loyihada to'liq tayyorlangan va avtomatik deploy qilish bo'yicha bosqichma-bosqich qo'llanma mavjud.
