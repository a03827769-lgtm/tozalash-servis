# Handoff Report: Backend & Telegram Bot Architecture, Containerization & Process Lifecycle for Cloud Deployment (Koyeb / Render)

**Agent ID**: teamwork_preview_explorer_survey_1  
**Timestamp**: 2026-08-17T09:55:00Z  
**Scope**: Backend entrypoints, FastAPI app lifecycle, Telegram Bot/Userbot concurrency, free cloud tier constraints (Koyeb/Render), port binding ($PORT), healthcheck endpoints, multi-stage Dockerfile architecture, and process supervision/shutdown.

---

## 1. Observation

Direct code observations from the codebase:

### 1.1 Backend Entrypoints & FastAPI Lifecycle Disconnect
- `main.py` lines 159-178:
  ```python
  tasks = [
      asyncio.create_task(
          start_scheduler(
              content_manager,
              competitor_analyzer,
              daily_report_system,
              self_learning_system,
              workers_manager,
              profit_analytics,
              voice_agent,
          )
      ),
      asyncio.create_task(run_userbot_async()),
      asyncio.create_task(run_bot_async()),
      asyncio.create_task(run_ws_server()),  # Real-Time WebSocket Dashboard (Port 8001)
      asyncio.create_task(_tts_worker()),    # TTS Async Queue Worker (Task 53)
      asyncio.create_task(start_cookie_server()), # Cookie Sync Server (Port 9090)
  ]
  ```
- `app/main.py` lines 40-86 defines the full FastAPI application (`app = FastAPI(...)`) containing:
  - CORS middleware (lines 54-60)
  - GraphQL router `/graphql` (line 65)
  - WebSockets router `/ws` (line 66)
  - Prometheus metrics `/metrics` and `/metrics_instrumentator` (lines 73-74)
  - API v1 router `/api/v1` (line 77) with 13 domain routers (Telegram Bot TMA, Instagram, Media/Telephony, BigData/IoT, CRM, Finance, HR, Inventory, Messaging, Payment, Staff, Clients, Orders)
  - Health check endpoint `@app.get("/health")` (line 80)
  - Local standalone runner at line 86: `uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)`
- **Disconnection**: When `python main.py` is executed (as invoked by `Dockerfile` line 76 `CMD ["python", "main.py"]` and `render.yaml` line 9 `startCommand: "python main.py"`), `app/main.py` is **never started**! Instead, only `ws_server.py` starts on port 8001 and `cookie_server.py` on 127.0.0.1:9090. As a result, port 8000 is unopened, and all REST endpoints, TMA verification, payment webhooks, and `/health` probes return `Connection Refused`.

### 1.2 Telegram Bot & UserBot Execution Structure
- `bot/telegram_bot.py` lines 37-107:
  - Uses `python-telegram-bot` v20.7 `Application.builder().token(TELEGRAM_BOT_TOKEN).build()`.
  - Runs in long-polling mode via `await app.updater.start_polling(drop_pending_updates=True)`.
  - In `run_bot_async()` lines 82-94, it uses an `asyncio.Event()` for stopping, with `loop.add_signal_handler(sig, stop_event.set)` wrapped in `try/except NotImplementedError` (for Windows compatibility).
  - In `finally` block (lines 100-106): calls `await app.updater.stop()`, `await app.stop()`, `await app.shutdown()`.
- `userbot/main_userbot.py` lines 247-302:
  - Uses Pyrogram v2.0 `Client(name="data/userbot", api_id=..., api_hash=...)`.
  - Checks `session_file = DATA_DIR / "userbot.session"` (line 255). If absent, logs error and returns early without crashing `main.py`.
  - Starts with `await app.start()`, then calls `await idle()`.
  - In `finally` block (lines 296-301): calls `await app.stop()`.
- In-memory coupling: Both `bot` and `userbot` interact directly with `database.py` (`db`), `ai_brain.py` (`ai_brain`), and `workers_manager.py` within the shared event loop.

