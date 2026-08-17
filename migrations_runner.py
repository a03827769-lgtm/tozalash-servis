"""
Tozalash Servis — Migrations Runner (SQLite versiyasi)
Eslatma: Mavjud .sql fayllar MySQL uchun yozilgan. Bu runner ularni o'tkazib yuborib,
to'g'ridan-to'g'ri Python DDL orqali SQLite jadvallarini yaratadi.
"""

import aiosqlite
from pathlib import Path
from loguru import logger

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def run_migrations(db):
    """
    SQLite uchun barcha jadvallarni Python DDL orqali yaratish.
    MySQL .sql fayllar SQLite bilan mos emas, shuning uchun o'tkazib yuboriladi.
    """
    async with db.get_conn() as conn:
        await _create_base_tables(conn)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.commit()

    logger.info("Barcha migratsiyalar tekshirildi va jadvallar tayyor.")


async def _create_base_tables(conn: aiosqlite.Connection):
    """Barcha asosiy jadvallarni to'g'ridan-to'g'ri SQLite DDL orqali yaratish."""
    logger.info("Asosiy jadvallar yaratilmoqda...")

    tables = [
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            language TEXT DEFAULT 'uz',
            city TEXT DEFAULT 'Toshkent',
            city_id INTEGER,
            gender TEXT,
            address TEXT,
            role TEXT DEFAULT 'client',
            total_orders INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0,
            rating REAL DEFAULT 5.0,
            churn_risk REAL DEFAULT 0.0,
            loyalty_points INTEGER DEFAULT 0,
            loyalty_coins REAL DEFAULT 0,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            is_blocked INTEGER DEFAULT 0,
            notification_enabled INTEGER DEFAULT 1,
            gold_status_notified INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            client_id INTEGER,
            client_telegram_id TEXT,
            service_type TEXT,
            service_name TEXT,
            quantity REAL,
            unit TEXT,
            price_per_unit REAL,
            surge_multiplier REAL DEFAULT 1.0,
            total_price REAL,
            address TEXT,
            scheduled_date TEXT,
            scheduled_time TEXT,
            status TEXT DEFAULT 'yangi',
            worker_ids TEXT,
            worker_names TEXT,
            before_photo TEXT,
            after_photo TEXT,
            qa_approved INTEGER DEFAULT 0,
            payment_method TEXT,
            payment_status TEXT DEFAULT 'kutilmoqda',
            notes TEXT,
            is_eco_friendly INTEGER DEFAULT 0,
            custom_checklist TEXT,
            lat REAL,
            lng REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            telegram_id TEXT UNIQUE,
            telegram_username TEXT,
            specialization TEXT,
            is_active INTEGER DEFAULT 1,
            is_available INTEGER DEFAULT 1,
            total_jobs INTEGER DEFAULT 0,
            monthly_salary REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            rating REAL DEFAULT 5.0,
            gps_lat REAL,
            gps_lon REAL,
            last_location_update TIMESTAMP,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS order_workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (order_id, worker_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            category TEXT,
            amount REAL,
            description TEXT,
            order_id INTEGER,
            date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context_type TEXT,
            input_data TEXT,
            output_data TEXT,
            success INTEGER,
            feedback_score REAL,
            improvement TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS channel_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            content TEXT,
            media_url TEXT,
            post_type TEXT,
            scheduled_at TIMESTAMP,
            posted_at TIMESTAMP,
            status TEXT DEFAULT 'kutilmoqda',
            engagement_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            platform TEXT,
            url TEXT,
            phone TEXT,
            services TEXT,
            price_info TEXT,
            followers_count INTEGER,
            last_post_date TEXT,
            strengths TEXT,
            weaknesses TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS competitor_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_name TEXT,
            service_name TEXT,
            price REAL,
            source_url TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS daily_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT UNIQUE,
            orders_count INTEGER DEFAULT 0,
            completed_orders INTEGER DEFAULT 0,
            total_revenue REAL DEFAULT 0,
            new_clients INTEGER DEFAULT 0,
            messages_received INTEGER DEFAULT 0,
            messages_answered INTEGER DEFAULT 0,
            ai_improvements TEXT,
            competitor_insights TEXT,
            tomorrow_plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            platform TEXT DEFAULT 'telegram',
            role TEXT,
            message TEXT,
            state TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            state TEXT DEFAULT 'idle',
            context TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            message TEXT,
            notification_type TEXT,
            is_sent INTEGER DEFAULT 0,
            scheduled_at TIMESTAMP,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            region TEXT,
            is_active INTEGER DEFAULT 1
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service_type TEXT,
            base_price REAL,
            unit TEXT DEFAULT 'xona',
            description TEXT,
            is_active INTEGER DEFAULT 1,
            city_id INTEGER
        )
        """,
    ]

    for table_sql in tables:
        await conn.execute(table_sql)

    await conn.commit()
    logger.success("Barcha asosiy jadvallar muvaffaqiyatli yaratildi (SQLite).")
