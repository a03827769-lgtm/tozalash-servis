## 2026-08-17T10:06:03Z

You are teamwork_preview_worker_m2, an implementation specialist.
Your working directory is: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_worker_m2
Original request path: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/ORIGINAL_REQUEST.md
Project plan path: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/PROJECT.md
Explorer handoff path: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_explorer_survey_2/handoff.md
Project root: c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis

Your exclusive file write ownership for Milestone 2:
- `database.py`
- `app/api/endpoints/clients.py`
- `app/api/endpoints/orders.py`
- `app/api/endpoints/staff.py`
- `analytics/chart_generator.py`
- `app/core/redis_manager.py`
- `app/core/redis.py`
- `app/services/cache_service.py`
- `app/main.py`

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your objectives:
1. Review `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `handoff.md` from `teamwork_preview_explorer_survey_2`.
2. Refactor `database.py`:
   - Parse standard `DATABASE_URL` (supporting `postgresql://...` and `postgres://...` formats as well as individual `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE`).
   - Automatically enable `ssl="require"` when SSL mode is requested or connecting to remote cloud hosts (Supabase/Neon).
   - Support Supabase transaction pooler (port 6543) by setting `statement_cache_size=0` on `asyncpg.create_pool`.
   - Set pool defaults suitable for cloud free tiers (`min_size=1, max_size=5`).
   - Ensure `_create_tables_and_indexes()` creates all 18 tables with PostgreSQL 16 compatible DDL and indexes, and matching SQLite DDL (`clients`, `workers`, `orders`, `transactions`, `messages`, `dynamic_guidelines`, `competitor_prices`, `learning_logs`, `finance`, `channel_posts`, `competitors`, `daily_reports`, `cities`, `services`, `order_workers`, `admin_audit_logs`, `feedback`, `marketing_campaigns`).
   - Restore all 16 missing business query methods in `database.py` (e.g. `get_orders_stats`, `get_finance_stats`, `get_today_orders`, `get_all_workers`, `get_available_workers`, `add_worker`, `register_worker`, `get_worker_by_tg_id`, `get_messages_count_today`, `get_successful_patterns`, `update_client_name`, `update_user_language`, `get_client_by_tg_id`, `add_order`, `update_order_status`, etc.) so that all application subsystems work flawlessly.
   - Maintain seamless zero-config fallback to `aiosqlite` WAL mode (`tozalash.db`) when PostgreSQL is not configured or unavailable.
3. Fix broken `conn.cursor()` and `%s` parameter usage in:
   - `app/api/endpoints/clients.py`
   - `app/api/endpoints/orders.py`
   - `app/api/endpoints/staff.py`
   - `analytics/chart_generator.py`
   Replace them with `await db.fetch_all(...)`, `await db.fetch_one(...)`, or `await db.execute(...)`.
4. Harden Serverless Redis 7 (Upstash) in `app/core/redis_manager.py` and `app/core/redis.py`:
   - Support `rediss://` TLS URLs with `health_check_interval=30` and `retry_on_timeout=True`.
   - In `app/core/redis.py`: Wrap `init_redis` in a try/except with `InMemoryBackend` fallback so temporary Redis unavailability never crashes the API.
   - Fix `app/services/cache_service.py` by importing `redis_manager` from `app.core.redis_manager` (instead of non-existent `redis_client`).
5. Enhance `/health` endpoint in `app/main.py`:
   - Perform active health verification against DB (`SELECT 1`) and Redis (`redis_manager.client.ping()`).
   - Return structured status: `{"status": "healthy"|"degraded", "database": "connected"|"offline", "redis": "connected"|"memory_fallback", "uptime_seconds": ..., "version": ...}`.
6. Verify and test all changes (run pytest, syntax checks, verify SQLite fallback and connection tests).
7. Write full handoff report to `c:/Users/victus/Desktop/avtomatizatsiya/tozalash_servis/.agents/teamwork_preview_worker_m2/handoff.md` and send completion message.
