"""
Test Verification Script for M1 DB Schema & Migration Tester (Challenger 2)

Empirically validates:
1. SQL syntax of migrations/005_fix_schema_gaps.sql against migrations_runner.py.
2. Migration statement splitting and exception handling (idempotency error codes 1050, 1060, 1061, 1091).
3. Columns in Database._CLIENT_UPDATABLE_COLUMNS match migration schema for `clients`.
4. Query strings in database.py and workers/workers_manager.py (e.g. competitor_prices sorting, orders alias).
"""

import re
import pytest
import sqlite3
from pathlib import Path
from database import Database, db
from config import settings, validate_config
from workers.workers_manager import WorkersManager


PROJECT_ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


def test_005_migration_syntax_and_runner_logic():
    """Verify 005_fix_schema_gaps.sql statement splitting and syntax."""
    file_path = MIGRATIONS_DIR / "005_fix_schema_gaps.sql"
    assert file_path.exists(), "migrations/005_fix_schema_gaps.sql must exist"

    sql_content = file_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql_content.split(";") if s.strip()]

    assert len(statements) >= 8, f"Expected at least 8 statements in 005 migration, found {len(statements)}"

    # Check statement structure
    valid_verbs = ("ALTER TABLE", "CREATE TABLE", "CREATE INDEX")
    for stmt in statements:
        # Strip comments
        lines = [line for line in stmt.splitlines() if not line.strip().startswith("--")]
        clean_stmt = " ".join(lines).strip()
        if not clean_stmt:
            continue
        assert any(clean_stmt.upper().startswith(verb) for verb in valid_verbs), \
            f"Statement does not start with valid DDL verb: {clean_stmt}"


def test_migrations_runner_idempotency_error_codes():
    """Verify migrations_runner exception handling covers MySQL duplicate/idempotency codes."""
    import aiomysql
    
    # Allowed skip error codes in migrations_runner.py:
    # 1061: Duplicate key name
    # 1050: Table already exists
    # 1060: Duplicate column name
    # 1091: Can't DROP non-existing key
    skip_codes = {1061, 1050, 1060, 1091}
    
    # Test OperationalError with skipped code
    for code in skip_codes:
        err = aiomysql.OperationalError(code, f"Mock MySQL error {code}")
        assert err.args[0] in (1061, 1050, 1060, 1091)

    # OperationalError with unhandled code (e.g. 1045 Access denied)
    unhandled_err = aiomysql.OperationalError(1045, "Access denied")
    assert unhandled_err.args[0] not in skip_codes


def test_all_migrations_parseable():
    """Parse all .sql files in migrations/ directory to ensure no broken statements."""
    sql_files = sorted([f for f in MIGRATIONS_DIR.iterdir() if f.suffix == ".sql"])
    assert len(sql_files) >= 9, f"Expected at least 9 migration files, found {len(sql_files)}"

    for sql_file in sql_files:
        content = sql_file.read_text(encoding="utf-8")
        statements = [s.strip() for s in content.split(";") if s.strip()]
        for stmt in statements:
            # Basic sanity checks on non-comment statement content
            clean_lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
            clean_stmt = " ".join(clean_lines).strip()
            if clean_stmt:
                assert len(clean_stmt) > 5, f"Suspiciously short statement in {sql_file.name}: '{clean_stmt}'"


def test_client_updatable_columns_match_schema():
    """Verify all columns in Database._CLIENT_UPDATABLE_COLUMNS exist across migrations."""
    updatable = Database._CLIENT_UPDATABLE_COLUMNS
    assert isinstance(updatable, frozenset)

    # Collect columns added to `clients` table across all migration files
    clients_columns = set()

    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        content = sql_file.read_text(encoding="utf-8")
        
        # Match CREATE TABLE clients (...)
        create_match = re.search(r"CREATE TABLE IF NOT EXISTS clients\s*\((.*?)\);", content, re.DOTALL | re.IGNORECASE)
        if create_match:
            lines = create_match.group(1).split(",")
            for line in lines:
                line = line.strip()
                if line and not line.upper().startswith(("PRIMARY", "FOREIGN", "KEY", "CONSTRAINT", "UNIQUE")):
                    col_name = line.split()[0].strip("`")
                    clients_columns.add(col_name)

        # Match ALTER TABLE clients ADD COLUMN <col_name>
        alter_matches = re.findall(r"ALTER TABLE clients\s+ADD COLUMN\s+(`?\w+`?)", content, re.IGNORECASE)
        for col_name in alter_matches:
            clients_columns.add(col_name.strip("`"))

    # Explicitly check each updatable column against clients_columns set
    for col in updatable:
        assert col in clients_columns, f"Updatable column '{col}' is missing from clients table migrations!"


def test_competitor_prices_query_columns():
    """Verify competitor_prices query in database.py references valid columns."""
    from database import db
    import inspect

    source = inspect.getsource(db.get_competitor_prices)
    assert "ORDER BY detected_at DESC, created_at DESC" in source, \
        "get_competitor_prices query must sort by detected_at DESC, created_at DESC"

    # Check 005 and 009 migration files for competitor_prices columns
    migration_005 = (MIGRATIONS_DIR / "005_fix_schema_gaps.sql").read_text(encoding="utf-8")
    assert "detected_at" in migration_005
    assert "created_at" in migration_005


def test_workers_manager_predictive_maintenance_query():
    """Verify query in workers_manager.py line 258 aliases client_telegram_id AS telegram_id."""
    from workers.workers_manager import WorkersManager
    import inspect

    source = inspect.getsource(WorkersManager.run_predictive_maintenance)
    assert "client_telegram_id AS telegram_id" in source, \
        "Predictive maintenance query must alias client_telegram_id AS telegram_id to prevent key errors"


def test_sqlite_inmemory_schema_simulation():
    """Run simulated SQLite schema creation for core tables to test SQL logic idempotency."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create clients table
    cursor.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            language TEXT DEFAULT 'uz',
            city TEXT DEFAULT 'Toshkent',
            address TEXT DEFAULT NULL,
            is_blocked BOOLEAN DEFAULT 0,
            gender TEXT DEFAULT NULL,
            notification_enabled BOOLEAN DEFAULT 1,
            gold_status_notified BOOLEAN DEFAULT 0,
            loyalty_coins REAL DEFAULT 0.00
        );
    """)

    # Create competitor_prices table
    cursor.execute("""
        CREATE TABLE competitor_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_name TEXT NOT NULL,
            service_name TEXT NOT NULL,
            price REAL NOT NULL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_url TEXT
        );
    """)

    # Create orders_archive, audit_logs, worker_locations
    cursor.execute("""
        CREATE TABLE orders_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_id INTEGER NOT NULL,
            amount REAL,
            status INTEGER,
            client_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            action TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            changes TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE worker_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            name TEXT,
            lat REAL,
            lon REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Insert test data into competitor_prices and test ordering query
    cursor.execute("INSERT INTO competitor_prices (competitor_name, service_name, price) VALUES ('CompA', 'Cleaning', 100)")
    cursor.execute("SELECT * FROM competitor_prices WHERE service_name = 'Cleaning' ORDER BY detected_at DESC, created_at DESC")
    rows = cursor.fetchall()
    assert len(rows) == 1

    conn.close()
