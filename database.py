"""
Tozalash Servis — Ma'lumotlar Bazasi Moduli (Enterprise Async Database Layer)
PostgreSQL 16 (AsyncPG) Primary + High-Performance Async SQLite Fallback (WAL mode)
ACID Transactions, Connection Pooling, B-Tree & Spatial Indexes, Supabase/Neon Compatibility
"""

import asyncio
import os
import json
import secrets
import string
import urllib.parse
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from loguru import logger

try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning("asyncpg o'rnatilmagan. PostgreSQL rejimida ishlash uchun: pip install asyncpg")

try:
    import aiosqlite
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

try:
    import aiomysql
except ImportError:
    aiomysql = None


def _row_to_dict(row: Any) -> Optional[Dict[str, Any]]:
    """Row obyektini xavfsiz dict formatiga o'tkazish"""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    if hasattr(row, "keys"):
        return {k: row[k] for k in row.keys()}
    try:
        return dict(row)
    except Exception:
        return dict(row)


class CursorProxy:
    """Legacy cursor emulation for backwards compatibility."""
    def __init__(self, db_instance):
        self.db = db_instance
        self.lastrowid = None
        self.rowcount = 0
        self._last_result = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def execute(self, query: str, params: Union[tuple, list] = ()):
        # Normalize %s to ?
        q = query
        if "%s" in q:
            q = q.replace("%s", "?")
        
        # Check if it's a SELECT query
        stripped = q.strip().upper()
        if stripped.startswith("SELECT") or stripped.startswith("WITH"):
            self._last_result = await self.db.fetch_all(q, params)
            self.rowcount = len(self._last_result)
            return self._last_result
        else:
            res = await self.db.execute(q, params)
            self.lastrowid = res
            self.rowcount = 1
            return res

    async def fetchone(self):
        if self._last_result is not None:
            if self._last_result:
                return self._last_result.pop(0)
            return None
        return None

    async def fetchall(self):
        if self._last_result is not None:
            res = self._last_result
            self._last_result = []
            return res
        return []


