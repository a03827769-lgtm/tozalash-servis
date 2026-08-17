# Handoff Report — Schema Migration 005 Gap Fix Investigation

## 1. Observation

Direct investigation of `migrations/`, `migrations_runner.py`, `database.py`, `app/models/`, `workers/workers_manager.py`, and related modules revealed the following exact observations:

1. **Missing Migration File Sequence Gap**:
   - `migrations/` directory listing (`find_by_name`): `001_initial.sql`, `002_add_indexes_and_fixes.sql`, `003_multi_city_and_payments.sql`, `004_normalize_workers.sql`, `006_rbac_roles.sql`, `007_add_referral_to_orders.sql`, `008_add_foreign_keys_and_json.sql`, `009_gamification_and_ratings.sql`.
   - **Observation**: File `005_*.sql` is completely missing. `migrations_runner.py` sorts `.sql` files (`sql_files = sorted(...)`) and records versions in `schema_migrations` table, leaving a numerical gap between `004` and `006`.

2. **Column Gaps in `clients` Table**:
   - `database.py` lines 169-187 defines `_CLIENT_UPDATABLE_COLUMNS`:
     ```python
     _CLIENT_UPDATABLE_COLUMNS = frozenset({
         "name", "language", "phone", "address", "is_blocked", "loyalty_points",
         "total_orders", "total_spent", "last_activity", "churn_risk", "gender",
         "referral_code", "referred_by", "notes", "notification_enabled"
     })
     ```
   - Inspection of SQL migration files `001` through `009` shows that `clients` table schema does NOT contain:
     - `address`
     - `is_blocked`
     - `gender`
     - `notification_enabled`
   - In `userbot/main_userbot.py` line 85:
     `await db.update_client(telegram_id, gold_status_notified=True)`
     While `gold_status_notified` exists in `001_initial.sql` line 18, it is missing from `_CLIENT_UPDATABLE_COLUMNS` whitelist in `database.py` line 169. This causes `update_client()` to reject updates for `gold_status_notified` with a warning (`update_client: hech qanday yaroqli ustun topilmadi`).

3. **Missing DDL for Application Models**:
   - `app/models/order.py` line 29 defines `OrderArchive` (`__tablename__ = "orders_archive"`). Used by Celery archiving worker `app/workers/archiving.py`.
   - `app/models/audit.py` line 13 defines `AuditLog` (`__tablename__ = "audit_logs"`).
   - `app/models/geo.py` line 7 defines `WorkerLocation` (`__tablename__ = "worker_locations"`).
   - **Observation**: None of the migration files `001` through `009` create `orders_archive`, `audit_logs`, or `worker_locations` tables in MySQL.

4. **Column & Query Mismatches**:
   - `009_gamification_and_ratings.sql` lines 25-32 creates `competitor_prices` with `detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`.
   - `database.py` line 582 executes:
     `SELECT * FROM competitor_prices WHERE service_name = %s ORDER BY created_at DESC`
     Querying `created_at` against a table with `detected_at` results in MySQL Error `1054: Unknown column 'created_at' in 'order clause'`. `PROJECT.md` Feature 2 specifically calls for aligning `competitor_prices` (`detected_at`).
   - `workers/workers_manager.py` line 258 executes:
     `SELECT telegram_id, service_type, created_at FROM orders WHERE status='completed' ...`
     In `orders` table (`001_initial.sql` line 26), the client Telegram ID column is named `client_telegram_id`, not `telegram_id`.

---

## 2. Logic Chain

1. **Observation 1** demonstrates that migration `005` was omitted from the `migrations/` sequence. Filling this gap with `005_fix_schema_gaps.sql` restores numerical continuity and ensures `migrations_runner.py` applies schema fixes seamlessly during DB initialization.
2. **Observation 2** shows that `database.py`'s `update_client()` method accepts `address`, `is_blocked`, `gender`, and `notification_enabled`, but queries against `clients` will fail if these columns do not exist in MySQL. Furthermore, `gold_status_notified`, `loyalty_coins`, `city_id`, and `role` need to be allowed in `_CLIENT_UPDATABLE_COLUMNS`.
3. **Observation 3** proves that SQLAlchemy models (`OrderArchive`, `AuditLog`, `WorkerLocation`) and background archiving tasks will fail at runtime because their corresponding tables (`orders_archive`, `audit_logs`, `worker_locations`) were never created in MySQL migrations.
4. **Observation 4** indicates runtime SQL exceptions due to column mismatches (`created_at` vs `detected_at` in `competitor_prices`, `telegram_id` vs `client_telegram_id` in `orders`).
5. **Conclusion**: Designing `005_fix_schema_gaps.sql` with idempotent `ALTER TABLE` and `CREATE TABLE IF NOT EXISTS` statements, along with specific python adjustments for `database.py` and `workers_manager.py`, resolves all identified database layer defects.