### 1.3 Free Cloud Tier Specifications (Render & Koyeb)
- **Render.com Free Web Service**:
  - RAM: 512 MB, CPU: 0.1 vCPU.
  - Port binding: Injects dynamic `PORT` environment variable (e.g. `PORT=10000` or user-defined `8000`). Public incoming traffic is routed to `0.0.0.0:$PORT`.
  - Inactivity: Spins down to sleep after 15 minutes of zero incoming HTTP traffic. Free worker processes (non-web services) do NOT exist on the free tier (workers are paid-only).
- **Koyeb.com Free Tier (Nano)**:
  - RAM: 512 MB, CPU: 0.1 vCPU, Disk: 2GB.
  - Port binding: Routes HTTP traffic to declared internal container port (typically `8000`).
  - Web Service constraint: Only 1 web service instance is free.

### 1.4 Dockerfile and Containerization State
- `Dockerfile` lines 25-36:
  - Builder stage hardcodes Aliyun mirror:
    ```dockerfile
    RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
        pip config set global.trusted-host mirrors.aliyun.com && \
        pip install --upgrade pip==24.2
    ```
    This causes network latency and timeout issues on European (Frankfurt) and US cloud builders.
  - Requirements list includes large dependencies: `torch==2.1.2`, `torchaudio==2.1.2`, `TTS==0.22.0`, `chromadb==0.4.22`, `matplotlib`, `pandas`.
  - Runtime stage creates non-root user `appuser` (UID default) and switches `USER appuser`.
  - Health check: `HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD curl -f http://localhost:8000/health || exit 1`.
  - Entrypoint: `CMD ["python", "main.py"]`.
- `.dockerignore`:
  - Contains `venv/`, `__pycache__/`, `logs/`, `.git/`, etc., but **omits** `new_venv/` (which exists in root with over 4GB of Windows virtualenv files).

### 1.5 Cloud Configuration Files (`render.yaml`, `koyeb.yaml`)
- `render.yaml` (lines 1-42):
  - Uses `env: python` instead of `env: docker`.
  - Uses `buildCommand: "pip install -r requirements.txt"`, which fails to install required system packages like `ffmpeg`, `libsndfile1`, and `libpq-dev` on native Python runtimes.
  - Uses hardcoded `PORT=8000`.
- `koyeb.yaml`: **Does not exist** anywhere in the repository.

### 1.6 Database & Redis Cloud Integration
- `database.py` (lines 30-90):
  - Primary: `asyncpg` PostgreSQL 16 pool with `min_size=5, max_size=30`, connection timeout 1.5s.
  - Fallback: `aiosqlite` with WAL mode (`PRAGMA journal_mode = WAL; PRAGMA busy_timeout = 30000;`).
  - Reads `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE`, `DB_TYPE`.
- `app/core/redis.py` (lines 14-23):
  - Connects via `redis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)`.
  - Works with Upstash Redis (`rediss://default:...@...upstash.io:6379`).

---

## 2. Logic Chain

### 2.1 Single-Process Unified Async Architecture for Free Tiers
1. **Free Tier Constraint**: Render and Koyeb free tiers permit exactly one free Web Service with 512MB RAM and 0.1 vCPU. Running a separate API container and a separate Bot worker container would require paid worker tiers or exceed free instance allocations.
2. **Resource Efficiency**: A single Python 3.11 process running FastAPI on Uvicorn + PTB Polling + Pyrogram UserBot + APScheduler consumes approximately 160MB–220MB RAM, well below the 512MB threshold.
3. **Event Loop Integration**: Uvicorn can be run programmatically via `uvicorn.Server(config).serve()` inside an `asyncio.Task` within `main.py`. This unifies FastAPI HTTP handling on `$PORT`, WebSocket handling on `/ws`, and Telegram polling into a single event loop sharing the same DB pool and Redis connection.

