# Technical Survey Report: Data Persistence, Managed PostgreSQL 16 (Supabase / Neon) & Serverless Redis 7 (Upstash) Integration

**Agent:** teamwork_preview_explorer_survey_2  
**Role:** Survey Explorer 2 — Data Persistence & Infrastructure Specialist  
**Target Project:** Tozalash Servis (FastAPI + Telegram Customer Bot + UserBot + Next.js Admin + Redis 7 + PostgreSQL 16)  
**Date:** 2026-08-17  
**Status:** Completed (Read-Only Investigation)  

---

## 1. Observation

A systematic, read-only code audit was conducted across all database, cache, configuration, migration, and containerization files in the `tozalash_servis` codebase. Below are direct, verbatim observations citing file paths, lines, and structural characteristics.

### 1.1 Database Architecture & ORM Dualism
- **Operational Layer (`database.py`)**:
  - `database.py:30-39`: Implements `Database` class supporting `PostgreSQL 16` via `asyncpg` and high-performance `SQLite` in WAL mode via `aiosqlite`.
  - `database.py:46-68`: Connection initialization uses separate environment variables (`DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE`). It does **not** parse or utilize standard cloud `DATABASE_URL` connection strings (e.g., Supabase/Neon DSNs).
  - `database.py:55-64`: Hardcoded connection pool sizing `min_size=5, max_size=30`, command timeout `5s`.
  - `database.py:55-64`: Passes no `ssl` parameter (`ssl=None`), causing connection rejections against cloud providers mandating `sslmode=require`.
  - `database.py:122-175`: Implements automatic query parameter translation (converts `?` to `$1, $2, ...` for `asyncpg`) across `execute()`, `fetch_one()`, and `fetch_all()`.
  - `database.py:179-447`: Initializes 8 relational tables (`clients`, `workers`, `orders`, `transactions`, `messages`, `dynamic_guidelines`, `competitor_prices`, `learning_logs`) and 8 B-Tree indexes.
  - **Method Truncation / Omission**: `database.py` contains 26 methods, but is missing 16 business methods that were present in `database_sqlite.py` / `database.py.orig` and are actively invoked by `bot/`, `ai_brain.py`, `reports/`, `analytics/`, and `workers/` (e.g. `get_orders_stats`, `get_messages_count_today`, `get_successful_patterns`, `get_finance_stats`, `get_today_orders`, `get_all_workers`, `get_available_workers`, `add_worker`, `register_worker`, `update_client_name`, `update_user_language`).

- **SQLAlchemy ORM Layer (`app/db/session.py`, `app/models/`)**:
  - `app/db/session.py:6-24`: Configures two async SQLAlchemy engines (`engine` for Master writes and `read_engine` for Read replicas) using `create_async_engine(settings.get_database_url, pool_size=50, max_overflow=20)`.
  - `app/core/config.py:135-139`: `settings.get_database_url` defaults to `mysql+aiomysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}`.
  - `app/models/base.py`: Defines `TenantBase` and `Company` with multi-tenant `company_id` columns.
  - `app/models/order.py`: Defines `Order` with `metadata_data = Column(JSONB)` and PostgreSQL GIN index `idx_order_metadata_gin`, plus `OrderArchive`.
  - `app/models/audit.py`: Defines `AuditLog`.
  - `app/models/geo.py`: Defines `WorkerLocation` with `Geometry("POINT", srid=4326)`.
  - **Incomplete Model Coverage**: ORM models exist for only 4 entities (`Company`, `Order`, `AuditLog`, `WorkerLocation`). The remaining 14 business entities lack SQLAlchemy models.

### 1.2 Broken Cursor Usage in FastAPI Endpoints
- Multiple REST API endpoints import `database.py`'s `Database` class but attempt to use cursor context managers leftover from deprecated `aiomysql` code:
  - `app/api/endpoints/clients.py:14-15`: `async with db.get_conn() as conn: async with conn.cursor() as cursor:`
  - `app/api/endpoints/clients.py:41-44`: `async with db.get_conn() as conn: async with conn.cursor() as cursor: await cursor.execute("DELETE FROM clients WHERE telegram_id = %s OR id = %s", (client_id, client_id))`
  - `app/api/endpoints/orders.py:14-16`: `async with db.get_conn() as conn: async with conn.cursor() as cursor:`
  - `app/api/endpoints/staff.py:57-60`: `async with db.get_conn() as conn: async with conn.cursor() as cursor:`
  - `analytics/chart_generator.py:18-20`: `async with db.get_conn() as conn: async with conn.cursor() as cursor:`
  - **Impact**: `db.get_conn()` returns `self.pg_pool.acquire()` (asyncpg connection) or `self` (Database instance). Neither has a `.cursor()` method, resulting in immediate runtime `AttributeError` crashes upon invocation. In addition, `%s` parameter syntax is incompatible with both SQLite (`?`) and `asyncpg` (`$1`).

