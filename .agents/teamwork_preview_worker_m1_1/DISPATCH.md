## 2026-08-13T17:51:46Z

<USER_REQUEST>
Identity: teamwork_preview_worker_m1_1
Role: Worker - M1 Core Infrastructure & Database Layer Refactoring
Working directory: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\teamwork_preview_worker_m1_1

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Task Assignment:
Implement all code modifications and schema fixes for Milestone M1 (Core Infrastructure & Database Layer).

Input Documents to Read:
1. ORIGINAL_REQUEST.md: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\ORIGINAL_REQUEST.md
2. PROJECT.md: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\PROJECT.md
3. M1 Explorer 1 Handoff Report: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\teamwork_preview_explorer_m1_1\handoff.md
4. M1 Explorer 2 Handoff Report: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\teamwork_preview_explorer_m1_2\handoff.md
5. M1 Explorer 3 Handoff Report: C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\teamwork_preview_explorer_m1_3\handoff.md

File Ownership (you exclusively own these files for this milestone):
- app/core/config.py
- config.py
- .env
- database.py
- ws_server.py
- migrations/005_fix_schema_gaps.sql
- workers/workers_manager.py

Implementation Tasks:
1. Config Consolidation & Backward Compatibility:
   - Update app/core/config.py with unified Pydantic Settings BaseSettings class covering all project environment variables (MySQL DB, Telegram, Gemini, Voice, Sheets, Instagram, Security, Business).
   - Update config.py to import settings from app.core.config and re-export top-level constants to preserve 100% backward compatibility for existing imports.
   - Refactor validate_config() in config.py to support non-blocking execution (returning status, logging warnings via loguru), auto-generating hex fallback key for JWT_SECRET_KEY in dev mode, and raising ValueError only when explicitly requested (strict=True or raise_on_error=True).
   - Clean up .env by removing duplicate WS_AUTH_TOKEN line 117.

2. Database Pool Lazy Lock & Schema Query Alignment:
   - In database.py, replace import-time self._lock = asyncio.Lock() with self._lock = None and @property def lock(self) -> asyncio.Lock: lazy initialization.
   - Update database.py get_competitor_prices line 582 to sort by ORDER BY detected_at DESC, created_at DESC.
   - Update database.py _CLIENT_UPDATABLE_COLUMNS to include "gold_status_notified", "loyalty_coins", "city_id", "role", "address", "is_blocked", "gender", "notification_enabled".
   - In ws_server.py line 264 (/health endpoint), replace db.pool.acquire() with async with db.get_conn() to safely handle uninitialized pools.
   - In workers/workers_manager.py line 258, update query from telegram_id to client_telegram_id AS telegram_id.

3. Schema Migration 005 Gap Fix:
   - Create migrations/005_fix_schema_gaps.sql containing idempotent DDL statements (ALTER TABLE clients ADD COLUMN ..., CREATE TABLE IF NOT EXISTS competitor_prices, orders_archive, audit_logs, worker_locations, and missing indexes).

Verification & Verification Report:
- Run syntax compilation checks (python -m py_compile database.py config.py ws_server.py app/core/config.py).
- Run pytest tests/ (or python -m pytest tests/test_core_config_security.py tests/test_core.py) to verify that tests pass.
- Deliver handoff report at C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\.agents\teamwork_preview_worker_m1_1\handoff.md detailing implemented changes, build/test commands executed, and verification output.
- Send completion message to parent.
</USER_REQUEST>
