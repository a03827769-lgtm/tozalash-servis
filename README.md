# 🧹 Tozalash Servis – AI Avtomatizatsiya Tizimi

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18.0-61dafb.svg" alt="React">
  <img src="https://img.shields.io/badge/Expo-51.0-black.svg" alt="Expo">
  <img src="https://img.shields.io/badge/Docker-Enabled-blue.svg" alt="Docker">
</div>

---

**Tozalash Servis** – bu O'zbekistondagi tozalash va klyning xizmatlari uchun yaratilgan mutlaqo innovatsion, AI (sun'iy intellekt) ga asoslangan boshqaruv va avtomatizatsiya platformasi.

Tizim nafaqat buyurtmalarni boshqaradi, balki telegram bot orqali mijozlar bilan muloqot qiladi, SMM postlar yozadi, to'lovlarni qabul qiladi, xodimlarning samaradorligini tahlil qiladi va kelajakdagi buyurtmalarni bashorat qiladi.

---

## 🌟 Asosiy Imkoniyatlar (Features)

1. **AI Telegram Bot (G4F / Gemini):** Mijozlar bilan insondek suhbatlashadigan va buyurtma oladigan sun'iy intellekt.
2. **Telegram Mini App (WebApp):** Glassmorphism dizaynida yozilgan interaktiv va juda qulay UI (React + Vite).
3. **Ishchilar uchun Mobil Ilova:** React Native (Expo) orqali yozilgan, ishchilar buyurtma statusini o'zgartiradigan portal.
4. **To'lov Tizimlari:** Payme va Click integratsiyasi orqali to'lovlarni avtomatik qabul qilish.
5. **Monitoring (Grafana + Prometheus):** Tizim resurslari va API holatini real vaqtda kuzatish imkoniyati.
6. **AI Content Manager:** Kanal uchun SMM postlar generatsiyasi (Kuniga 4 ta).
7. **Predictive Analytics:** Kelajakdagi xizmatlarga bo'lgan talabni bashorat qiluvchi AI model.

---

## 🛠 Texnologiyalar Steki

- **Backend:** FastAPI, Python, aiomysql, Sentry
- **Frontend (WebApp):** React, Vite, TypeScript, Telegram WebApp SDK, Vanilla CSS (Premium Glassmorphism)
- **Mobile (Worker App):** React Native, Expo, TypeScript
- **Database:** MySQL, Redis
- **Monitoring:** Prometheus, Grafana
- **AI Models:** Google Gemini 1.5 Pro, G4F (Fallback), HuggingFace Transformers

---

## 🚀 Ishga Tushirish (Docker yordamida)

Loyihani serverga deploy qilish yoki lokal kompyuterda ishga tushirish uchun Docker'dan foydalanish eng to'g'ri va barqaror yo'ldir.

### 1-qadam: Repozitoriyni yuklab olish
```bash
git clone https://github.com/yourusername/tozalash_servis.git
cd tozalash_servis
```

### 2-qadam: Muhit o'zgaruvchilarini (.env) sozlash
```bash
cp .env.example .env
```
`.env` faylini matn muharririda oching va quyidagi muhim qatorlarni to'ldiring:
- `TELEGRAM_BOT_TOKEN` - BotFather'dan olingan token
- `GEMINI_API_KEY` - Google AI Studio'dan olingan API kalit
- `ADMIN_TELEGRAM_ID` - Sizning shaxsiy telegram ID'ingiz
- `PAYME_KEY` va `CLICK_SECRET` - To'lov tizimlari kalitlari

### 3-qadam: Docker Compose orqali ishga tushirish
```bash
docker-compose up -d --build
```

Bu buyruq barcha xizmatlarni (MySQL, Redis, FastAPI Backend, React WebApp, Prometheus, Grafana) alohida konteynerlarda parallel ravishda ko'taradi.

---

## 🔗 Xizmatlar manzillari (Ports & Endpoints)

| Xizmat | Manzil / Port |
|---------|---------------|
| **FastAPI Backend** | `http://localhost:8000` |
| **Swagger API Docs** | `http://localhost:8000/docs` |
| **Telegram WebApp** | `http://localhost:8080` |
| **Grafana Dashboard** | `http://localhost:3001` (Login: `admin` / `admin`) |
| **Prometheus** | `http://localhost:9090` |
| **MySQL Database** | `localhost:3306` |
| **Redis** | `localhost:6379` |

---

## 📱 Mobil Ilovani Ishga Tushirish

Mobil ilova (Ishchilar uchun MVP) `mobile_app` papkasida joylashgan.
Uni kompyuterda sinab ko'rish uchun `Node.js` o'rnatilgan bo'lishi kerak.

```bash
cd mobile_app
npm install
npx expo start
```
Telefoningizdagi **Expo Go** ilovasi orqali QR kodni skanerlang va ilovani jonli test qiling.

---

## 🧪 Avtomatik Testlar (Unit & Integration)

Kodning barqarorligini tekshirish uchun Pytest orqali 70% dan ortiq kod qoplanishi (coverage) ta'minlangan.
Lokal muhitda testlarni yurgizish:
```bash
pytest tests/ -v
```
Kod qamrovini (Coverage) ko'rish uchun:
```bash
pytest --cov=app --cov=ai_brain tests/
```

---

## 👨‍💻 Loyiha Muallifi
Ushbu innovatsion tizim **Kubboy AI** (Sun'iy Intelekt va Tizim Arxitektori) hamda foydalanuvchi bilan hamkorlikda yaratildi. Maksimal sifat va muhandislik yechimlari qo'llanildi.

*Tozalash Servis – Tozalik kelajagi endi aqlli!*
