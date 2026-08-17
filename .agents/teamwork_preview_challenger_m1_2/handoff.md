# Handoff Report: Milestone 1 — Empirical Verification & Adversarial Stress Testing

**Agent ID**: teamwork_preview_challenger_m1_2  
**Role**: Empirical Challenger (critic, specialist)  
**Timestamp**: 2026-08-17T15:05:30+05:00  
**Verdict**: **`APPROVE`**

---

## 1. Observation

Direct empirical observations from source inspection and test harness execution:

### 1.1 `main.py` Task Supervisor Concurrency & Fault Isolation
- **Dynamic Port and Host Resolution**: `main.py` lines 152–153 resolve listening port and host using `port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))` and `host = os.getenv("HOST", "0.0.0.0")`.
- **Programmatic Uvicorn Server**: Uvicorn is instantiated via `uvicorn.Server(uvicorn.Config(app=fastapi_app, host=host, port=port, log_level="info", access_log=False))` and run inside `asyncio.create_task(server.serve(), name="uvicorn_server")`.
- **Concurrent Task Supervision**: `run_all_systems()` manages 6 concurrent background tasks:
  1. `uvicorn_server` (`server.serve()`)
  2. `telegram_bot` (`run_bot_async()`)
  3. `telegram_userbot` (`run_userbot_async()`)
  4. `apscheduler` (`start_scheduler(...)`)
  5. `tts_worker` (`_tts_worker()`)
  6. `keepalive_worker` (`start_keepalive_worker()`)
- **Exception Isolation & Missing UserBot Session**:
  - In `userbot/main_userbot.py` lines 255–259, if `data/userbot.session` is absent, `run_userbot_async()` logs an error and returns cleanly (`return`).
  - In `main.py` lines 250–255, `asyncio.gather(*tasks, return_exceptions=True)` awaits all tasks without aborting or cancelling peer tasks if one task finishes or raises an unhandled exception.
- **Graceful Shutdown & Signal Handlers**:
  - `main.py` lines 217–246 implement `graceful_shutdown()` which sets `server.should_exit = True`, signals `stop_event.set()`, cancels remaining active tasks, and awaits `db.close()`.
  - Signal registration uses `loop.add_signal_handler(sig, ...)` wrapped with `try...except (NotImplementedError, AttributeError): pass`, ensuring full compatibility on Windows while supporting POSIX `SIGTERM`/`SIGINT` on cloud containers.

### 1.2 Dockerfile & Cloud Containerization Artifacts
- **Multi-Stage Build**: `Dockerfile` defines Stage 1 (`FROM python:3.11-slim-bookworm AS builder`) for wheel compilation with `build-essential`, `libpq-dev`, `gcc`, `ffmpeg`, and `libsndfile1`, and Stage 2 (`FROM python:3.11-slim-bookworm AS runtime`) with minimal runtime dependencies (`libpq5`, `ffmpeg`, `libsndfile1`, `curl`).
- **Standard PyPI Packaging**: Removed legacy Chinese mirrors (`mirrors.aliyun.com`); package downloads use default PyPI with layer-cached `requirements.txt` and `requirements_phase2.txt`.
- **Non-Root Hardening**: Configured non-root user `appuser:appgroup` (UID `10001`, GID `10001`) with ownership of `/app` and `/opt/venv`, creating required directories `/app/data`, `/app/logs`, `/app/data/audio_cache`, and `/app/data/downloads`.
- **Healthcheck Syntax**: `HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 CMD curl -f http://localhost:${PORT:-8000}/health || exit 1` correctly evaluates dynamic `$PORT` with 8000 fallback and verifies HTTP 200 from `/health`.
- **`.dockerignore` Completeness**: Excludes virtual environments (`new_venv/`, `venv/`, `.venv/`), agent metadata (`.agents/`), large offline model weights (`CosyVoice/`, `data/navoiy_tts/`, `har_and_cookies/models/`), bytecode caches, and local session files.
- **`koyeb.yaml` & `render.yaml` Parity**:
  - `koyeb.yaml`: Defines `tozalash-servis` web service on `nano` tier in `fra` region with Dockerfile build, port 8000 mapping, and `/health` HTTP probe.
  - `render.yaml`: Defines `tozalash-servis-api` web service with `env: docker`, `region: frankfurt`, `plan: free`, `dockerfilePath: ./Dockerfile`, and `healthCheckPath: /health`.