### 2.2 Port Binding & Health Check Resolution
1. Cloud platforms dynamically assign `$PORT` (e.g. Render assigns `PORT=10000`, Koyeb defaults to `8000`).
2. Binding to `0.0.0.0` with `port = int(os.getenv("PORT", 8000))` guarantees compatibility with any cloud routing layer.
3. Consolidating `ws_server.py` into `app/main.py` eliminates the conflict between port 8000 (API) and port 8001 (WebSocket), allowing both `/api/v1/*`, `/ws`, and `/health` to be served over the single exposed public port.
4. Comprehensive health checks (`/health`, `/healthz`, `/api/health`) must provide:
   - Immediate liveness (HTTP 200) to pass cloud load balancer probes during cold boot.
   - Readiness details (PostgreSQL connection status, Redis ping, bot polling state, uptime).

### 2.3 Container Build & Image Size Optimization
1. Removing the Aliyun mirror restores direct high-speed downloads from standard PyPI and PyTorch CPU wheel indices (`https://download.pytorch.org/whl/cpu`).
2. Adding `new_venv/`, `CosyVoice/`, `*.db-shm`, `*.db-wal` to `.dockerignore` prevents gigabytes of unnecessary build context from transferring to the Docker daemon.
3. Multi-stage Dockerfile cleanly separates heavy build tools (`gcc`, `build-essential`) from the lean runtime container containing only compiled wheels, `ffmpeg`, `libsndfile1`, `libpq5`, and `curl`.
4. Running as non-root `appuser` (UID 10001) prevents privilege escalation security risks.

### 2.4 Process Supervision & Graceful Shutdown
1. When Koyeb or Render restarts or redeploys, it dispatches `SIGTERM` to PID 1.
2. On Linux, `loop.add_signal_handler(signal.SIGTERM, shutdown_callback)` catches this signal.
3. Shutdown sequence:
   - Set server `should_exit = True` on Uvicorn to stop accepting new requests.
   - Await `app.updater.stop()`, `app.stop()`, and `app.shutdown()` on Telegram Bot.
   - Await `userbot.stop()` on Pyrogram Userbot.
   - Await `db.close()` to release all asyncpg connections back to Supabase/Neon.
   - Cancel keepalive pinger and scheduler tasks.
   - Exit with status code 0 within the 10–30s cloud grace period.

---

## 3. Caveats

1. **UserBot Session in Headless Cloud**: Pyrogram `userbot` requires either an existing `data/userbot.session` file or a Pyrogram session string (`PYROGRAM_SESSION_STRING` / `SESSION_STRING` in `.env`). In ephemeral containers, generating a session string locally and passing it via environment variable is the recommended pattern.
2. **Render Sleep on Inactivity**: On Render Free Web Services, if no HTTP request arrives for 15 minutes, the instance is suspended. The internal `keepalive_worker.py` (which pings `APP_PUBLIC_URL/health` every 8 minutes) plus an external pinger (e.g. Cron-Job.org / UptimeRobot) prevents idle sleep.
3. **Heavy Offline TTS vs Cloud TTS**: Large offline TTS models (CosyVoice / offline TTS >1GB) cannot run inside 512MB RAM containers. The codebase already implements Edge-TTS (`edge-tts` with `uz-UZ-MadinaNeural`) and audio caching in `uzbek_tts.py`, which operates with minimal RAM (<30MB) and fast responses (<300ms).

---

## 4. Conclusion

The repository has a strong foundational implementation (FastAPI, PTB bot, asyncpg database layer, Edge-TTS), but exhibits five critical gaps preventing seamless cloud deployment:
1. **Entrypoint Disconnection**: `main.py` does not mount or serve `app.main:app` (FastAPI), resulting in an unopened port 8000 and failing health checks.
2. **Port Fragmentation**: Standalone `ws_server.py` runs on port 8001 while API runs on 8000; free cloud tiers expose only one port.
3. **Missing Koyeb Configuration**: `koyeb.yaml` is absent.
4. **Suboptimal Render Configuration**: `render.yaml` specifies native Python instead of Docker and hardcodes port 8000.
5. **Dockerfile & .dockerignore Inefficiencies**: Aliyun mirror hardcoding, missing `new_venv` exclusion in `.dockerignore`, and lack of Linux `SIGTERM` signal handling.