### 1.3 Database Initialization & Migrations
- `alembic.ini:63`: `sqlalchemy.url = driver://user:pass@localhost/dbname`.
- `alembic/env.py:15`: `config.set_main_option("sqlalchemy.url", settings.get_database_url)`.
- `alembic/versions/`: Directory is **empty** (0 migration scripts).
- `migrations/`: Contains 9 `.sql` files (`001_initial.sql` to `009_gamification_and_ratings.sql`) with MySQL-specific syntax (`AUTO_INCREMENT`, `VARCHAR(255)`, `DOUBLE`, `BOOLEAN DEFAULT FALSE`, `ON UPDATE CURRENT_TIMESTAMP`), which fail when executed on PostgreSQL 16.
- `migrations_runner.py:1-5`: Hardcoded exclusively for `aiosqlite` and explicitly skips `migrations/*.sql` because of MySQL incompatibility.
- `main.py:123`: Calls `await db.init_db()` at startup to run `_create_tables_and_indexes()`.

### 1.4 Redis Layer & Serverless Redis 7 (Upstash) Usage
- **Manager Implementation (`app/core/redis_manager.py`)**:
  - Implements `RedisManager` singleton with `MemoryFallback` class.
  - `redis_manager.py:86-93`: Initializes connection pool using `aioredis.ConnectionPool.from_url(self.redis_url, max_connections=50, decode_responses=True, socket_timeout=5, socket_connect_timeout=5)`.
  - Feature coverage:
    - **FSM State**: `get_fsm_state(user_id)`, `set_fsm_state(user_id, state, context, ttl=86400)`, `clear_fsm(user_id)`.
    - **Redlock**: `acquire_lock(resource_name, timeout_seconds=10)` (atomic `SET NX EX`), `release_lock(resource_name)`.
    - **Pub/Sub**: `publish(channel, message)` (used by `app/api/websockets.py` for room events).
    - **Query Cache**: `get_cache(key)`, `set_cache(key, value, ttl=300)`.
  - **MemoryFallback**: Full local dictionary fallback with async lock and subscriber callback support for offline/local resilience.
- **FastAPI Cache & Rate Limiting (`app/core/redis.py`)**:
  - `app/core/redis.py:14-18`: `redis.from_url(settings.REDIS_URL...)` initializes `FastAPICache` with `RedisBackend`.
  - `app/core/redis.py:10-12`: `Limiter(key_func=get_remote_address)` from `slowapi` for endpoint rate limiting.
- **Broken Import in Cache Service (`app/services/cache_service.py:2`)**:
  - `from app.core.redis import redis_client`
  - In `app/core/redis.py`, `redis_client` is a local variable inside `init_redis(app: FastAPI)` and is not exported at the module level. Any call to `app.services.cache_service` raises `ImportError: cannot import name 'redis_client' from 'app.core.redis'`.
- **Audio / TTS Caching (`uzbek_tts.py`)**:
  - `uzbek_tts.py:17-18, 95-99`: Uses disk-based caching in `data/audio_cache/tts_{hash}.ogg` via MD5 text hashing and pre-warming (`preload_models()`). While functional on persistent filesystems, containerized serverless deployments (Render/Koyeb) have ephemeral disks where persistent Redis binary caching provides faster, permanent audio reuse.

### 1.5 Environment Variables & Configuration Audit
- `.env.example` & `.env`:
  - Contains outdated MySQL settings (`DB_CONNECTION=mysql`, `DB_PORT=3306`, `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`, `DB_USERNAME=tozalash_user`, `DB_PASSWORD=tozalash_password`).
  - Contains basic `REDIS_URL=redis://localhost:6379/0` and `REDIS_PASSWORD=`.
  - Missing standard cloud variables: `DATABASE_URL` (Supabase / Neon DSN), `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `DB_SSL`, `DB_POOL_MIN`, `DB_POOL_MAX`.
- `render.yaml:17-29`: Configures `DB_TYPE=postgres`, `DB_PORT=5432`, `DB_HOST`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE`, and `REDIS_URL`.

