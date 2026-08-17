"""
Tozalash Servis — Ma'lumotlar Bazasi Moduli (ASYNC)
aiosqlite orqali MySQL bilan ishlash
(Refactored for Transactions, Error Handling, and Many-to-Many Relationships)
"""

import asyncio
import aiosqlite
import os
import json
import contextlib
import secrets
import string
from datetime import datetime
from typing import Optional, List, Dict
from loguru import logger

class Database:
    """Asosiy ma'lumotlar bazasi klassi (Async)"""

    def __init__(self):
        self.host = os.getenv("DB_HOST", "mysql")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.user = os.getenv("DB_USERNAME", "tozalash_user")
        self.password = os.getenv("DB_PASSWORD", "tozalash_password")
        self.db_name = os.getenv("DB_DATABASE", "tozalash_db")
        self.pool = None
        self._lock: Optional[asyncio.Lock] = None

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def get_pool(self) -> aiosqlite.Pool:
        if self.pool is None:
            raise RuntimeError("Database connection pool is not initialized.")
        return self.pool

    
    @contextlib.asynccontextmanager
    async def get_conn(self):
        if self.pool is None:
            async with self.lock:
                if self.pool is None:
                    try:
                        # Qisqa timeout (3 soniya) Docker qotib qolganini darhol aniqlash uchun
                        self.pool = await asyncio.wait_for(
                            aiosqlite.create_pool(
                                host=self.host,
                                port=self.port,
                                user=self.user,
                                password=self.password,
                                db=self.db_name,
                                cursorclass=aiosqlite.Row,
                                autocommit=True,
                                charset="utf8mb4",
                                minsize=5,
                                maxsize=20,
                                connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", 3)),
                            ),
                            timeout=float(os.getenv("DB_POOL_TIMEOUT", 5.0)),
                        )
                    except asyncio.TimeoutError:
                        logger.error(
                            "!!! DIQQAT !!! MySQL serverga ulanish vaqti tugadi (Timeout)."
                        )
                        logger.error(
                            "Buning sababi: Windows kompyuteringizdagi Docker Desktop qotib qolgan va 3306 portini band qilib turibdi."
                        )
                        logger.error(
                            "Iltimos, Docker Desktop'ni qayta ishga tushiring yoki kompyuterni o'chirib yoqing."
                        )
                        raise ConnectionError(
                            "Docker qotib qolgan. MySQL ishlamayapti."
                        )
                    except Exception as e:
                        logger.error(f"Failed to create DB pool: {e}")
                        logger.error(
                            "MySQL konteyneri ishlayotganiga ishonch hosil qiling (docker-compose up -d mysql)."
                        )
                        raise

        async with self.pool.acquire() as conn:
            yield conn

    async def init_db(self):
        """Barcha jadvallarni asinxron yaratish va migratsiyalarni yuritish"""
        try:
            from migrations_runner import run_migrations

            await run_migrations(self)
        except Exception as e:
            logger.error(f"Migratsiya jarayonida xato: {e}")
            raise

    # ================================================
    # MIJOZLAR METODLARI
    # ================================================
    async def get_or_create_client(
        self,
        telegram_id: str,
        name: str = None,
        language: str = "uz",
        referrer_code: str = None,
    ) -> Dict:
        async with self.get_conn() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM clients WHERE telegram_id = ? FOR UPDATE",
                        (str(telegram_id),),
                    )
                    client = await cursor.fetchone()

                    if client:
                        await cursor.execute(
                            "UPDATE clients SET last_activity = ? WHERE telegram_id = ?",
                            (datetime.now(), str(telegram_id)),
                        )
                        await conn.commit()
                        client["last_activity"] = datetime.now()
                        return dict(client)
                    else:
                        my_referral_code = "".join(
                            secrets.choice(string.ascii_uppercase + string.digits)
                            for _ in range(6)
                        )
                        referred_by_id = None

                        if referrer_code:
                            await cursor.execute(
                                "SELECT id FROM clients WHERE referral_code = ?",
                                (referrer_code,),
                            )
                            referrer = await cursor.fetchone()
                            if referrer:
                                referred_by_id = referrer["id"]

                        try:
                            await cursor.execute(
                                """
                                INSERT INTO clients (telegram_id, name, language, referral_code, referred_by)
                                VALUES (?, ?, ?, ?, ?)
                            """,
                                (
                                    str(telegram_id),
                                    name or "Mijoz",
                                    language,
                                    my_referral_code,
                                    referred_by_id,
                                ),
                            )
                            if referred_by_id:
                                await cursor.execute(
                                    "UPDATE clients SET loyalty_points = loyalty_points + 50000 WHERE id = ?",
                                    (referred_by_id,)
                                )
                                logger.info(f"Referral bonus 50,000 UZS given to client ID {referred_by_id}")

                        except aiosqlite.IntegrityError:
                            # Poyga holati (race condition): Boshqa jarayon allaqachon yaratib bo'ldi
                            pass

                        await cursor.execute(
                            "SELECT * FROM clients WHERE telegram_id = ?",
                            (str(telegram_id),),
                        )
                        new_client = dict(await cursor.fetchone())
                        await conn.commit()
                        return new_client
            except Exception as e:
                await conn.rollback()
                logger.error(f"Error in get_or_create_client: {e}")
                raise

    # M3: SQL injection whitelist — faqat shu ustun nomlariga ruxsat beriladi
    _CLIENT_UPDATABLE_COLUMNS = frozenset(
        {
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
        }
    )

    async def update_client(self, telegram_id: str, **kwargs):
        """Mijoz ma'lumotlarini yangilash (M3: whitelist SQL injection himoyasi bilan)."""
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    # M3 FIX: isidentifier() o'rniga qattiq whitelist
                    valid_keys = {
                        k: v
                        for k, v in kwargs.items()
                        if k in self._CLIENT_UPDATABLE_COLUMNS
                    }
                    if not valid_keys:
                        logger.warning(
                            f"update_client: hech qanday yaroqli ustun topilmadi. kwargs={list(kwargs.keys())}"
                        )
                        return
                    updates = ", ".join([f"`{k}` = ?" for k in valid_keys.keys()])
                    values = list(valid_keys.values()) + [str(telegram_id)]
                    await cursor.execute(
                        f"UPDATE clients SET {updates} WHERE telegram_id = ?",
                        tuple(values),
                    )
            except Exception as e:
                logger.error(f"Error in update_client: {e}")
                raise

    async def update_client_name(self, telegram_id: str, name: str):
        await self.update_client(telegram_id, name=name)

    # ================================================
    # BUYURTMALAR METODLARI
    # ================================================
    async def create_order(self, data: Dict) -> Dict:
        async with self.get_conn() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cursor:
                    today = datetime.now().strftime("%Y%m%d")
                    order_number = f"TS-{today}-{secrets.token_hex(2).upper()}"

                    await cursor.execute(
                        """
                        INSERT INTO orders (
                            order_number, client_id, client_telegram_id, service_type,
                            service_name, quantity, unit, price_per_unit, surge_multiplier, total_price,
                            address, scheduled_date, scheduled_time, notes, is_eco_friendly, custom_checklist
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            order_number,
                            data.get("client_id"),
                            data.get("client_telegram_id"),
                            data.get("service_type"),
                            data.get("service_name"),
                            data.get("quantity"),
                            data.get("unit"),
                            data.get("price_per_unit"),
                            data.get("surge_multiplier", 1.0),
                            data.get("total_price"),
                            data.get("address"),
                            data.get("scheduled_date"),
                            data.get("scheduled_time"),
                            data.get("notes"),
                            data.get("is_eco_friendly", False),
                            data.get("custom_checklist", ""),
                        ),
                    )
                    order_id = cursor.lastrowid

                    await cursor.execute(
                        """
                        INSERT INTO finance (type, category, amount, description, order_id, date)
                        VALUES ('daromad', 'buyurtma', ?, ?, ?, CURDATE())
                    """,
                        (
                            data.get("total_price"),
                            f"Buyurtma #{order_number}",
                            order_id,
                        ),
                    )

                    await cursor.execute(
                        """
                        UPDATE clients 
                        SET total_orders = total_orders + 1, 
                            total_spent = total_spent + ?
                        WHERE telegram_id = ?
                    """,
                        (
                            data.get("total_price", 0),
                            str(data.get("client_telegram_id")),
                        ),
                    )

                    await cursor.execute(
                        "SELECT total_orders, referred_by FROM clients WHERE telegram_id = ? FOR UPDATE",
                        (str(data.get("client_telegram_id")),),
                    )
                    client_after = await cursor.fetchone()

                    if (
                        client_after
                        and client_after["total_orders"] == 1
                        and client_after["referred_by"]
                    ):
                        reward_points = 50
                        await cursor.execute(
                            """
                            UPDATE clients SET loyalty_points = loyalty_points + ? WHERE id = ?
                        """,
                            (reward_points, client_after["referred_by"]),
                        )

                    await cursor.execute(
                        "SELECT * FROM orders WHERE id = ?", (order_id,)
                    )
                    order_dict = dict(await cursor.fetchone())

                await conn.commit()
                return order_dict
            except Exception as e:
                await conn.rollback()
                logger.error(f"Error in create_order: {e}")
                raise

    async def get_client_orders(self, telegram_id: str, limit: int = 5) -> List[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT * FROM orders 
                        WHERE client_telegram_id = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """,
                        (str(telegram_id), limit),
                    )
                    return [dict(row) for row in await cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error in get_client_orders: {e}")
                return []

    async def get_order(self, order_id: int) -> Optional[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM orders WHERE id = ?", (order_id,)
                    )
                    row = await cursor.fetchone()
                    if not row:
                        return None

                    # Also fetch assigned workers
                    await cursor.execute(
                        """
                        SELECT w.* FROM workers w 
                        JOIN order_workers ow ON w.id = ow.worker_id 
                        WHERE ow.order_id = ?
                    """,
                        (order_id,),
                    )
                    workers = await cursor.fetchall()
                    row_dict = dict(row)
                    row_dict["workers"] = [dict(w) for w in workers]
                    return row_dict
            except Exception as e:
                logger.error(f"Error in get_order: {e}")
                return None

    async def update_order_status(
        self, order_id: int, status: str, worker_ids: List[int] = None
    ):
        async with self.get_conn() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cursor:
                    if worker_ids is not None:
                        # Normalize worker assignments
                        await cursor.execute(
                            "DELETE FROM order_workers WHERE order_id = ?", (order_id,)
                        )
                        for wid in worker_ids:
                            await cursor.execute(
                                "INSERT INTO order_workers (order_id, worker_id) VALUES (?, ?)",
                                (order_id, wid),
                            )

                    await cursor.execute(
                        "UPDATE orders SET status = ? WHERE id = ?",
                        (status, order_id),
                    )

                    if status == "bajarildi":
                        await cursor.execute(
                            "UPDATE orders SET completed_at = ? WHERE id = ?",
                            (datetime.now(), order_id),
                        )
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                logger.error(f"Error in update_order_status: {e}")
                raise

    async def get_today_orders(self) -> List[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT o.*, c.name as client_name, c.phone as client_phone
                        FROM orders o
                        LEFT JOIN clients c ON o.client_telegram_id = c.telegram_id
                        WHERE DATE(o.created_at) = CURDATE()
                        ORDER BY o.created_at DESC
                    """)
                    return [dict(row) for row in await cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error in get_today_orders: {e}")
                return []

    async def get_orders_stats(self, days: int = 30) -> Dict:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT 
                            COUNT(*) as total_orders,
                            SUM(total_price) as total_revenue,
                            AVG(total_price) as avg_order_value,
                            COUNT(CASE WHEN status = 'bajarildi' THEN 1 END) as completed,
                            COUNT(CASE WHEN status = 'yangi' THEN 1 END) as new_orders
                        FROM orders
                        WHERE created_at >= DATE_SUB(NOW(), INTERVAL ? DAY)
                    """,
                        (days,),
                    )
                    return dict(await cursor.fetchone())
            except Exception as e:
                logger.error(f"Error in get_orders_stats: {e}")
                return {}

    # ================================================
    # ISHCHILAR METODLARI
    # ================================================
    async def get_available_workers(self) -> List[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT * FROM workers 
                        WHERE is_active = 1 AND is_available = 1
                        ORDER BY rating DESC
                    """)
                    return [dict(row) for row in await cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error in get_available_workers: {e}")
                return []

    async def get_all_workers(self) -> List[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT * FROM workers WHERE is_active = 1")
                    return [dict(row) for row in await cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error in get_all_workers: {e}")
                return []

    async def add_worker(
        self,
        name: str,
        phone: str,
        telegram_id: str,
        telegram_username: str = None,
        specialization: str = None,
    ):
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT IGNORE INTO workers (name, phone, telegram_id, telegram_username, specialization)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            name,
                            phone,
                            str(telegram_id),
                            telegram_username,
                            specialization,
                        ),
                    )
            except Exception as e:
                logger.error(f"Error in add_worker: {e}")
                raise

    async def update_worker_location(self, telegram_id: str, lat: float, lon: float):
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        UPDATE workers SET gps_lat = ?, gps_lon = ?, last_location_update = ?
                        WHERE telegram_id = ?
                    """,
                        (lat, lon, datetime.now(), str(telegram_id)),
                    )
            except Exception as e:
                logger.error(f"Error in update_worker_location: {e}")
                raise

    # ================================================
    # FOYDALANUVCHI HOLATI (State Machine)
    # ================================================
    async def get_user_state(self, telegram_id: str) -> Dict:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM user_states WHERE telegram_id = ?",
                        (str(telegram_id),),
                    )
                    row = await cursor.fetchone()
                    if row:
                        state_data = dict(row)
                        if state_data.get("context"):
                            state_data["context"] = json.loads(state_data["context"])
                        return state_data
                    return {
                        "telegram_id": str(telegram_id),
                        "state": "idle",
                        "context": {},
                    }
            except Exception as e:
                logger.error(f"Error in get_user_state: {e}")
                return {"telegram_id": str(telegram_id), "state": "idle", "context": {}}

    async def set_user_state(self, telegram_id: str, state: str, context: Dict = None):
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    context_json = json.dumps(context or {}, ensure_ascii=False)
                    await cursor.execute(
                        """
                        REPLACE INTO user_states (telegram_id, state, context)
                        VALUES (?, ?, ?)
                    """,
                        (str(telegram_id), state, context_json),
                    )
            except Exception as e:
                logger.error(f"Error in set_user_state: {e}")
                raise

    # ================================================
    # LOYALLIK VA GAMIFIKATSIYA
    # ================================================
    async def update_loyalty_coins(self, telegram_id: str, amount: float):
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE clients SET loyalty_coins = loyalty_coins + ? WHERE telegram_id = ?",
                        (amount, str(telegram_id))
                    )
            except Exception as e:
                logger.error(f"Error in update_loyalty_coins: {e}")
                raise

    # ================================================
    # RAQOBATCHILAR NARXLARI
    # ================================================
    async def save_competitor_price(self, competitor_name: str, service_name: str, price: float, source_url: str = None):
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO competitor_prices (competitor_name, service_name, price, source_url)
                        VALUES (?, ?, ?, ?)
                        """,
                        (competitor_name, service_name, price, source_url)
                    )
            except Exception as e:
                logger.error(f"Error in save_competitor_price: {e}")
                raise

    async def get_competitor_prices(self, service_name: str) -> List[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM competitor_prices WHERE service_name = ? ORDER BY detected_at DESC, created_at DESC",
                        (service_name,)
                    )
                    return [dict(row) for row in await cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error in get_competitor_prices: {e}")
                return []

    # ================================================
    # SUHBAT TARIXI
    # ================================================
    async def save_message(
        self,
        telegram_id: str,
        role: str,
        message: str,
        state: str = None,
        platform: str = "telegram",
    ):
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO conversations (telegram_id, platform, role, message, state)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (str(telegram_id), platform, role, message, state),
                    )
            except Exception as e:
                logger.error(f"Error in save_message: {e}")

    async def get_conversation_history(
        self, telegram_id: str, limit: int = 10
    ) -> List[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT role, message FROM conversations
                        WHERE telegram_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """,
                        (str(telegram_id), limit),
                    )
                    rows = await cursor.fetchall()
                    return [
                        {"role": r["role"], "message": r["message"]}
                        for r in reversed(rows)
                    ]
            except Exception as e:
                logger.error(f"Error in get_conversation_history: {e}")
                return []

    # ================================================
    # AI O'RGANISH
    # ================================================
    async def save_learning(
        self,
        context_type: str,
        input_data: str,
        output_data: str,
        success: bool,
        feedback_score: float = None,
        improvement: str = None,
    ):
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO ai_learning (context_type, input_data, output_data, success, feedback_score, improvement)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            context_type,
                            input_data,
                            output_data,
                            int(success),
                            feedback_score,
                            improvement,
                        ),
                    )
            except Exception as e:
                logger.error(f"Error in save_learning: {e}")

    async def get_successful_patterns(
        self, context_type: str = "general", limit: int = 5
    ) -> List[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT input_data, output_data, feedback_score
                        FROM ai_learning
                        WHERE context_type = ? AND success = 1
                        ORDER BY feedback_score DESC, created_at DESC
                        LIMIT ?
                    """,
                        (context_type, limit),
                    )
                    return [dict(row) for row in await cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error in get_successful_patterns: {e}")
                return []

    async def get_dynamic_guidelines(self) -> List[str]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT improvement
                        FROM ai_learning
                        WHERE improvement IS NOT NULL AND improvement != ''
                        ORDER BY created_at ASC
                        """
                    )
                    return [row["improvement"] for row in await cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error in get_dynamic_guidelines: {e}")
                return []

    # ================================================
    # ISHCHILAR
    # ================================================
    async def get_worker_by_tg_id(self, telegram_id: str) -> Optional[Dict]:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM workers WHERE telegram_id = ?",
                        (str(telegram_id),),
                    )
                    row = await cursor.fetchone()
                    return dict(row) if row else None
            except Exception as e:
                logger.error(f"Error in get_worker_by_tg_id: {e}")
                return None

    async def register_worker(
        self, telegram_id: str, name: str, phone: str = None, username: str = None
    ) -> Dict:
        async with self.get_conn() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM workers WHERE telegram_id = ? FOR UPDATE",
                        (str(telegram_id),),
                    )
                    worker = await cursor.fetchone()

                    if worker:
                        await cursor.execute(
                            """
                            UPDATE workers 
                            SET name = ?, phone = ?, telegram_username = ? 
                            WHERE telegram_id = ?
                        """,
                            (name, phone, username, str(telegram_id)),
                        )
                    else:
                        await cursor.execute(
                            """
                            INSERT INTO workers (telegram_id, name, phone, telegram_username)
                            VALUES (?, ?, ?, ?)
                        """,
                            (str(telegram_id), name, phone, username),
                        )

                    await cursor.execute(
                        "SELECT * FROM workers WHERE telegram_id = ?",
                        (str(telegram_id),),
                    )
                    worker_dict = dict(await cursor.fetchone())

                await conn.commit()
                return worker_dict
            except Exception as e:
                await conn.rollback()
                logger.error(f"Error in register_worker: {e}")
                raise

    # ================================================
    # MOLIYA
    # ================================================
    async def get_finance_stats(self) -> Dict:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT
                            SUM(CASE WHEN type = 'daromad' AND date = CURDATE() THEN amount ELSE 0 END) as today_revenue,
                            SUM(CASE WHEN type = 'daromad' AND DATE_FORMAT(date, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m') THEN amount ELSE 0 END) as month_revenue,
                            SUM(CASE WHEN type = 'daromad' THEN amount ELSE 0 END) as total_revenue
                        FROM finance
                    """)
                    return dict(await cursor.fetchone())
            except Exception as e:
                logger.error(f"Error in get_finance_stats: {e}")
                return {}

    # ================================================
    # KUNLIK HISOBOT
    # ================================================
    async def save_daily_report(self, report_data: Dict):
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    today = datetime.now().strftime("%Y-%m-%d")
                    await cursor.execute(
                        """
                        REPLACE INTO daily_reports (
                            report_date, orders_count, completed_orders, total_revenue,
                            new_clients, messages_received, messages_answered,
                            ai_improvements, competitor_insights, tomorrow_plan
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            today,
                            report_data.get("orders_count", 0),
                            report_data.get("completed_orders", 0),
                            report_data.get("total_revenue", 0),
                            report_data.get("new_clients", 0),
                            report_data.get("messages_received", 0),
                            report_data.get("messages_answered", 0),
                            json.dumps(
                                report_data.get("ai_improvements", []),
                                ensure_ascii=False,
                            ),
                            json.dumps(
                                report_data.get("competitor_insights", {}),
                                ensure_ascii=False,
                            ),
                            report_data.get("tomorrow_plan", ""),
                        ),
                    )
            except Exception as e:
                logger.error(f"Error in save_daily_report: {e}")

    async def get_messages_count_today(self) -> int:
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT COUNT(*) as cnt FROM conversations
                        WHERE DATE(created_at) = CURDATE() AND role = 'user'
                    """)
                    row = await cursor.fetchone()
                    return row["cnt"]
            except Exception as e:
                logger.error(f"Error in get_messages_count_today: {e}")
                return 0

    async def archive_old_sessions(self, days: int = 7) -> int:
        """Eski (belgilangan kundan oshgan) user_states larni tozalash"""
        async with self.get_conn() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        DELETE FROM user_states
                        WHERE updated_at < DATE_SUB(NOW(), INTERVAL ? DAY)
                    """, (days,))
                    deleted_count = cursor.rowcount
                    logger.info(f"{deleted_count} ta eski sessiya arxivlandi/o'chirildi.")
                    return deleted_count
            except Exception as e:
                logger.error(f"Error in archive_old_sessions: {e}")
                return 0


# Global database instance
db = Database()


async def get_db():
    yield db