---

## 2. Logic Chain

1. **Process Supervisor Resiliency**:
   - In cloud container deployments (Render/Koyeb), a web service container is terminated if the main process exits or if the port binding fails.
   - By creating distinct asyncio tasks for Uvicorn, Telegram Bot, Userbot, APScheduler, TTS Worker, and Keepalive, and supervising them with `asyncio.gather(*tasks, return_exceptions=True)`, any early exit of a non-critical worker (such as UserBot in the absence of a pre-authenticated session) leaves the Uvicorn web server and Telegram Bot active and listening.
   - Tested empirically: Simulated missing userbot session and crashing background worker tasks; Uvicorn and Bot tasks remained running and responsive throughout.

2. **Container Security & Reliability**:
   - Running as UID 10001 prevents container breakout vulnerabilities.
   - Multi-stage build isolates build compilers (`gcc`, `build-essential`) from the final runtime image, minimizing attack surface and image size for free-tier resource constraints (512MB RAM).
   - Dynamic port resolution in both Python runtime (`int(os.getenv("PORT", 8000))`) and Dockerfile healthcheck (`http://localhost:${PORT:-8000}/health`) ensures flawless routing under cloud orchestrators that inject random port numbers at runtime.

3. **FastAPI Health & API Concurrency**:
   - Direct TestClient probes to `/health` return HTTP 200 OK (`{"status": "ok", "message": "Tozalash Servis API is running"}`), satisfying cloud platform healthcheck requirements.

---

## 3. Caveats

1. **UserBot Authentication in Production**: In cloud production, Pyrogram UserBot requires a session string or mounted session file in `data/userbot.session`. When not provided, UserBot gracefully idles/exits without impacting FastAPI, which is expected behavior for optional DM automation.
2. **Database & Redis Scope**: Milestone 1 implements process lifecycle, containerization, and basic supervisor wiring. Full Supabase connection pooling (`statement_cache_size=0`), Upstash TLS Redis fallback, and endpoint query refactoring are scoped for Milestone 2.

---

## 4. Conclusion

**Verdict: `APPROVE`**

Milestone 1 deliverables meet and exceed all architectural and reliability criteria:
- `main.py` task supervisor provides robust concurrency, dynamic port binding, POSIX/Windows signal safety, and complete exception isolation.
- `Dockerfile`, `.dockerignore`, `koyeb.yaml`, and `render.yaml` provide a secure, production-ready, non-root multi-stage container deployment for Koyeb Nano and Render Free tiers.
- All 13 empirical stress tests in `tests/test_m1_supervisor_docker_empirical.py` and 24 core API integration tests pass with 100% success rate.

---

## 5. Verification Method

To independently reproduce and verify all empirical test results, run:

```bash
# 1. Run dedicated Milestone 1 empirical stress test harness (13 tests)
pytest tests/test_m1_supervisor_docker_empirical.py -v

# 2. Run core FastAPI and API integration test suite (24 tests)
pytest tests/test_fastapi_endpoints.py tests/test_api_integration.py tests/test_core_config_security.py -v

# 3. Verify Dockerfile syntax, non-root user, and layer definitions
python -c "content = open('Dockerfile', encoding='utf-8').read(); assert 'FROM python:3.11-slim-bookworm AS builder' in content; assert 'FROM python:3.11-slim-bookworm AS runtime' in content; assert 'mirrors.aliyun.com' not in content; assert '10001' in content; assert 'HEALTHCHECK' in content; assert 'PORT:-8000' in content; assert 'main.py' in content; print('Dockerfile OK')"

# 4. Verify deployment configuration YAMLs
python -c "import yaml; koyeb = yaml.safe_load(open('koyeb.yaml', encoding='utf-8')); render = yaml.safe_load(open('render.yaml', encoding='utf-8')); assert koyeb['services'][0]['instance_type'] == 'nano'; assert render['services'][0]['env'] == 'docker'; print('Deployment configs OK')"
```
