# Project: Tozalash Servis Cloud Deployment

## Architecture
Tozalash Servis is an AI-powered enterprise cleaning automation platform designed for 24/7 continuous operation on 100% Free Forever cloud infrastructure.

### Component Topology
1. **Unified Backend Web Service (Render / Koyeb Free Nano)**:
   - Single-container multi-tasking async Python 3.11 runtime on `python:3.11-slim-bookworm`.
   - Programmatic Uvicorn ASGI server hosting FastAPI on `0.0.0.0:$PORT` (REST API `/api/v1/*`, GraphQL `/graphql`, WebSocket `/ws`, Healthcheck `/health`).
   - Concurrently scheduled Telegram Customer Bot (`python-telegram-bot` v20.7 polling), Pyrogram UserBot, APScheduler, and Keepalive Worker in a shared non-blocking event loop.
2. **Managed Cloud Database (Supabase / Neon PostgreSQL 16)**:
   - Managed PostgreSQL 16 via `asyncpg` with SSL (`sslmode=require`), transaction pooler support (port 6543, `statement_cache_size=0`), and automated schema migration / initialization (`init_db()`).
   - Resilient zero-config fallback to `aiosqlite` in WAL mode for local offline development.
3. **Serverless Cloud Cache & State (Upstash Redis 7)**:
   - Serverless Redis 7 via TLS (`rediss://...`) with connection keepalive (`health_check_interval=30`, `retry_on_timeout=True`), FSM state management, Redlock distributed locking, Pub/Sub room broadcasting, and non-blocking in-memory fallback.
4. **Edge Admin Panel & CRM (Vercel / Cloudflare Edge)**:
   - Next.js 16.3.0 + React 19.2.8 + Tailwind CSS v4 frontend built as static CDN edge assets.
   - Real-time WSS client with exponential backoff and room multiplexing.
5. **24/7 Keepalive & Anti-Sleep Monitoring**:
   - Internal async self-pinger pinging `/health` every 8 minutes.
   - External HTTP monitoring via Cron-Job.org / UptimeRobot.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Unified Async Event Loop | Supervise Uvicorn, PTB Bot, Userbot, Scheduler, and Keepalive in `main.py` | M1 | Survey 1 / R1 |
| 2 | Dynamic Port & Host Binding | Bind to `0.0.0.0:$PORT` with fallback to 8000 | M1 | Survey 1 / R1 |
| 3 | Multi-Stage Dockerfile | Production Dockerfile with `python:3.11-slim-bookworm`, non-root user, curl healthcheck | M1 | Survey 1 / R1 |
| 4 | Clean Dockerignore | Exclude `new_venv`, `.agents`, `CosyVoice`, caches from build context | M1 | Survey 1 / R1 |
| 5 | Koyeb Deployment Specification | Production `koyeb.yaml` for Koyeb Nano free tier | M1 | Survey 1 / R1 |
| 6 | Render Deployment Specification | Production `render.yaml` with Docker environment & dynamic healthcheck | M1 | Survey 1 / R1 |
| 7 | Graceful Signal Handling | Linux SIGTERM / SIGINT shutdown sequence for cloud platforms | M1 | Survey 1 / R1 |
| 8 | Cloud DATABASE_URL Parsing | Parse Supabase / Neon connection strings with `ssl="require"` | M2 | Survey 2 / R2 |
| 9 | Supabase PgBouncer Compatibility | Support port 6543 with `statement_cache_size=0` & pool size (1-5) | M2 | Survey 2 / R2 |
| 10 | Schema Completeness | Full 18-table DDL and B-tree indexes in `_create_tables_and_indexes()` | M2 | Survey 2 / R2 |
| 11 | Missing Database Query Methods | Restore 16 missing business query methods in `database.py` | M2 | Survey 2 / R2 |
| 12 | Endpoint Query Refactoring | Fix broken `conn.cursor()` and `%s` in FastAPI endpoints | M2 | Survey 2 / R2 |
| 13 | Upstash Redis 7 TLS & Resiliency | Configure `rediss://`, `health_check_interval=30`, `retry_on_timeout=True` | M2 | Survey 2 / R2 |
| 14 | Cache Service Import Fix | Fix broken `redis_client` import in `app/services/cache_service.py` | M2 | Survey 2 / R2 |
| 15 | Active DB & Redis Healthcheck | Enhance `/health` with live `SELECT 1` and Redis ping checks | M2 | Survey 2 / R2 |
| 16 | Vercel Deployment Configuration | `admin_panel/vercel.json` with security headers, clean URLs, CSP | M3 | Survey 3 / R3 |
| 17 | Real-Time WSS Frontend Client | Client-side WebSocket hook with exponential backoff & room multiplexing | M3 | Survey 3 / R3 |
| 18 | Admin Panel Settings Page | Create `/dashboard/settings/page.tsx` to eliminate 404 navigation gap | M3 | Survey 3 / R3 |
| 19 | Admin Panel Env Templates | `admin_panel/.env.example` & `.env.local.example` with API/WS URLs | M3 | Survey 3 / R3 |
| 20 | Internal Keepalive Self-Ping | Integrate `keepalive_worker.py` into `main.py`, lifespan & scheduler | M4 | Survey 3 / R4 |
| 21 | External Uptime Monitoring | Configurations and guides for Cron-Job.org / UptimeRobot | M4 | Survey 3 / R4 |
| 22 | Comprehensive Deployment Guide | Production `DEPLOYMENT_GUIDE.md` with step-by-step free tier guide | M5 | Survey 1-3 |
| 23 | Root & Component Env Templates | Clean, sanitized `.env.example` across all service folders | M5 | Survey 1-3 |
| 24 | Cloud Deployment Verification Script | Automated CLI smoke test validating DB, Redis, Bot, AI, and HTTP | M5 | Survey 1-3 |
| 25 | E2E Cloud Test Suite Validation | Pass 100% of E2E and unit test suite across Tiers 1-5 | M6 | Survey 1-3 |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Containerization & Process Lifecycle | `main.py`, `Dockerfile`, `.dockerignore`, `koyeb.yaml`, `render.yaml` | None | DONE |
| M2 | Cloud PostgreSQL 16 & Serverless Redis 7 | `database.py`, `app/api/endpoints/*.py`, `app/core/redis_manager.py`, `app/core/redis.py`, `app/services/cache_service.py`, `app/main.py` | M1 | PLANNED |
| M3 | Next.js Admin Panel & CRM Deployment | `admin_panel/vercel.json`, `admin_panel/src/hooks/useWebSocket.ts`, `admin_panel/src/app/dashboard/settings/page.tsx`, `admin_panel/.env.example` | None | PLANNED |
| M4 | 24/7 Keepalive & Health Monitoring | `keepalive_worker.py`, `main.py`, `app/main.py`, `scheduler_manager.py` | M1, M2 | PLANNED |
| M5 | Deployment Documentation & Verification Tooling | `DEPLOYMENT_GUIDE.md`, `.env.example`, `scripts/verify_cloud_deployment.py` | M1, M2, M3, M4 | PLANNED |
| M6 | Final Verification & Coverage Hardening | E2E Test Suite (Tiers 1-5), Reviewer Approval, Challenger Validation, Clean Audit | M1, M2, M3, M4, M5 | PLANNED |