---

## 3. Caveats

- `migrations_runner.py` uses `aiomysql` and splits SQL files by `;`. Statements must end with `;` and be standard MySQL queries. MySQL safe error codes (1060 for duplicate column, 1050 for table exists, 1061 for duplicate key) are ignored by `migrations_runner.py`, making the script idempotent.
- SQLite-to-MySQL legacy script (`archive_scripts/migrate_sqlite_to_mysql.py`) contains historical table names, but `database.py` and active application components rely exclusively on `aiomysql` and the migration files in `migrations/`.

---

## 4. Conclusion

### Proposed Design for `migrations/005_fix_schema_gaps.sql`:

```sql
-- Migration 005: Fix Schema Gaps, Missing Columns, Missing Tables and Index Optimizations
-- Note: Duplikat column (1060), table already exists (1050), duplicate index (1061) xatolari
-- migrations_runner.py tomonidan xavfsiz ravishda o'tkazib yuboriladi.

-- 1. Add missing columns to clients table (referenced in database.py _CLIENT_UPDATABLE_COLUMNS)
ALTER TABLE clients ADD COLUMN address TEXT DEFAULT NULL;
ALTER TABLE clients ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE;
ALTER TABLE clients ADD COLUMN gender VARCHAR(20) DEFAULT NULL;
ALTER TABLE clients ADD COLUMN notification_enabled BOOLEAN DEFAULT TRUE;

-- 2. Create competitor_prices table (if not created yet) and ensure both detected_at and created_at exist
CREATE TABLE IF NOT EXISTS competitor_prices (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    competitor_name VARCHAR(100) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_url VARCHAR(255)
);

ALTER TABLE competitor_prices ADD COLUMN detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE competitor_prices ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 3. Create missing tables defined in app/models (orders_archive, audit_logs, worker_locations)
CREATE TABLE IF NOT EXISTS orders_archive (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    original_id INTEGER NOT NULL,
    amount DOUBLE,
    status INTEGER,
    client_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_orders_archive_original_id (original_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NULL,
    action VARCHAR(50) NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    entity_id INTEGER NOT NULL,
    changes JSON,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_entity (entity_name, entity_id)
);

CREATE TABLE IF NOT EXISTS worker_locations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    worker_id INTEGER NOT NULL,
    name VARCHAR(255),
    lat DOUBLE,
    lon DOUBLE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_worker_locations_worker_id (worker_id)
);

-- 4. Add missing index optimizations
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_city_id ON orders(city_id);
CREATE INDEX idx_workers_active_available ON workers(is_active, is_available, rating);
CREATE INDEX idx_clients_city_id ON clients(city_id);
CREATE INDEX idx_clients_referred_by ON clients(referred_by);
```

### Accompanying Recommendations for Code Fixes (for Worker):

1. **`database.py` (`_CLIENT_UPDATABLE_COLUMNS`)**:
   Add `"gold_status_notified"`, `"loyalty_coins"`, `"city_id"`, and `"role"` to `_CLIENT_UPDATABLE_COLUMNS` whitelist so that `update_client()` can update these fields without error.

2. **`database.py` (`get_competitor_prices`)**:
   Update line 582 to query `ORDER BY detected_at DESC, created_at DESC`.

3. **`workers/workers_manager.py` (`run_predictive_maintenance`)**:
   Update line 258 SQL query from `SELECT telegram_id...` to `SELECT client_telegram_id AS telegram_id, service_type, created_at FROM orders...`.

---

## 5. Verification Method

1. **Inspect Migration File**:
   Check that `migrations/005_fix_schema_gaps.sql` exists and contains valid MySQL DDL statements.

2. **Run Migrations Test**:
   Execute `python -c "import asyncio; from database import db; asyncio.run(db.init_db())"` (when MySQL container is available) to verify that `migrations_runner.py` executes `001` through `009` without errors.

3. **Database Verification Query**:
   Inspect MySQL schema using `DESCRIBE clients;`, `DESCRIBE competitor_prices;`, `SHOW TABLES;` to verify columns (`address`, `is_blocked`, `gender`, `notification_enabled`, `detected_at`, `created_at`) and tables (`orders_archive`, `audit_logs`, `worker_locations`) exist.
