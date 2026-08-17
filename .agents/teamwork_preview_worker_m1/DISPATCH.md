## 2026-08-17T09:57:18Z

You are teamwork_preview_worker_m1, an implementation specialist.
Your working directory is: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_worker_m1
Original request path: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/ORIGINAL_REQUEST.md
Project plan path: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/PROJECT.md
Explorer handoff path: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_explorer_survey_1/handoff.md
Project root: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis

Your exclusive file write ownership for Milestone 1:
- `main.py`
- `Dockerfile`
- `.dockerignore`
- `koyeb.yaml`
- `render.yaml`

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your objectives:
1. Review `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `handoff.md` from `teamwork_preview_explorer_survey_1`.
2. Refactor `main.py` to be a unified, high-performance async process supervisor that:
   - Initializes the database via `await db.init_db()`.
   - Programmatically runs Uvicorn ASGI server (`app.main:app`) on host `0.0.0.0` and dynamic port `int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))`.
   - Concurrently executes `run_bot_async()`, `run_userbot_async()`, `start_scheduler(...)`, `_tts_worker()`, and `start_keepalive_worker()`.
   - Implements graceful shutdown signal handlers (`SIGTERM`, `SIGINT`) on Linux/POSIX and Windows compatibility fallback.
3. Update `Dockerfile` to a clean, multi-stage, production-ready container definition:
   - Remove Aliyun mirror, use standard PyPI.
   - Stage 1 builder: `python:3.11-slim-bookworm`, install compilation tools (`build-essential`, `libpq-dev`, `gcc`, `ffmpeg`, `libsndfile1`), install requirements into `/opt/venv`.
   - Stage 2 runtime: `python:3.11-slim-bookworm`, copy `/opt/venv`, install runtime libs (`libpq5`, `ffmpeg`, `libsndfile1`, `curl`), create non-root `appuser` (UID 10001), set permissions for `/app/data` and `/app/logs`.
   - Add dynamic port healthcheck: `HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 CMD curl -f http://localhost:${PORT:-8000}/health || exit 1`.
   - Default `CMD ["python", "main.py"]`.
4. Update `.dockerignore` to cleanly exclude `new_venv/`, `venv/`, `.agents/`, `CosyVoice/`, `*.session`, `*.session-journal`, `*.db-shm`, `*.db-wal`, `__pycache__`, `.git`.
5. Create production `koyeb.yaml` configured for Koyeb Free Nano tier with port 8000, `/health` route, health checks, and standard environment variables.
6. Update `render.yaml` with `env: docker`, `dockerfilePath: ./Dockerfile`, `healthCheckPath: /health`, Frankfurt region, and complete environment variable mapping.
7. Run verification commands (e.g. Python syntax checks `python -m py_compile main.py`, pytest on existing unit tests) and document the full results in `c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_worker_m1/handoff.md`.

Send a summary message when complete.
