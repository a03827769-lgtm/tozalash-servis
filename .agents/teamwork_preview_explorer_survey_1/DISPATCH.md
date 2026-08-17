## 2026-08-17T09:51:50Z
<USER_REQUEST>
You are teamwork_preview_explorer_survey_1, a read-only exploration agent.
Your working directory is: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_explorer_survey_1
Original request path: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/ORIGINAL_REQUEST.md
Project root: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis

Your task is to conduct a thorough technical investigation of the Backend & Telegram Bot architecture, containerization requirements, and process lifecycle for Cloud Deployment (Koyeb / Render).

Specifically investigate and document in your handoff report:
1. Detailed repository layout and backend structure (FastAPI app, routes, background tasks, entrypoints like main.py, bot runners).
2. How the Telegram Bot and UserBot (if any) are currently run, how they interact with FastAPI, and how they should be containerized.
3. Multi-process / concurrent execution strategy for free cloud tiers: can FastAPI and Telegram bot run in a single container or separate services? How to configure Koyeb (`koyeb.yaml`) and Render (`render.yaml`)?
4. Port management ($PORT environment variable handling, default 8000/80), host binding (0.0.0.0), and existing vs needed healthcheck endpoints (`/health`, `/healthz`, `/api/health`).
5. Multi-stage Dockerfile architecture (optimizing image size, non-root user, Python dependencies, caching, security, fast startup).
6. Asynchronous process supervision, signal handling (SIGTERM, SIGINT), and graceful shutdown mechanisms.
7. Missing files, configuration gaps, and concrete recommendations for Milestone 1.

Follow the Handoff Protocol. Write your comprehensive report to `c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_explorer_survey_1/handoff.md` and send a summary message back. Do NOT edit source code files.
</USER_REQUEST>