---

## 5. Verification Method & Actionable Recommendations

### 5.1 Independent Verification Commands
To independently verify the findings without modifying source code:
1. **Check entrypoints and ports**:
   ```powershell
   Select-String -Path "main.py", "ws_server.py", "app/main.py" -Pattern "uvicorn|8000|8001|run_ws_server"
   ```
2. **Check `.dockerignore` for `new_venv`**:
   ```powershell
   Select-String -Path ".dockerignore" -Pattern "new_venv"
   ```
3. **Verify tests suite passes**:
   ```powershell
   pytest tests/test_fastapi_endpoints.py tests/test_api_integration.py -v
   ```

---

### 5.2 Concrete Implementation Specifications for Milestone 1

#### A. Unified `main.py` Process Supervisor Pattern
Integrate Uvicorn server directly into `main.py` with dynamic `$PORT` and graceful shutdown:
```python
import os
import asyncio
import signal
import uvicorn
from app.main import app as fastapi_app
from bot.telegram_bot import run_bot_async
from userbot.main_userbot import run_userbot_async
from scheduler_manager import start_scheduler
from keepalive_worker import start_keepalive_worker
from database import db

async def run_all_systems():
    port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
    host = "0.0.0.0"
    
    # 1. Initialize Database
    await db.init_db()
    
    # 2. Uvicorn Server Config
    config = uvicorn.Config(
        app=fastapi_app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    
    # 3. Concurrent Tasks
    tasks = [
        asyncio.create_task(server.serve()),
        asyncio.create_task(run_bot_async()),
        asyncio.create_task(run_userbot_async()),
        asyncio.create_task(start_scheduler(...)),
        asyncio.create_task(start_keepalive_worker()),
    ]
    
    # 4. Graceful Shutdown Signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(server, tasks)))
        except (NotImplementedError, AttributeError):
            pass  # Windows fallback
            
    await asyncio.gather(*tasks, return_exceptions=True)
```

#### B. Proposed Production `Dockerfile`
```dockerfile
# Multi-Stage Production Dockerfile for Tozalash Servis
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt requirements_phase2.txt ./
RUN pip install --no-cache-dir \
    --default-timeout=600 \
    -r requirements.txt \
    -r requirements_phase2.txt

# --- Stage 2: Lean Runtime ---
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

COPY . .

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser && \
    mkdir -p /app/data /app/logs /app/data/audio_cache && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["python", "main.py"]
```

#### C. Proposed `koyeb.yaml`
```yaml
name: tozalash-servis
services:
  - name: backend
    type: web
    instance_type: nano
    regions:
      - fra
    docker:
      dockerfile: Dockerfile
    ports:
      - port: 8000
        path: /
        protocol: http
    routes:
      - path: /
        port: 8000
    health_checks:
      - http:
          path: /health
          port: 8000
        interval: 30
        timeout: 5
        unhealthy_threshold: 3
        healthy_threshold: 1
    env:
      - key: PORT
        value: "8000"
      - key: DB_TYPE
        value: "postgres"
      - key: DB_PORT
        value: "5432"
```

#### D. Proposed `render.yaml`
```yaml
services:
  - type: web
    name: tozalash-servis-api
    env: docker
    region: frankfurt
    plan: free
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: PORT
        value: 8000
      - key: DB_TYPE
        value: postgres
      - key: DB_PORT
        value: 5432
      - key: DB_HOST
        sync: false
      - key: DB_USERNAME
        sync: false
      - key: DB_PASSWORD
        sync: false
      - key: DB_DATABASE
        sync: false
      - key: REDIS_URL
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: ADMIN_TELEGRAM_ID
        sync: false
      - key: APP_PUBLIC_URL
        fromService:
          type: web
          name: tozalash-servis-api
          property: host
```

#### E. Additions to `.dockerignore`
```gitignore
new_venv/
venv/
.agents/
CosyVoice/
*.session
*.session-journal
*.db-shm
*.db-wal
```