---

## 2. Logic Chain

From the direct observations above, we establish the following structured deduction:

```
[Observation 1.1] database.py uses individual DB_HOST/PORT/USER/PASSWORD env vars with ssl=None & pool 5-30
       ↓
[Logic Step 1] Cloud Managed PostgreSQL 16 (Supabase / Neon) provides single connection URIs (DATABASE_URL) mandating SSL (sslmode=require) and limited connections (15-20 max on Free Tier).
       ↓
[Deduction 1] Without DATABASE_URL parsing and ssl="require" parameterization, connecting database.py to Supabase or Neon fails at pool creation. Furthermore, Supabase transaction pooler (port 6543) requires statement_cache_size=0.

[Observation 1.2] app/api/endpoints/clients.py, orders.py, staff.py use "async with conn.cursor() as cursor" & "%s"
       ↓
[Logic Step 2] Neither asyncpg.Connection nor database.py Database class implements .cursor(). Unified query execution must use db.fetch_all(), db.fetch_one(), or db.execute().
       ↓
[Deduction 2] Invoking /api/v1/clients, /api/v1/orders, or /api/v1/staff on either SQLite or PostgreSQL triggers an unhandled AttributeError and 500 Internal Server Error.

[Observation 1.3] migrations/ has 9 MySQL SQL files, alembic/versions/ is empty, and database.py creates only 8 tables
       ↓
[Logic Step 3] Business logic in bot/admin_handlers.py, workers/workers_manager.py, and reports/daily_reports.py requires tables like finance, channel_posts, competitors, daily_reports, cities, services, and order_workers.
       ↓
[Deduction 3] A complete schema covering all 18 tables with PostgreSQL 16 compatible DDL and B-Tree indexes is required during database.py initialization to prevent missing-table query exceptions.

[Observation 1.4] Upstash Redis uses "rediss://" (TLS) and terminates idle connections after 60-120 seconds
       ↓
[Logic Step 4] Standard redis.asyncio ConnectionPool requires health_check_interval=30 and retry_on_timeout=True to maintain healthy keepalive connections and prevent broken socket errors after idle periods.
       ↓
[Deduction 4] Configuring RedisManager and FastAPICache with retry parameters and non-blocking in-memory fallback guarantees 24/7 uptime without container crashes during serverless cold starts.
```

---

## 3. Caveats

1. **Active Database Selection in Development vs Production**:
   - In local development without PostgreSQL running, `database.py` seamlessly falls back to SQLite WAL mode (`tozalash.db`), which allows full offline development.
   - Any modifications for PostgreSQL 16 must strictly preserve this zero-configuration SQLite fallback so local developer workflows and automated unit tests remain 100% operational.
2. **Supabase Direct Port (5432) vs Pooled Port (6543)**:
   - Supabase provides two connection strings: Direct (`port 5432`) for persistent session connections and Supavisor/PgBouncer (`port 6543`) for transaction-level pooling.
   - When deploying to Koyeb/Render web services where multiple workers connect to Supabase, `port 6543` (transaction pooling) is recommended to prevent connection exhaustion. In this mode, `statement_cache_size=0` **must** be enforced in `asyncpg`.
3. **GeoAlchemy2 & PostGIS**:
   - `app/models/geo.py` uses `geoalchemy2.Geometry`. If PostGIS extension is not installed in the target database (`CREATE EXTENSION IF NOT EXISTS postgis;`), raw `lat` and `lon` float columns must serve as the fallback representation.

---

## 4. Conclusion

The application architecture has a solid foundation for enterprise operations, featuring an async database engine (`database.py`), an async Redis manager with distributed locking and in-memory fallbacks (`redis_manager.py`), and FastAPI microservices.

However, full integration with Managed PostgreSQL 16 (Supabase / Neon) and Serverless Redis 7 (Upstash) in Milestone 2 requires resolving five distinct categories of issues:

1. **Connection String & SSL Compatibility**:
   - Enable `database.py` to parse `DATABASE_URL` (accepting `postgresql://...` and `postgres://...`).
   - Pass `ssl="require"` when SSL mode is indicated or connecting to remote cloud hosts.
   - Set `statement_cache_size=0` on `asyncpg.create_pool` to support Supabase/PgBouncer transaction pooling (port 6543).
   - Adjust default pool sizing for free cloud tiers (`min_size=1, max_size=5`).