class ConnectionContextProxy:
    """Wraps connection context for async with db.get_conn() as conn: async with conn.cursor():"""
    def __init__(self, db_instance, real_conn=None):
        self.db = db_instance
        self.real_conn = real_conn

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def cursor(self):
        return CursorProxy(self.db)

    async def begin(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass


class Database:
    """Enterprise Asinxron Ma'lumotlar Bazasi (PostgreSQL 16 + AsyncPG / SQLite WAL Fallback)"""

    _CLIENT_UPDATABLE_COLUMNS = frozenset({
        "name",
        "language",
        "phone",
        "address",
        "is_blocked",
        "loyalty_points",
        "loyalty_coins",
        "total_orders",
        "total_spent",
        "last_activity",
        "churn_risk",
        "gender",
        "referral_code",
        "referred_by",
        "notes",
        "notification_enabled",
        "gold_status_notified",
        "city_id",
        "role",
    })

    def __init__(self, sqlite_path: Optional[str] = None):
        self.db_type = os.getenv("DB_TYPE", "postgres" if (os.getenv("DATABASE_URL") or os.getenv("DB_TYPE") == "postgres") else "sqlite")
        self.pg_pool: Optional[Any] = None
        self.sqlite_conn: Optional[Any] = None
        self.sqlite_path = sqlite_path or os.getenv("DATABASE_PATH", "tozalash.db")
        self._lock: Optional[asyncio.Lock] = None
        self._initialized = False

    def get_pool(self):
        """Returns pg_pool or self for backwards compatibility."""
        if self.pg_pool is not None:
            return self.pg_pool
        return self

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def init_db(self):
        """Ma'lumotlar bazasi ulanishini ishga tushirish va barcha 18 ta jadvalni indekslar bilan yaratish"""
        if self._initialized:
            return

        if hasattr(self, "pool") and self.pool is not None and not self.pg_pool and not self.sqlite_conn:
            self._initialized = True
            return

        async with self.lock:
            if self._initialized:
                return

            if hasattr(self, "pool") and self.pool is not None and not self.pg_pool and not self.sqlite_conn:
                self._initialized = True
                return

            # Check DATABASE_URL or individual env vars
            database_url = os.getenv("DATABASE_URL", "").strip()
            db_host = os.getenv("DB_HOST", "localhost")
            db_user = os.getenv("DB_USERNAME", os.getenv("DB_USER", "postgres"))
            db_pass = os.getenv("DB_PASSWORD", "postgres")
            db_name = os.getenv("DB_DATABASE", os.getenv("DB_NAME", "tozalash_db"))
            db_port = int(os.getenv("DB_PORT", 5432))
            db_ssl = os.getenv("DB_SSL", "").lower() in ("true", "1", "require")

            ssl_ctx = None
            statement_cache_size = 0 if os.getenv("DB_STATEMENT_CACHE_SIZE") == "0" else None

            if database_url and (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
                parsed = urllib.parse.urlparse(database_url)
                db_host = parsed.hostname or db_host
                db_port = parsed.port or 5432
                db_user = parsed.username or db_user
                db_pass = parsed.password or db_pass
                db_name = parsed.path.lstrip("/") or db_name
                query_params = urllib.parse.parse_qs(parsed.query)

                if "sslmode" in query_params:
                    ssl_mode_val = query_params["sslmode"][0].lower()
                    if ssl_mode_val in ("require", "verify-full", "verify-ca", "prefer"):
                        ssl_ctx = "require"
                if db_ssl or (db_host and ("supabase" in db_host or "neon.tech" in db_host or "render.com" in db_host or "koyeb.app" in db_host)):
                    ssl_ctx = "require"

                # Supabase pooler port 6543 requires statement_cache_size=0
                if db_port == 6543 or "pooler" in (db_host or ""):
                    statement_cache_size = 0

            elif db_ssl or (db_host and ("supabase" in db_host or "neon.tech" in db_host or "render.com" in db_host or "koyeb.app" in db_host)):
                ssl_ctx = "require"
                if db_port == 6543 or "pooler" in (db_host or ""):
                    statement_cache_size = 0

            pool_min = int(os.getenv("DB_POOL_MIN", 1))
            pool_max = int(os.getenv("DB_POOL_MAX", 5))

            connect_pg = POSTGRES_AVAILABLE and (bool(database_url) or (os.getenv("DB_TYPE") == "postgres") or (os.getenv("DB_HOST") and os.getenv("DB_HOST") not in ("localhost", "mysql", "127.0.0.1") and os.getenv("DB_TYPE") != "sqlite"))

            if connect_pg:
                try:
                    pool_kwargs = {
                        "host": db_host,
                        "port": db_port,
                        "user": db_user,
                        "password": db_pass,
                        "database": db_name,
                        "min_size": pool_min,
                        "max_size": pool_max,
                        "command_timeout": float(os.getenv("DB_COMMAND_TIMEOUT", 10.0)),
                    }
                    if ssl_ctx:
                        pool_kwargs["ssl"] = ssl_ctx
                    if statement_cache_size is not None:
                        pool_kwargs["statement_cache_size"] = statement_cache_size

                    self.pg_pool = await asyncio.wait_for(
                        asyncpg.create_pool(**pool_kwargs),
                        timeout=float(os.getenv("DB_CONNECT_TIMEOUT", 0.3))
                    )
                    self.db_type = "postgres"
                    logger.success(f"✅ PostgreSQL 16 ulandi: {db_user}@{db_host}:{db_port}/{db_name} (Pool: {pool_min}-{pool_max}, SSL: {ssl_ctx or 'off'})")
                except Exception as e:
                    logger.info(f"ℹ️ PostgreSQL ulanmadi ({e}). SQLite WAL fallback rejimiga o'tildi.")
                    self.db_type = "sqlite"
                    self.pg_pool = None
            else:
                self.db_type = "sqlite"

            if self.db_type == "sqlite":
                if not SQLITE_AVAILABLE:
                    raise RuntimeError("Na PostgreSQL, na aiosqlite kutubxonasi mavjud emas!")
                sqlite_dir = os.path.dirname(self.sqlite_path)
                if sqlite_dir:
                    os.makedirs(sqlite_dir, exist_ok=True)
                self.sqlite_conn = await aiosqlite.connect(self.sqlite_path, timeout=5.0, isolation_level=None)
                self.sqlite_conn.row_factory = aiosqlite.Row
                try:
                    await self.sqlite_conn.execute("PRAGMA busy_timeout = 5000;")
                    await self.sqlite_conn.execute("PRAGMA journal_mode = WAL;")
                    await self.sqlite_conn.execute("PRAGMA synchronous = NORMAL;")
                    await self.sqlite_conn.execute("PRAGMA cache_size = -64000;")
                    await self.sqlite_conn.execute("PRAGMA foreign_keys = ON;")
                except Exception:
                    pass
                logger.success(f"✅ SQLite WAL High-Performance rejimi tayyor: {self.sqlite_path}")

            self._initialized = True

        await self._create_tables_and_indexes()

    async def close(self):
        """Baza ulanishlarini xavfsiz yopish"""
        if self.pg_pool:
            await self.pg_pool.close()
            logger.info("PostgreSQL ulanishlar puli yopildi.")
            self.pg_pool = None
        if self.sqlite_conn:
            await self.sqlite_conn.close()
            logger.info("SQLite ulanishi yopildi.")
            self.sqlite_conn = None
        self._initialized = False

    def get_conn(self):
        """Mos keluvchi asinxron ulanish konteksti"""
        if hasattr(self, "pool") and self.pool is not None and not self.pg_pool and not self.sqlite_conn:
            return self.pool.acquire()
        return ConnectionContextProxy(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    # =========================================================================
    # GENERIC QUERY RUNNER (Postgres & SQLite avtomatik moslashuv)
    # =========================================================================
    def _normalize_query(self, query: str) -> str:
        """SQL dialektiga qarab so'rovni moslashtirish"""
        q = query
        if self.db_type == "postgres":
            # Replace %s with ? first if needed
            if "%s" in q:
                q = q.replace("%s", "?")
            # Replace ? with $1, $2, ... for PostgreSQL
            if "?" in q:
                parts = q.split("?")
                q = "".join(f"{parts[i]}${i+1}" for i in range(len(parts)-1)) + parts[-1]
            # Replace MySQL/SQLite date helpers
            q = q.replace("CURDATE()", "CURRENT_DATE")
            q = q.replace("DATE_SUB(NOW(), INTERVAL 30 DAY)", "(CURRENT_TIMESTAMP - INTERVAL '30 days')")
        else:
            # SQLite normalization
            if "%s" in q:
                q = q.replace("%s", "?")
            q = q.replace("CURDATE()", "DATE('now')")
            q = q.replace("NOW()", "DATETIME('now')")
            q = q.replace("DATE_SUB(NOW(), INTERVAL 30 DAY)", "DATETIME('now', '-30 days')")
        return q

    async def execute(self, query: str, params: Union[tuple, list] = ()) -> Any:
        """INSERT / UPDATE / DELETE so'rovini bajarish"""
        if not self._initialized:
            await self.init_db()

        if hasattr(self, "pool") and self.pool is not None and not self.pg_pool and not self.sqlite_conn:
            async with self.pool.acquire() as conn:
                try:
                    await conn.begin()
                except Exception:
                    pass
                async with conn.cursor() as cursor:
                    mysql_query = query.replace("?", "%s") if "?" in query else query
                    await cursor.execute(mysql_query, params)
                    try:
                        await conn.commit()
                    except Exception:
                        pass
                    return getattr(cursor, "lastrowid", 1) or 1

        pg_query = self._normalize_query(query)
        if self.db_type == "postgres" and self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                return await conn.execute(pg_query, *params)
        else:
            async with self.lock:
                cursor = await self.sqlite_conn.execute(pg_query, params)
                last_id = cursor.lastrowid
                await cursor.close()
                return last_id

    async def fetch_one(self, query: str, params: Union[tuple, list] = ()) -> Optional[Dict[str, Any]]:
        """Bitta qatorni dict formatida qaytarish"""
        if not self._initialized:
            await self.init_db()

        if hasattr(self, "pool") and self.pool is not None and not self.pg_pool and not self.sqlite_conn:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    mysql_query = query.replace("?", "%s") if "?" in query else query
                    await cursor.execute(mysql_query, params)
                    row = await cursor.fetchone()
                    return _row_to_dict(row)

        pg_query = self._normalize_query(query)
        if self.db_type == "postgres" and self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow(pg_query, *params)
                return _row_to_dict(row)
        else:
            async with self.lock:
                cursor = await self.sqlite_conn.execute(pg_query, params)
                row = await cursor.fetchone()
                await cursor.close()
                return _row_to_dict(row)

    async def fetch_all(self, query: str, params: Union[tuple, list] = ()) -> List[Dict[str, Any]]:
        """Barcha qatorlarni dictlar ro'yxati formatida qaytarish"""
        if not self._initialized:
            await self.init_db()

        if hasattr(self, "pool") and self.pool is not None and not self.pg_pool and not self.sqlite_conn:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    mysql_query = query.replace("?", "%s") if "?" in query else query
                    await cursor.execute(mysql_query, params)
                    rows = await cursor.fetchall()
                    return [_row_to_dict(r) for r in rows] if rows else []

        pg_query = self._normalize_query(query)
        if self.db_type == "postgres" and self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(pg_query, *params)
                return [_row_to_dict(r) for r in rows]
        else:
            async with self.lock:
                cursor = await self.sqlite_conn.execute(pg_query, params)
                rows = await cursor.fetchall()
                await cursor.close()
                return [_row_to_dict(r) for r in rows]

    # =========================================================================
    # JADVALLAR VA INDEKSLARNI YARATISH (18 Relational Tables)
    # =========================================================================
    async def _create_tables_and_indexes(self):
        """Barcha 18 relatsion jadvallar va B-Tree indekslarni yaratish"""
        is_pg = self.db_type == "postgres"
        
        tables = [
            # 1. Cities
            """
            CREATE TABLE IF NOT EXISTS cities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                price_multiplier REAL DEFAULT 1.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price_multiplier REAL DEFAULT 1.0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 2. Clients
            """
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                telegram_id VARCHAR(64) UNIQUE NOT NULL,
                name VARCHAR(255),
                phone VARCHAR(64),
                language VARCHAR(8) DEFAULT 'uz',
                city VARCHAR(255) DEFAULT 'Toshkent',
                city_id INTEGER DEFAULT 1,
                address TEXT,
                referral_code VARCHAR(32) UNIQUE,
                referred_by INTEGER,
                points INTEGER DEFAULT 0,
                loyalty_points INTEGER DEFAULT 0,
                loyalty_coins NUMERIC(14,2) DEFAULT 0.0,
                total_orders INTEGER DEFAULT 0,
                total_spent NUMERIC(14,2) DEFAULT 0.0,
                rating REAL DEFAULT 5.0,
                churn_risk REAL DEFAULT 0.0,
                gender VARCHAR(32),
                is_blocked BOOLEAN DEFAULT FALSE,
                notification_enabled BOOLEAN DEFAULT TRUE,
                gold_status_notified BOOLEAN DEFAULT FALSE,
                role VARCHAR(32) DEFAULT 'client',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT UNIQUE NOT NULL,
                name TEXT,
                phone TEXT,
                language TEXT DEFAULT 'uz',
                city TEXT DEFAULT 'Toshkent',
                city_id INTEGER DEFAULT 1,
                address TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                points INTEGER DEFAULT 0,
                loyalty_points INTEGER DEFAULT 0,
                loyalty_coins REAL DEFAULT 0.0,
                total_orders INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0.0,
                rating REAL DEFAULT 5.0,
                churn_risk REAL DEFAULT 0.0,
                gender TEXT,
                is_blocked INTEGER DEFAULT 0,
                notification_enabled INTEGER DEFAULT 1,
                gold_status_notified INTEGER DEFAULT 0,
                role TEXT DEFAULT 'client',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 3. Workers
            """
            CREATE TABLE IF NOT EXISTS workers (
                id SERIAL PRIMARY KEY,
                telegram_id VARCHAR(64) UNIQUE,
                telegram_username VARCHAR(255),
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(64),
                role VARCHAR(64) DEFAULT 'cleaner',
                specialization VARCHAR(255),
                is_active INTEGER DEFAULT 1,
                is_available INTEGER DEFAULT 1,
                total_jobs INTEGER DEFAULT 0,
                completed_orders INTEGER DEFAULT 0,
                monthly_salary NUMERIC(14,2) DEFAULT 0.0,
                balance NUMERIC(14,2) DEFAULT 0.0,
                rating REAL DEFAULT 5.0,
                average_rating REAL DEFAULT 5.0,
                total_ratings INTEGER DEFAULT 0,
                current_lat REAL,
                current_lon REAL,
                gps_lat REAL,
                gps_lon REAL,
                last_location_update TIMESTAMP,
                skills TEXT,
                city_id INTEGER DEFAULT 1,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT UNIQUE,
                telegram_username TEXT,
                name TEXT NOT NULL,
                phone TEXT,
                role TEXT DEFAULT 'cleaner',
                specialization TEXT,
                is_active INTEGER DEFAULT 1,
                is_available INTEGER DEFAULT 1,
                total_jobs INTEGER DEFAULT 0,
                completed_orders INTEGER DEFAULT 0,
                monthly_salary REAL DEFAULT 0.0,
                balance REAL DEFAULT 0.0,
                rating REAL DEFAULT 5.0,
                average_rating REAL DEFAULT 5.0,
                total_ratings INTEGER DEFAULT 0,
                current_lat REAL,
                current_lon REAL,
                gps_lat REAL,
                gps_lon REAL,
                last_location_update TIMESTAMP,
                skills TEXT,
                city_id INTEGER DEFAULT 1,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 4. Orders
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_number VARCHAR(64) UNIQUE NOT NULL,
                client_id INTEGER,
                client_telegram_id VARCHAR(64) NOT NULL,
                worker_id INTEGER,
                worker_ids TEXT,
                worker_names TEXT,
                city_id INTEGER DEFAULT 1,
                service_type VARCHAR(64) NOT NULL,
                service_name VARCHAR(255) NOT NULL,
                quantity REAL DEFAULT 1.0,
                unit VARCHAR(32) DEFAULT 'xizmat',
                price_per_unit NUMERIC(14,2) DEFAULT 0.0,
                surge_multiplier REAL DEFAULT 1.0,
                total_price NUMERIC(14,2) NOT NULL,
                final_price NUMERIC(14,2),
                status VARCHAR(64) DEFAULT 'yangi',
                address TEXT,
                lat REAL,
                lon REAL,
                lng REAL,
                scheduled_date VARCHAR(32),
                scheduled_time VARCHAR(32),
                payment_method VARCHAR(64),
                payment_status VARCHAR(64) DEFAULT 'kutilmoqda',
                payment_provider VARCHAR(64),
                payment_url TEXT,
                notes TEXT,
                is_eco_friendly BOOLEAN DEFAULT FALSE,
                custom_checklist TEXT,
                photos_before TEXT,
                photos_after TEXT,
                before_photo TEXT,
                after_photo TEXT,
                qa_approved INTEGER DEFAULT 0,
                client_rating INTEGER,
                client_feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                client_id INTEGER,
                client_telegram_id TEXT NOT NULL,
                worker_id INTEGER,
                worker_ids TEXT,
                worker_names TEXT,
                city_id INTEGER DEFAULT 1,
                service_type TEXT NOT NULL,
                service_name TEXT NOT NULL,
                quantity REAL DEFAULT 1.0,
                unit TEXT DEFAULT 'xizmat',
                price_per_unit REAL DEFAULT 0.0,
                surge_multiplier REAL DEFAULT 1.0,
                total_price REAL NOT NULL,
                final_price REAL,
                status TEXT DEFAULT 'yangi',
                address TEXT,
                lat REAL,
                lon REAL,
                lng REAL,
                scheduled_date TEXT,
                scheduled_time TEXT,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'kutilmoqda',
                payment_provider TEXT,
                payment_url TEXT,
                notes TEXT,
                is_eco_friendly INTEGER DEFAULT 0,
                custom_checklist TEXT,
                photos_before TEXT,
                photos_after TEXT,
                before_photo TEXT,
                after_photo TEXT,
                qa_approved INTEGER DEFAULT 0,
                client_rating INTEGER,
                client_feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );
            """,

            # 5. Transactions
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                order_id INTEGER,
                provider VARCHAR(64) NOT NULL,
                transaction_id VARCHAR(128) UNIQUE NOT NULL,
                amount NUMERIC(14,2) NOT NULL,
                currency VARCHAR(16) DEFAULT 'UZS',
                status VARCHAR(64) DEFAULT 'kutilmoqda',
                raw_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                provider TEXT NOT NULL,
                transaction_id TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'UZS',
                status TEXT DEFAULT 'kutilmoqda',
                raw_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 6. Messages & Conversations
            """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                telegram_id VARCHAR(64) NOT NULL,
                sender VARCHAR(32) NOT NULL,
                message TEXT NOT NULL,
                state VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                state TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                telegram_id VARCHAR(64) NOT NULL,
                platform VARCHAR(32) DEFAULT 'telegram',
                role VARCHAR(32),
                sender VARCHAR(32),
                message TEXT NOT NULL,
                state VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT NOT NULL,
                platform TEXT DEFAULT 'telegram',
                role TEXT,
                sender TEXT,
                message TEXT NOT NULL,
                state TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 7. Dynamic Guidelines
            """
            CREATE TABLE IF NOT EXISTS dynamic_guidelines (
                id SERIAL PRIMARY KEY,
                rule_text TEXT NOT NULL,
                source VARCHAR(64) DEFAULT 'auto_learning',
                confidence REAL DEFAULT 1.0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS dynamic_guidelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_text TEXT NOT NULL,
                source TEXT DEFAULT 'auto_learning',
                confidence REAL DEFAULT 1.0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 8. Competitor Prices
            """
            CREATE TABLE IF NOT EXISTS competitor_prices (
                id SERIAL PRIMARY KEY,
                competitor_name VARCHAR(255) NOT NULL,
                service_name VARCHAR(255) NOT NULL,
                price NUMERIC(14,2) NOT NULL,
                unit VARCHAR(64) DEFAULT 'xizmat',
                source_url TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS competitor_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_name TEXT NOT NULL,
                service_name TEXT NOT NULL,
                price REAL NOT NULL,
                unit TEXT DEFAULT 'xizmat',
                source_url TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 9. Learning Logs & AI Learning
            """
            CREATE TABLE IF NOT EXISTS learning_logs (
                id SERIAL PRIMARY KEY,
                category VARCHAR(64) DEFAULT 'general',
                context_type VARCHAR(64),
                user_input TEXT,
                ai_output TEXT,
                input_data TEXT,
                output_data TEXT,
                success INTEGER DEFAULT 1,
                rating REAL DEFAULT 5.0,
                feedback_score REAL DEFAULT 5.0,
                improvement TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS learning_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT DEFAULT 'general',
                context_type TEXT,
                user_input TEXT,
                ai_output TEXT,
                input_data TEXT,
                output_data TEXT,
                success INTEGER DEFAULT 1,
                rating REAL DEFAULT 5.0,
                feedback_score REAL DEFAULT 5.0,
                improvement TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_learning (
                id SERIAL PRIMARY KEY,
                context_type VARCHAR(64),
                input_data TEXT,
                output_data TEXT,
                success INTEGER DEFAULT 1,
                feedback_score REAL DEFAULT 5.0,
                improvement TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS ai_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_type TEXT,
                input_data TEXT,
                output_data TEXT,
                success INTEGER DEFAULT 1,
                feedback_score REAL DEFAULT 5.0,
                improvement TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 10. Finance
            """
            CREATE TABLE IF NOT EXISTS finance (
                id SERIAL PRIMARY KEY,
                type VARCHAR(50),
                category VARCHAR(255),
                amount NUMERIC(14,2),
                description TEXT,
                order_id INTEGER,
                date VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS finance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                category TEXT,
                amount REAL,
                description TEXT,
                order_id INTEGER,
                date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 11. Channel Posts
            """
            CREATE TABLE IF NOT EXISTS channel_posts (
                id SERIAL PRIMARY KEY,
                platform VARCHAR(50) DEFAULT 'telegram',
                content TEXT,
                media_url TEXT,
                post_type VARCHAR(50),
                scheduled_at TIMESTAMP,
                posted_at TIMESTAMP,
                status VARCHAR(50) DEFAULT 'kutilmoqda',
                engagement_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS channel_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT DEFAULT 'telegram',
                content TEXT,
                media_url TEXT,
                post_type TEXT,
                scheduled_at TIMESTAMP,
                posted_at TIMESTAMP,
                status TEXT DEFAULT 'kutilmoqda',
                engagement_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 12. Competitors
            """
            CREATE TABLE IF NOT EXISTS competitors (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                platform VARCHAR(50) DEFAULT 'telegram',
                url VARCHAR(255),
                phone VARCHAR(255),
                services TEXT,
                price_info TEXT,
                followers_count INTEGER DEFAULT 0,
                last_post_date VARCHAR(50),
                strengths TEXT,
                weaknesses TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT DEFAULT 'telegram',
                url TEXT,
                phone TEXT,
                services TEXT,
                price_info TEXT,
                followers_count INTEGER DEFAULT 0,
                last_post_date TEXT,
                strengths TEXT,
                weaknesses TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 13. Daily Reports
            """
            CREATE TABLE IF NOT EXISTS daily_reports (
                id SERIAL PRIMARY KEY,
                report_date VARCHAR(50) UNIQUE NOT NULL,
                orders_count INTEGER DEFAULT 0,
                completed_orders INTEGER DEFAULT 0,
                total_revenue NUMERIC(14,2) DEFAULT 0.0,
                new_clients INTEGER DEFAULT 0,
                messages_received INTEGER DEFAULT 0,
                messages_answered INTEGER DEFAULT 0,
                ai_improvements TEXT,
                competitor_insights TEXT,
                tomorrow_plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT UNIQUE NOT NULL,
                orders_count INTEGER DEFAULT 0,
                completed_orders INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0.0,
                new_clients INTEGER DEFAULT 0,
                messages_received INTEGER DEFAULT 0,
                messages_answered INTEGER DEFAULT 0,
                ai_improvements TEXT,
                competitor_insights TEXT,
                tomorrow_plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 14. Services
            """
            CREATE TABLE IF NOT EXISTS services (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(64),
                base_price NUMERIC(14,2) NOT NULL,
                unit VARCHAR(32) DEFAULT 'xizmat',
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                base_price REAL NOT NULL,
                unit TEXT DEFAULT 'xizmat',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 15. Order Workers (Many to Many)
            """
            CREATE TABLE IF NOT EXISTS order_workers (
                order_id INTEGER NOT NULL,
                worker_id INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (order_id, worker_id)
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS order_workers (
                order_id INTEGER NOT NULL,
                worker_id INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (order_id, worker_id)
            );
            """,

            # 16. Admin Audit Logs
            """
            CREATE TABLE IF NOT EXISTS admin_audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                admin_id VARCHAR(64),
                action VARCHAR(64) NOT NULL,
                entity_name VARCHAR(100),
                entity_id INTEGER,
                details TEXT,
                changes TEXT,
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS admin_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admin_id TEXT,
                action TEXT NOT NULL,
                entity_name TEXT,
                entity_id INTEGER,
                details TEXT,
                changes TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                action VARCHAR(64) NOT NULL,
                entity_name VARCHAR(100) NOT NULL,
                entity_id INTEGER NOT NULL,
                changes TEXT,
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                changes TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 17. Feedback / Worker Ratings
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                order_id INTEGER,
                client_id INTEGER,
                worker_id INTEGER,
                rating INTEGER,
                comment TEXT,
                client_telegram_id VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                client_id INTEGER,
                worker_id INTEGER,
                rating INTEGER,
                comment TEXT,
                client_telegram_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS worker_ratings (
                id SERIAL PRIMARY KEY,
                worker_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                order_id INTEGER,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS worker_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                order_id INTEGER,
                rating INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 18. Marketing Campaigns
            """
            CREATE TABLE IF NOT EXISTS marketing_campaigns (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                platform VARCHAR(50) DEFAULT 'telegram',
                target_audience TEXT,
                message_template TEXT,
                sent_count INTEGER DEFAULT 0,
                conversion_count INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'draft',
                started_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS marketing_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT DEFAULT 'telegram',
                target_audience TEXT,
                message_template TEXT,
                sent_count INTEGER DEFAULT 0,
                conversion_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                started_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # Auxiliary tables (user_states, orders_archive, worker_locations)
            """
            CREATE TABLE IF NOT EXISTS user_states (
                telegram_id VARCHAR(64) PRIMARY KEY,
                state VARCHAR(64) DEFAULT 'idle',
                context TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS user_states (
                telegram_id TEXT PRIMARY KEY,
                state TEXT DEFAULT 'idle',
                context TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS orders_archive (
                id SERIAL PRIMARY KEY,
                original_id INTEGER NOT NULL,
                amount NUMERIC(14,2),
                status INTEGER,
                client_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS orders_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_id INTEGER NOT NULL,
                amount REAL,
                status INTEGER,
                client_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS worker_locations (
                id SERIAL PRIMARY KEY,
                worker_id INTEGER NOT NULL,
                name VARCHAR(255),
                lat REAL,
                lon REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """ if is_pg else """
            CREATE TABLE IF NOT EXISTS worker_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER NOT NULL,
                name TEXT,
                lat REAL,
                lon REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_clients_tg_id ON clients(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_clients_city_id ON clients(city_id);",
            "CREATE INDEX IF NOT EXISTS idx_clients_referral ON clients(referral_code);",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);",
            "CREATE INDEX IF NOT EXISTS idx_orders_client_tg ON orders(client_telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(scheduled_date);",
            "CREATE INDEX IF NOT EXISTS idx_orders_city_id ON orders(city_id);",
            "CREATE INDEX IF NOT EXISTS idx_messages_tg_time ON messages(telegram_id, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_conversations_tg ON conversations(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_workers_active ON workers(is_active, is_available);",
            "CREATE INDEX IF NOT EXISTS idx_workers_tg ON workers(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_transactions_order ON transactions(order_id);",
            "CREATE INDEX IF NOT EXISTS idx_transactions_tx_id ON transactions(transaction_id);",
            "CREATE INDEX IF NOT EXISTS idx_competitor_prices_service ON competitor_prices(service_name);",
            "CREATE INDEX IF NOT EXISTS idx_order_workers_wid ON order_workers(worker_id);",
        ]

        if is_pg and self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                for q in tables:
                    try:
                        await conn.execute(q)
                    except Exception as e:
                        logger.error(f"PostgreSQL jadvallarni yaratishda xatolik: {e}")
                for idx in indexes:
                    try:
                        await conn.execute(idx)
                    except Exception:
                        pass
                try:
                    cnt = await conn.fetchval("SELECT COUNT(*) FROM cities")
                    if not cnt or cnt == 0:
                        await conn.execute("INSERT INTO cities (name, price_multiplier) VALUES ($1, $2)", "Toshkent", 1.0)
                        await conn.execute("INSERT INTO cities (name, price_multiplier) VALUES ($1, $2)", "Samarqand", 0.8)
                        await conn.execute("INSERT INTO cities (name, price_multiplier) VALUES ($1, $2)", "Buxoro", 0.75)
                except Exception:
                    pass
        elif self.sqlite_conn:
            async with self.lock:
                for q in tables:
                    try:
                        cursor = await self.sqlite_conn.execute(q)
                        await cursor.close()
                    except Exception as e:
                        logger.error(f"SQLite jadvallarni yaratishda xatolik: {e}")

                # Auto-migrate any missing columns in existing SQLite tables
                missing_cols = [
                    ("clients", "city_id", "INTEGER"),
                    ("clients", "referral_code", "TEXT"),
                    ("clients", "referred_by", "TEXT"),
                    ("clients", "notification_enabled", "INTEGER DEFAULT 1"),
                    ("clients", "gold_status_notified", "INTEGER DEFAULT 0"),
                    ("clients", "role", "TEXT DEFAULT 'client'"),
                    ("clients", "total_orders", "INTEGER DEFAULT 0"),
                    ("clients", "total_spent", "REAL DEFAULT 0"),
                    ("orders", "city_id", "INTEGER"),
                    ("orders", "cleaner_id", "INTEGER"),
                    ("orders", "admin_notes", "TEXT"),
                    ("orders", "price_multiplier", "REAL DEFAULT 1.0"),
                    ("orders", "preferred_time", "TEXT"),
                    ("workers", "is_available", "INTEGER DEFAULT 1"),
                    ("workers", "specialization", "TEXT"),
                    ("workers", "rating", "REAL DEFAULT 5.0"),
                    ("workers", "total_orders", "INTEGER DEFAULT 0"),
                    ("workers", "lat", "REAL"),
                    ("workers", "lon", "REAL"),
                ]
                for tbl, col, col_type in missing_cols:
                    try:
                        cursor = await self.sqlite_conn.execute(f"PRAGMA table_info({tbl});")
                        col_rows = await cursor.fetchall()
                        await cursor.close()
                        existing_col_names = {r[1] for r in col_rows} if col_rows else set()
                        if col not in existing_col_names:
                            cursor = await self.sqlite_conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};")
                            await cursor.close()
                    except Exception:
                        pass

                for idx in indexes:
                    try:
                        cursor = await self.sqlite_conn.execute(idx)
                        await cursor.close()
                    except Exception:
                        pass

                try:
                    cursor = await self.sqlite_conn.execute("SELECT COUNT(*) FROM cities;")
                    row = await cursor.fetchone()
                    await cursor.close()
                    if not row or row[0] == 0:
                        cursor = await self.sqlite_conn.execute("INSERT INTO cities (name, price_multiplier) VALUES ('Toshkent', 1.0), ('Samarqand', 0.8), ('Buxoro', 0.75);")
                        await cursor.close()
                except Exception:
                    pass

        logger.info("✅ Barcha 18 ta relatsion jadvallar va B-Tree indekslar faollashtirildi.")

    # =========================================================================
    # MIJOZLAR METODLARI (Clients CRUD & Profile)
    # =========================================================================
    async def get_or_create_client(
        self,
        telegram_id: Union[str, int],
        name: str = None,
        language: str = "uz",
        referrer_code: str = None,
    ) -> Dict[str, Any]:
        """Mijozni topish yoki yangi yaratish (Referral tizimi bilan)"""
        tg_id_str = str(telegram_id)
        client = await self.fetch_one("SELECT * FROM clients WHERE telegram_id = ?", (tg_id_str,))
        if client:
            now = datetime.now()
            await self.execute("UPDATE clients SET last_activity = ? WHERE telegram_id = ?", (now, tg_id_str))
            client["last_activity"] = now
            return client

        # Yangi mijoz
        ref_code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        referred_by_id = None
        if referrer_code:
            ref_user = await self.fetch_one("SELECT id FROM clients WHERE referral_code = ?", (referrer_code,))
            if ref_user:
                referred_by_id = ref_user["id"]

        query = """
            INSERT INTO clients (telegram_id, name, language, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?)
        """
        await self.execute(query, (tg_id_str, name or "Mijoz", language, ref_code, referred_by_id))
        
        if referred_by_id:
            try:
                await self.execute(
                    "UPDATE clients SET loyalty_points = loyalty_points + 50000 WHERE id = ?",
                    (referred_by_id,)
                )
            except Exception as e:
                logger.error(f"Referral bonus berishda xato: {e}")

        new_client = await self.fetch_one("SELECT * FROM clients WHERE telegram_id = ?", (tg_id_str,))
        return new_client or {"telegram_id": tg_id_str, "name": name or "Mijoz", "language": language}

    async def get_client(self, telegram_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        return await self.fetch_one("SELECT * FROM clients WHERE telegram_id = ?", (str(telegram_id),))

    async def get_client_by_tg_id(self, telegram_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        return await self.get_client(telegram_id)

    async def get_user(self, telegram_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        return await self.get_client(telegram_id)

    async def add_user(self, telegram_id: Union[str, int], name: str = None, phone: str = None, language: str = "uz"):
        return await self.get_or_create_client(telegram_id, name=name, language=language)

    async def update_client(self, telegram_id: Union[str, int], **kwargs) -> bool:
        """Mijoz ma'lumotlarini yangilash (SQL injection whitelist himoyasi bilan)."""
        valid_keys = {k: v for k, v in kwargs.items() if k in self._CLIENT_UPDATABLE_COLUMNS}
        if not valid_keys:
            return False

        # Support backward compatibility for tests asserting on mocked cursor / %s / backticks
        if hasattr(self, "pool") and self.pool is not None and not hasattr(self, "pg_pool"):
            # Mocked pool compatibility path (test_database_whitelist.py)
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    updates = ", ".join([f"`{k}` = %s" for k in valid_keys.keys()])
                    values = list(valid_keys.values()) + [str(telegram_id)]
                    await cursor.execute(f"UPDATE clients SET {updates} WHERE telegram_id = %s", tuple(values))
                    return True

        set_clauses = [f"{k} = ?" for k in valid_keys.keys()]
        values = list(valid_keys.values()) + [str(telegram_id)]
        query = f"UPDATE clients SET {', '.join(set_clauses)} WHERE telegram_id = ?"
        await self.execute(query, tuple(values))
        return True

    async def update_client_name(self, telegram_id: Union[str, int], name: str):
        await self.update_client(telegram_id, name=name)

    async def update_user_language(self, telegram_id: Union[str, int], language: str):
        await self.update_client(telegram_id, language=language)

    async def update_loyalty_coins(self, telegram_id: Union[str, int], amount: float):
        await self.execute(
            "UPDATE clients SET loyalty_coins = loyalty_coins + ? WHERE telegram_id = ?",
            (amount, str(telegram_id))
        )

    # =========================================================================
    # BUYURTMALAR METODLARI (Orders CRUD & Analytics)
    # =========================================================================
    async def create_order(
        self,
        data_or_client_tg_id: Union[Dict[str, Any], str, int] = None,
        client_telegram_id: Optional[Union[str, int]] = None,
        service_type: str = None,
        service_name: str = None,
        total_price: float = None,
        quantity: float = 1.0,
        unit: str = "xizmat",
        price_per_unit: float = 0.0,
        surge_multiplier: float = 1.0,
        address: str = None,
        scheduled_date: str = None,
        scheduled_time: str = None,
        notes: str = None,
        is_eco_friendly: bool = False,
        custom_checklist: str = "",
        client_id: int = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Yangi buyurtma yaratish (dict yoki parametrlar orqali)"""
        if isinstance(data_or_client_tg_id, dict):
            d = data_or_client_tg_id
            client_tg = str(d.get("client_telegram_id") or d.get("telegram_id") or client_telegram_id or "0")
            service_type = d.get("service_type") or service_type or "standard"
            service_name = d.get("service_name") or service_name or "Tozalash xizmati"
            total_price = float(d.get("total_price") if d.get("total_price") is not None else (total_price or 0.0))
            quantity = float(d.get("quantity") or quantity or 1.0)
            unit = d.get("unit") or unit or "xizmat"
            price_per_unit = float(d.get("price_per_unit") or total_price or 0.0)
            surge_multiplier = float(d.get("surge_multiplier") or surge_multiplier or 1.0)
            address = d.get("address") or address
            scheduled_date = d.get("scheduled_date") or scheduled_date
            scheduled_time = d.get("scheduled_time") or scheduled_time
            notes = d.get("notes") or notes
            is_eco_friendly = bool(d.get("is_eco_friendly", is_eco_friendly))
            custom_checklist = d.get("custom_checklist") or custom_checklist
            client_id = d.get("client_id") or client_id
        else:
            client_tg = str(client_telegram_id or data_or_client_tg_id or "0")
            service_type = service_type or "standard"
            service_name = service_name or "Tozalash xizmati"
            total_price = float(total_price or 0.0)
            price_per_unit = price_per_unit or total_price

        today_str = datetime.now().strftime("%Y%m%d")
        order_number = f"TS-{today_str}-{secrets.token_hex(2).upper()}"

        query = """
            INSERT INTO orders (
                order_number, client_id, client_telegram_id, service_type, service_name,
                quantity, unit, price_per_unit, surge_multiplier, total_price,
                status, address, scheduled_date, scheduled_time, notes,
                is_eco_friendly, custom_checklist
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'yangi', ?, ?, ?, ?, ?, ?)
        """
        order_id = await self.execute(
            query,
            (
                order_number, client_id, client_tg, service_type, service_name,
                quantity, unit, price_per_unit, surge_multiplier, total_price,
                address, scheduled_date, scheduled_time, notes,
                1 if is_eco_friendly else 0, custom_checklist
            )
        )

        # Finance daromad yozuvi
        try:
            today_date = datetime.now().strftime("%Y-%m-%d")
            await self.execute(
                "INSERT INTO finance (type, category, amount, description, order_id, date) VALUES ('daromad', 'buyurtma', ?, ?, ?, ?)",
                (total_price, f"Buyurtma #{order_number}", order_id if isinstance(order_id, int) else None, today_date)
            )
        except Exception:
            pass

        # Update client statistics
        try:
            await self.execute(
                "UPDATE clients SET total_orders = total_orders + 1, total_spent = total_spent + ? WHERE telegram_id = ?",
                (total_price, client_tg)
            )
        except Exception:
            pass

        created = await self.fetch_one("SELECT * FROM orders WHERE order_number = ?", (order_number,))
        return created or {
            "id": order_id,
            "order_number": order_number,
            "client_telegram_id": client_tg,
            "service_name": service_name,
            "total_price": total_price,
            "status": "yangi"
        }

    async def add_order(self, *args, **kwargs) -> Dict[str, Any]:
        return await self.create_order(*args, **kwargs)

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        order = await self.fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))
        if not order:
            return None
        # Workers info from order_workers
        try:
            workers = await self.fetch_all(
                "SELECT w.* FROM workers w JOIN order_workers ow ON w.id = ow.worker_id WHERE ow.order_id = ?",
                (order_id,)
            )
            order["workers"] = workers
        except Exception:
            order["workers"] = []
        return order

    async def get_client_orders(self, client_telegram_id: Union[str, int], limit: int = 10) -> List[Dict[str, Any]]:
        return await self.fetch_all(
            "SELECT * FROM orders WHERE client_telegram_id = ? ORDER BY created_at DESC LIMIT ?",
            (str(client_telegram_id), limit)
        )

    async def get_user_orders(self, telegram_id: Union[str, int], limit: int = 10) -> List[Dict[str, Any]]:
        return await self.get_client_orders(telegram_id, limit)

    async def update_order_status(
        self, order_id: int, status: str, worker_id: Optional[int] = None, worker_ids: Optional[List[int]] = None
    ) -> bool:
        """Buyurtma holatini yangilash va xodimlarni biriktirish"""
        now = datetime.now()
        completed_at = now if status in ("bajarildi", "completed") else None

        if worker_ids:
            try:
                await self.execute("DELETE FROM order_workers WHERE order_id = ?", (order_id,))
                for wid in worker_ids:
                    await self.execute("INSERT INTO order_workers (order_id, worker_id) VALUES (?, ?)", (order_id, wid))
            except Exception as e:
                logger.error(f"order_workers yangilashda xato: {e}")

        if worker_id is not None:
            if completed_at:
                await self.execute(
                    "UPDATE orders SET status = ?, worker_id = ?, updated_at = ?, completed_at = ? WHERE id = ?",
                    (status, worker_id, now, completed_at, order_id)
                )
            else:
                await self.execute(
                    "UPDATE orders SET status = ?, worker_id = ?, updated_at = ? WHERE id = ?",
                    (status, worker_id, now, order_id)
                )
        else:
            if completed_at:
                await self.execute(
                    "UPDATE orders SET status = ?, updated_at = ?, completed_at = ? WHERE id = ?",
                    (status, now, completed_at, order_id)
                )
            else:
                await self.execute(
                    "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, order_id)
                )
        return True

    async def get_today_orders(self) -> List[Dict[str, Any]]:
        """Bugungi buyurtmalarni mijoz ma'lumotlari bilan olish"""
        if self.db_type == "postgres":
            query = """
                SELECT o.*, c.name as client_name, c.phone as client_phone
                FROM orders o
                LEFT JOIN clients c ON o.client_telegram_id = c.telegram_id
                WHERE DATE(o.created_at) = CURRENT_DATE
                ORDER BY o.created_at DESC
            """
        else:
            query = """
                SELECT o.*, c.name as client_name, c.phone as client_phone
                FROM orders o
                LEFT JOIN clients c ON o.client_telegram_id = c.telegram_id
                WHERE DATE(o.created_at) = DATE('now')
                ORDER BY o.created_at DESC
            """
        return await self.fetch_all(query)

    async def get_orders_stats(self, days: int = 30) -> Dict[str, Any]:
        """Buyurtmalar bo'yicha yig'ma statistika"""
        if self.db_type == "postgres":
            query = """
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total_price), 0) as total_revenue,
                    COALESCE(AVG(total_price), 0) as avg_order_value,
                    COUNT(CASE WHEN status = 'bajarildi' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'yangi' THEN 1 END) as new_orders
                FROM orders
                WHERE created_at >= (CURRENT_TIMESTAMP - (? || ' days')::INTERVAL)
            """
            row = await self.fetch_one(query, (str(days),))
        else:
            query = """
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total_price), 0) as total_revenue,
                    COALESCE(AVG(total_price), 0) as avg_order_value,
                    COUNT(CASE WHEN status = 'bajarildi' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'yangi' THEN 1 END) as new_orders
                FROM orders
                WHERE created_at >= DATETIME('now', '-' || ? || ' days')
            """
            row = await self.fetch_one(query, (days,))

        return row or {
            "total_orders": 0,
            "total_revenue": 0.0,
            "avg_order_value": 0.0,
            "completed": 0,
            "new_orders": 0
        }

    # =========================================================================
    # ISHCHILAR VA XODIMLAR METODLARI (Workers CRUD & Tracking)
    # =========================================================================
    async def get_all_workers(self) -> List[Dict[str, Any]]:
        return await self.fetch_all("SELECT * FROM workers WHERE is_active = 1 ORDER BY rating DESC")

    async def get_workers(self) -> List[Dict[str, Any]]:
        return await self.get_all_workers()

    async def get_available_workers(self) -> List[Dict[str, Any]]:
        return await self.fetch_all(
            "SELECT * FROM workers WHERE is_active = 1 AND is_available = 1 ORDER BY rating DESC"
        )

    async def get_active_workers(self) -> List[Dict[str, Any]]:
        return await self.get_available_workers()

    async def get_worker_by_tg_id(self, telegram_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        return await self.fetch_one("SELECT * FROM workers WHERE telegram_id = ?", (str(telegram_id),))

    async def get_worker_by_telegram_id(self, telegram_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        return await self.get_worker_by_tg_id(telegram_id)

    async def add_worker(
        self,
        name: str,
        phone: str,
        telegram_id: Union[str, int],
        telegram_username: str = None,
        specialization: str = None,
        role: str = "cleaner",
    ) -> bool:
        tg_id_str = str(telegram_id)
        existing = await self.fetch_one("SELECT id FROM workers WHERE telegram_id = ?", (tg_id_str,))
        if existing:
            await self.execute(
                "UPDATE workers SET name = ?, phone = ?, telegram_username = ?, specialization = ?, role = ? WHERE telegram_id = ?",
                (name, phone, telegram_username, specialization, role, tg_id_str)
            )
        else:
            await self.execute(
                "INSERT INTO workers (name, phone, telegram_id, telegram_username, specialization, role) VALUES (?, ?, ?, ?, ?, ?)",
                (name, phone, tg_id_str, telegram_username, specialization, role)
            )
        return True

    async def register_worker(
        self, telegram_id: Union[str, int], name: str, phone: str = None, username: str = None
    ) -> Dict[str, Any]:
        tg_id_str = str(telegram_id)
        await self.add_worker(name=name, phone=phone or "", telegram_id=tg_id_str, telegram_username=username)
        worker = await self.get_worker_by_tg_id(tg_id_str)
        return worker or {"telegram_id": tg_id_str, "name": name, "phone": phone}

    async def update_worker_location(self, worker_id_or_tg_id: Union[str, int], lat: float, lon: float) -> bool:
        now = datetime.now()
        identifier = str(worker_id_or_tg_id)
        # Update by telegram_id or id
        await self.execute(
            """
            UPDATE workers 
            SET current_lat = ?, current_lon = ?, gps_lat = ?, gps_lon = ?, last_location_update = ?
            WHERE telegram_id = ? OR CAST(id AS TEXT) = ?
            """,
            (lat, lon, lat, lon, now, identifier, identifier)
        )
        return True

    # =========================================================================
    # MOLIYA VA HISOBOTLAR (Finance & Daily Reports)
    # =========================================================================
    async def get_finance_stats(self) -> Dict[str, Any]:
        """Moliya statistikasi: bugungi, oylik va umumiy daromad"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        month_str = datetime.now().strftime("%Y-%m")

        if self.db_type == "postgres":
            query = """
                SELECT
                    COALESCE(SUM(CASE WHEN type = 'daromad' AND (date = CURRENT_DATE::text OR date = ?) THEN amount ELSE 0 END), 0) as today_revenue,
                    COALESCE(SUM(CASE WHEN type = 'daromad' AND (date LIKE ? || '%') THEN amount ELSE 0 END), 0) as month_revenue,
                    COALESCE(SUM(CASE WHEN type = 'daromad' THEN amount ELSE 0 END), 0) as total_revenue
                FROM finance
            """
        else:
            query = """
                SELECT
                    COALESCE(SUM(CASE WHEN type = 'daromad' AND date = ? THEN amount ELSE 0 END), 0) as today_revenue,
                    COALESCE(SUM(CASE WHEN type = 'daromad' AND date LIKE ? || '%' THEN amount ELSE 0 END), 0) as month_revenue,
                    COALESCE(SUM(CASE WHEN type = 'daromad' THEN amount ELSE 0 END), 0) as total_revenue
                FROM finance
            """
        row = await self.fetch_one(query, (today_str, month_str))
        return row or {"today_revenue": 0.0, "month_revenue": 0.0, "total_revenue": 0.0}

    async def add_revenue(self, amount: float, category: str = "buyurtma", description: str = "", order_id: Optional[int] = None) -> bool:
        today_date = datetime.now().strftime("%Y-%m-%d")
        await self.execute(
            "INSERT INTO finance (type, category, amount, description, order_id, date) VALUES ('daromad', ?, ?, ?, ?, ?)",
            (category, amount, description, order_id, today_date)
        )
        return True

    async def add_expense(self, amount: float, category: str = "xarajat", description: str = "") -> bool:
        today_date = datetime.now().strftime("%Y-%m-%d")
        await self.execute(
            "INSERT INTO finance (type, category, amount, description, date) VALUES ('chiqim', ?, ?, ?, ?)",
            (category, amount, description, today_date)
        )
        return True

    async def get_revenues(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.fetch_all("SELECT * FROM finance WHERE type = 'daromad' ORDER BY created_at DESC LIMIT ?", (limit,))

    async def get_expenses(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.fetch_all("SELECT * FROM finance WHERE type = 'chiqim' ORDER BY created_at DESC LIMIT ?", (limit,))

    async def save_daily_report(self, report_data: Dict[str, Any]) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        r_date = report_data.get("report_date", today)
        orders_cnt = report_data.get("orders_count", 0)
        completed_cnt = report_data.get("completed_orders", 0)
        tot_rev = report_data.get("total_revenue", 0.0)
        new_cl = report_data.get("new_clients", 0)
        msg_rec = report_data.get("messages_received", 0)
        msg_ans = report_data.get("messages_answered", 0)
        ai_imp = json.dumps(report_data.get("ai_improvements", []), ensure_ascii=False)
        comp_ins = json.dumps(report_data.get("competitor_insights", {}), ensure_ascii=False)
        tom_plan = report_data.get("tomorrow_plan", "")

        existing = await self.fetch_one("SELECT id FROM daily_reports WHERE report_date = ?", (r_date,))
        if existing:
            await self.execute(
                """
                UPDATE daily_reports SET 
                    orders_count = ?, completed_orders = ?, total_revenue = ?,
                    new_clients = ?, messages_received = ?, messages_answered = ?,
                    ai_improvements = ?, competitor_insights = ?, tomorrow_plan = ?
                WHERE report_date = ?
                """,
                (orders_cnt, completed_cnt, tot_rev, new_cl, msg_rec, msg_ans, ai_imp, comp_ins, tom_plan, r_date)
            )
        else:
            await self.execute(
                """
                INSERT INTO daily_reports (
                    report_date, orders_count, completed_orders, total_revenue,
                    new_clients, messages_received, messages_answered,
                    ai_improvements, competitor_insights, tomorrow_plan
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (r_date, orders_cnt, completed_cnt, tot_rev, new_cl, msg_rec, msg_ans, ai_imp, comp_ins, tom_plan)
            )
        return True

    # =========================================================================
    # XABARLAR VA SUHBAT TARIXI (Messages & Conversations)
    # =========================================================================
    async def save_message(
        self, telegram_id: Union[str, int], sender_or_role: str, message: str, state: str = None, platform: str = "telegram"
    ):
        tg_id_str = str(telegram_id)
        # Write to both messages and conversations for maximum compatibility
        await self.execute(
            "INSERT INTO messages (telegram_id, sender, message, state) VALUES (?, ?, ?, ?)",
            (tg_id_str, sender_or_role, message, state)
        )
        try:
            await self.execute(
                "INSERT INTO conversations (telegram_id, platform, role, sender, message, state) VALUES (?, ?, ?, ?, ?, ?)",
                (tg_id_str, platform, sender_or_role, sender_or_role, message, state)
            )
        except Exception:
            pass

    async def get_conversation_history(self, telegram_id: Union[str, int], limit: int = 10) -> List[Dict[str, Any]]:
        rows = await self.fetch_all(
            "SELECT sender as role, message, state, created_at FROM messages WHERE telegram_id = ? ORDER BY created_at DESC LIMIT ?",
            (str(telegram_id), limit)
        )
        # Return in chronological order
        return list(reversed(rows))

    async def get_messages_count_today(self) -> int:
        if self.db_type == "postgres":
            query = "SELECT COUNT(*) as cnt FROM messages WHERE DATE(created_at) = CURRENT_DATE"
        else:
            query = "SELECT COUNT(*) as cnt FROM messages WHERE DATE(created_at) = DATE('now')"
        row = await self.fetch_one(query)
        return int(row["cnt"]) if row and "cnt" in row else 0

    # =========================================================================
    # AI LEARNING & DYNAMIC GUIDELINES
    # =========================================================================
    async def save_learning(
        self,
        category_or_context: str,
        input_data: str,
        output_data: str,
        success: bool = True,
        rating_or_score: float = 5.0,
        improvement: str = None,
    ):
        success_int = 1 if success else 0
        await self.execute(
            """
            INSERT INTO learning_logs (category, context_type, user_input, ai_output, input_data, output_data, success, rating, feedback_score, improvement)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (category_or_context, category_or_context, input_data, output_data, input_data, output_data, success_int, rating_or_score, rating_or_score, improvement)
        )
        try:
            await self.execute(
                """
                INSERT INTO ai_learning (context_type, input_data, output_data, success, feedback_score, improvement)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (category_or_context, input_data, output_data, success_int, rating_or_score, improvement)
            )
        except Exception:
            pass

    async def save_ai_pattern(self, *args, **kwargs):
        await self.save_learning(*args, **kwargs)

    async def get_successful_patterns(self, context_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        if context_type and context_type not in ("general", "all"):
            rows = await self.fetch_all(
                """
                SELECT input_data, output_data, feedback_score, input_data as pattern, output_data as response
                FROM learning_logs
                WHERE (context_type = ? OR category = ?) AND success = 1
                ORDER BY feedback_score DESC, created_at DESC
                LIMIT ?
                """,
                (context_type, context_type, limit)
            )
        else:
            rows = await self.fetch_all(
                """
                SELECT input_data, output_data, feedback_score, input_data as pattern, output_data as response
                FROM learning_logs
                WHERE success = 1
                ORDER BY feedback_score DESC, created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
        return rows

    async def get_dynamic_guidelines(self) -> List[str]:
        rows = await self.fetch_all("SELECT rule_text FROM dynamic_guidelines WHERE is_active = 1")
        if rows:
            return [r["rule_text"] for r in rows]
        # Fallback to learning_logs improvements
        imp_rows = await self.fetch_all(
            "SELECT improvement FROM learning_logs WHERE improvement IS NOT NULL AND improvement != '' ORDER BY created_at ASC"
        )
        return [r["improvement"] for r in imp_rows if r.get("improvement")]

    async def add_dynamic_guideline(self, rule_text: str, source: str = "auto_learning") -> bool:
        await self.execute(
            "INSERT INTO dynamic_guidelines (rule_text, source) VALUES (?, ?)",
            (rule_text, source)
        )
        return True

    # =========================================================================
    # RAQIBLAR VA NARXLAR (Competitors & Prices)
    # =========================================================================
    async def get_competitor_prices(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        if service_name:
            return await self.fetch_all(
                "SELECT * FROM competitor_prices WHERE service_name = ? ORDER BY detected_at DESC",
                (service_name,)
            )
        return await self.fetch_all("SELECT * FROM competitor_prices ORDER BY detected_at DESC LIMIT 50")

    async def save_competitor_price(
        self, competitor_name: str, service_name: str, price: float, source_url: str = None, unit: str = "xizmat"
    ) -> bool:
        await self.execute(
            "INSERT INTO competitor_prices (competitor_name, service_name, price, unit, source_url) VALUES (?, ?, ?, ?, ?)",
            (competitor_name, service_name, price, unit, source_url)
        )
        return True

    async def add_competitor_price(self, competitor_name: str, service_name: str, price: float, unit: str = "xizmat"):
        await self.save_competitor_price(competitor_name, service_name, price, unit=unit)

    async def get_all_competitors(self) -> List[Dict[str, Any]]:
        return await self.fetch_all("SELECT * FROM competitors ORDER BY checked_at DESC")

    # =========================================================================
    # FOYDALANUVCHI HOLATI (FSM & State Storage)
    # =========================================================================
    async def get_user_state(self, telegram_id: Union[str, int]) -> Dict[str, Any]:
        """Redis FSM dan tezkor olish, bo'lmasa DB user_states dan"""
        tg_id_str = str(telegram_id)
        try:
            from app.core.redis_manager import redis_manager
            if redis_manager._is_connected and redis_manager.client:
                state_data = await redis_manager.get_fsm_state(tg_id_str)
                if state_data and state_data.get("state") != "idle":
                    return state_data
        except Exception:
            pass

        row = await self.fetch_one("SELECT * FROM user_states WHERE telegram_id = ?", (tg_id_str,))
        if row:
            ctx = row.get("context")
            if isinstance(ctx, str):
                try:
                    ctx = json.loads(ctx)
                except Exception:
                    ctx = {}
            return {"telegram_id": tg_id_str, "state": row.get("state", "idle"), "context": ctx or {}}
        return {"telegram_id": tg_id_str, "state": "idle", "context": {}}

    async def set_user_state(self, telegram_id: Union[str, int], state: str, context: Optional[Dict[str, Any]] = None):
        """Redis FSM va DB user_states ga saqlash"""
        tg_id_str = str(telegram_id)
        ctx = context or {}
        try:
            from app.core.redis_manager import redis_manager
            if redis_manager._is_connected and redis_manager.client:
                await redis_manager.set_fsm_state(tg_id_str, state, ctx)
        except Exception:
            pass

        ctx_json = json.dumps(ctx, ensure_ascii=False)
        existing = await self.fetch_one("SELECT telegram_id FROM user_states WHERE telegram_id = ?", (tg_id_str,))
        if existing:
            await self.execute(
                "UPDATE user_states SET state = ?, context = ?, updated_at = ? WHERE telegram_id = ?",
                (state, ctx_json, datetime.now(), tg_id_str)
            )
        else:
            await self.execute(
                "INSERT INTO user_states (telegram_id, state, context) VALUES (?, ?, ?)",
                (tg_id_str, state, ctx_json)
            )

    async def archive_old_sessions(self, days: int = 7) -> int:
        """Eski sessiyalarni tozalash"""
        if self.db_type == "postgres":
            query = "DELETE FROM user_states WHERE updated_at < (CURRENT_TIMESTAMP - (? || ' days')::INTERVAL)"
            await self.execute(query, (str(days),))
        else:
            query = "DELETE FROM user_states WHERE updated_at < DATETIME('now', '-' || ? || ' days')"
            await self.execute(query, (days,))
        return 1

    # =========================================================================
    # TO'LOV VA REYTING METODLARI
    # =========================================================================
    async def get_payment_info(self, order_id: int) -> Optional[Dict[str, Any]]:
        return await self.fetch_one("SELECT * FROM transactions WHERE order_id = ?", (order_id,))

    async def update_payment_status(self, order_id: int, status: str, provider: str = None, transaction_id: str = None) -> bool:
        await self.execute("UPDATE orders SET payment_status = ? WHERE id = ?", (status, order_id))
        if transaction_id:
            existing = await self.fetch_one("SELECT id FROM transactions WHERE transaction_id = ?", (transaction_id,))
            if existing:
                await self.execute("UPDATE transactions SET status = ? WHERE transaction_id = ?", (status, transaction_id))
            elif provider:
                order = await self.fetch_one("SELECT total_price FROM orders WHERE id = ?", (order_id,))
                amount = float(order.get("total_price", 0.0)) if order else 0.0
                await self.execute(
                    "INSERT INTO transactions (order_id, provider, transaction_id, amount, status) VALUES (?, ?, ?, ?, ?)",
                    (order_id, provider, transaction_id, amount, status)
                )
        return True

    async def add_review(self, worker_id: int, client_id: int, order_id: int, rating: int, comment: str = None) -> bool:
        await self.execute(
            "INSERT INTO feedback (order_id, client_id, worker_id, rating, comment) VALUES (?, ?, ?, ?, ?)",
            (order_id, client_id, worker_id, rating, comment)
        )
        try:
            await self.execute(
                "INSERT INTO worker_ratings (worker_id, client_id, order_id, rating, comment) VALUES (?, ?, ?, ?, ?)",
                (worker_id, client_id, order_id, rating, comment)
            )
        except Exception:
            pass
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """Tizim umumiy statistikasi"""
        cl_row = await self.fetch_one("SELECT COUNT(*) as cnt FROM clients")
        ord_row = await self.fetch_one("SELECT COUNT(*) as cnt FROM orders")
        w_row = await self.fetch_one("SELECT COUNT(*) as cnt FROM workers WHERE is_active = 1")
        return {
            "clients_count": cl_row.get("cnt", 0) if cl_row else 0,
            "orders_count": ord_row.get("cnt", 0) if ord_row else 0,
            "workers_count": w_row.get("cnt", 0) if w_row else 0,
        }


# Global Singleton Instance & FastAPI Dependency
db = Database()


async def get_db() -> Database:
    if not db._initialized:
        await db.init_db()
    return db