---

## Interface Contracts
### Unified Backend ↔ Cloud Host (Koyeb / Render)
- **Port**: Listens on `0.0.0.0:$PORT` (defaults to 8000).
- **Health Check**: `GET /health` returns `200 OK` with JSON `{"status": "healthy"|"degraded", "database": "connected"|"offline", "redis": "connected"|"memory_fallback", "bot": "running", "uptime_seconds": float}`.
- **Signals**: `SIGTERM` / `SIGINT` initiates graceful drain within 15 seconds.

### Backend ↔ PostgreSQL 16 (Supabase / Neon)
- **DSN Format**: `postgresql://[user]:[password]@[host]:[port]/[dbname]?sslmode=require`
- **Pooler Mode (Port 6543)**: `statement_cache_size=0`, `min_size=1`, `max_size=5`.
- **Query Interface**: `await db.execute(sql, *params)`, `await db.fetch_one(sql, *params)`, `await db.fetch_all(sql, *params)`.

### Backend ↔ Upstash Redis 7
- **DSN Format**: `rediss://default:[token]@[host]:6379`
- **Options**: `health_check_interval=30`, `retry_on_timeout=True`, `socket_timeout=5.0`.
- **Fallback**: In-memory dictionary fallback with identical async interface if Redis is unreachable.

### Admin Panel ↔ Backend
- **REST API**: `NEXT_PUBLIC_API_URL` -> `${BACKEND_URL}/api/v1`
- **WebSocket (WSS)**: `NEXT_PUBLIC_WS_URL` -> `wss://${BACKEND_HOST}/ws?room=admin`

---

## Code Layout
- `main.py`: Top-level async supervisor for Uvicorn, Telegram Bot, UserBot, and Keepalive.
- `app/main.py`: FastAPI application definition, middleware, routers, `/health`, `/ws`.
- `app/api/endpoints/`: FastAPI REST controllers (`clients.py`, `orders.py`, `staff.py`, `finance.py`, etc.).
- `app/core/redis_manager.py`: Redis 7 FSM, Redlock, and Pub/Sub manager.
- `database.py`: Asyncpg PostgreSQL 16 / SQLite WAL persistence engine.
- `Dockerfile`: Multi-stage Docker container build.
- `koyeb.yaml`: Koyeb Nano service specification.
- `render.yaml`: Render Web Service specification.
- `keepalive_worker.py`: 8-minute async self-ping worker.
- `admin_panel/`: Next.js 16 frontend application.
  - `vercel.json`: Vercel edge deployment configuration.
  - `src/hooks/useWebSocket.ts`: Real-time WebSocket hook.
  - `src/app/dashboard/settings/page.tsx`: System settings page.
- `DEPLOYMENT_GUIDE.md`: Step-by-step 100% Free Forever deployment guide.
- `scripts/verify_cloud_deployment.py`: Automated cloud verification script.