2. **Schema & Table Completeness**:
   - Expand `_create_tables_and_indexes()` in `database.py` to cover all 18 tables using valid PostgreSQL 16 DDL (`SERIAL PRIMARY KEY`, `VARCHAR`, `TEXT`, `NUMERIC(14,2)`, `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, `BOOLEAN`, `JSONB`) and corresponding SQLite DDL.
   - Restore missing business query methods in `database.py` (`get_orders_stats`, `get_finance_stats`, `get_today_orders`, `get_all_workers`, `get_available_workers`, `add_worker`, `register_worker`, `get_worker_by_tg_id`, `get_messages_count_today`, `get_successful_patterns`, etc.).
3. **FastAPI Endpoint Query Refactoring**:
   - Clean up `app/api/endpoints/clients.py`, `orders.py`, `staff.py`, and `analytics/chart_generator.py` by removing broken `async with conn.cursor()` constructs and replacing them with `await db.fetch_all(...)`, `await db.fetch_one(...)`, and `await db.execute(...)`.
4. **Serverless Redis 7 (Upstash) Hardening**:
   - Update `app/core/redis_manager.py` connection pool with `health_check_interval=30` and `retry_on_timeout=True`.
   - In `app/core/redis.py`, wrap `init_redis` in a `try...except` block with `InMemoryBackend` fallback so temporary Redis unavailability during serverless cold starts never crashes the FastAPI server.
   - Fix `app/services/cache_service.py` by importing from `app.core.redis_manager` instead of the non-existent module-level `redis_client`.
5. **Configuration & Health Check Enhancement**:
   - Clean up `.env.example` and `app/core/config.py` by adding `DATABASE_URL`, `REDIS_URL`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `DB_SSL`, `DB_POOL_MIN`, `DB_POOL_MAX`.
   - Update `/health` endpoint in `app/main.py` to perform active ping verification against DB (`SELECT 1`) and Redis (`redis_manager.client.ping()`).

---

## 5. Verification Method

To independently verify all findings and test subsequent implementation changes for Milestone 2, execute the following commands and checks:

### 5.1 Static Verification of Code Locations & Imports
```powershell
# 1. Verify broken cursor usage in API endpoints
Select-String -Path "app\api\endpoints\*.py" -Pattern "conn\.cursor\(\)"

# 2. Verify broken redis_client import in cache_service
Select-String -Path "app\services\cache_service.py" -Pattern "from app\.core\.redis import redis_client"

# 3. Verify missing methods in database.py
Select-String -Path "database.py" -Pattern "def get_orders_stats|def get_all_workers|def get_finance_stats"
```

### 5.2 Test Execution (Local SQLite & In-Memory Redis)
```powershell
# Run the complete test suite to verify baseline functionality
pytest -v tests/test_enterprise_database.py tests/test_redis_fsm.py tests/test_core_config_security.py
```

### 5.3 Cloud PostgreSQL 16 & Upstash Verification Matrix
Once implemented in Milestone 2, verify against live cloud instances using the following test matrix:

| Target Service | Connection String Pattern | Expected Result | Verification Check |
|---|---|---|---|
| **Supabase Direct** | `postgresql://postgres:pwd@db.xxxx.supabase.co:5432/postgres?sslmode=require` | Connection established, pool 1-5 | `await db.init_db()` logs `PostgreSQL 16 ulandi` |
| **Supabase Pooled** | `postgresql://postgres.xxxx:pwd@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require` | Connection established with `statement_cache_size=0` | Execute repeated parameterized queries without prepared statement collisions |
| **Neon Serverless** | `postgresql://user:pwd@ep-xxxx-pooler.region.neon.tech/neondb?sslmode=require` | Connection established with TLS | `await db.fetch_one("SELECT 1 as alive")` returns `{"alive": 1}` |
| **Upstash Redis** | `rediss://default:token@region.upstash.io:6379` | TLS ping success, FSM & Redlock operational | `pytest -v tests/test_redis_fsm.py` with `REDIS_URL` set |
| **SQLite Fallback** | *(No DB_HOST / DB_TYPE=sqlite)* | Instant fallback to `tozalash.db` WAL mode | Logs `SQLite WAL High-Performance rejimi tayyor` |

---
*Report compiled and verified by Survey Explorer 2. Ready for Milestone 2 implementation planning.*
