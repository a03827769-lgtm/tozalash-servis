# BRIEFING — 2026-08-17T09:51:50Z

## Mission
Investigate Backend & Telegram Bot architecture, containerization requirements, and process lifecycle for Cloud Deployment (Koyeb / Render).

## 🔒 My Identity
- Archetype: explorer
- Roles: survey, synthesis, architectural analysis
- Working directory: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_explorer_survey_1
- Original parent: 38e7b44d-431f-4ee8-8359-a3f0fedecbb8
- Milestone: Milestone 1 - Cloud Deployment Readiness & Container Architecture Investigation

## 🔒 Key Constraints
- Read-only investigation — do NOT implement / edit source code
- Files for content delivery, messages for coordination
- Self-contained 5-component handoff report (handoff.md)

## Current Parent
- Conversation ID: 38e7b44d-431f-4ee8-8359-a3f0fedecbb8
- Updated: 2026-08-17T09:51:50Z

## Investigation State
- **Explored paths**: `main.py`, `app/main.py`, `app/api/*`, `bot/telegram_bot.py`, `userbot/main_userbot.py`, `ws_server.py`, `cookie_server.py`, `keepalive_worker.py`, `database.py`, `app/core/config.py`, `Dockerfile`, `render.yaml`, `docker-compose.yml`, `.dockerignore`, `tests/`
- **Key findings**:
  1. Root `main.py` runs `ws_server.py` on 8001 and `cookie_server.py` on 9090, but DOES NOT start `app.main:app` (FastAPI) on port 8000. In cloud deployments, port 8000 is unopened and all REST endpoints/health checks fail.
  2. Free cloud tiers (Koyeb / Render) provide 512MB RAM and only 1 public web service/port. Running FastAPI and Telegram Bot inside a single unified Python async event loop is the most cost-effective (<200MB RAM) and robust pattern.
  3. `render.yaml` uses python native env instead of Docker; `koyeb.yaml` is completely missing.
  4. `Dockerfile` hardcodes Aliyun mirror (breaks/slows cloud builds outside China) and `.dockerignore` misses `new_venv/` (which bloats context by >4GB).
  5. Port handling must dynamically resolve `$PORT` and bind to `0.0.0.0`.
  6. Graceful shutdown requires capturing `SIGTERM` on Linux PID 1 and cleanly stopping PTB updater, Pyrogram, and DB/Redis pools.
- **Unexplored areas**: None, full survey completed.

## Key Decisions Made
- Recommend unifying FastAPI and Bot runner into a single-process async supervisor in `main.py` using `uvicorn.Server` + `asyncio.gather`.
- Recommend multi-stage Dockerfile based on `python:3.11-slim-bookworm` with standard PyPI wheels, non-root user, and dynamic `$PORT`.
- Recommend creating `koyeb.yaml` and updating `render.yaml` for 100% Free Forever deployment.

## Artifact Index
- DISPATCH.md — incoming dispatch records
- BRIEFING.md — persistent working memory
- progress.md — liveness heartbeat
- handoff.md — final comprehensive report
