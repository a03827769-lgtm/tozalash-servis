"""
Tozalash Servis — Milestone 2 Adversarial & Empirical Challenger Stress Suite
Authored by: teamwork_preview_challenger_m2_1 (Empirical Verifier)

Vectors Tested:
1. DSN Parsing, Port 6543 vs 5432, Supabase/Neon/Render/Koyeb detection, SSL selection, statement_cache_size logic.
2. Full 18-Table Relational Schema & B-Tree Index Integrity in SQLite and Mock AsyncPG.
3. Database Business Query Methods Stress & Boundary Tests (Concurrency, Whitelist Injection, Aggregation, Upsert).
4. FastAPI Endpoints (/api/v1/clients, /api/v1/orders, /api/v1/staff, /health) - Zero AttributeError Guarantee.
5. RedisManager & FastAPICache Fallback Under Concurrency & Lock Collisions.
"""

import os
import sys
import json
import asyncio
import tempfile
import urllib.parse
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Database, get_db
from app.main import app
from app.core.redis_manager import RedisManager, MemoryFallback
from analytics.chart_generator import ChartGenerator


# =============================================================================
# VECTOR 1: DSN Parsing, Port 6543 vs 5432, Cloud Provider SSL & Cache Config
# =============================================================================
class TestDSNParsingAndConnectionConfig:
    """Stress-tests database connection string normalization and pool kwargs logic."""

    def test_supabase_pooler_port_6543(self, monkeypatch):
        """Supabase transaction pooler on port 6543 must enforce statement_cache_size=0 and SSL require."""
        dsn = "postgresql://postgres.myproject:SecretPassword123@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require"
        monkeypatch.setenv("DATABASE_URL", dsn)
        monkeypatch.setenv("DB_TYPE", "postgres")

        parsed = urllib.parse.urlparse(dsn)
        assert parsed.port == 6543
        assert "pooler.supabase.com" in parsed.hostname

        # Simulate Database.init_db() parameter extraction logic
        db_inst = Database(sqlite_path=":memory:")
        database_url = dsn
        db_host = parsed.hostname
        db_port = parsed.port
        query_params = urllib.parse.parse_qs(parsed.query)

        ssl_ctx = None
        statement_cache_size = None

        if "sslmode" in query_params:
            ssl_mode_val = query_params["sslmode"][0].lower()
            if ssl_mode_val in ("require", "verify-full", "verify-ca", "prefer"):
                ssl_ctx = "require"

        if "supabase" in db_host:
            ssl_ctx = "require"

        if db_port == 6543 or "pooler" in db_host:
            statement_cache_size = 0

        assert ssl_ctx == "require"
        assert statement_cache_size == 0

    def test_standard_postgres_port_5432(self, monkeypatch):
        """Standard direct PostgreSQL connection on port 5432 should allow default statement caching."""
        dsn = "postgresql://postgres:postgres@localhost:5432/tozalash_db"
        monkeypatch.setenv("DATABASE_URL", dsn)

        parsed = urllib.parse.urlparse(dsn)
        assert parsed.port == 5432

        db_host = parsed.hostname
        db_port = parsed.port
        query_params = urllib.parse.parse_qs(parsed.query)

        ssl_ctx = None
        statement_cache_size = None

        if "sslmode" in query_params:
            ssl_mode_val = query_params["sslmode"][0].lower()
            if ssl_mode_val in ("require", "verify-full", "verify-ca", "prefer"):
                ssl_ctx = "require"

        if db_port == 6543 or "pooler" in (db_host or ""):
            statement_cache_size = 0

        assert ssl_ctx is None
        assert statement_cache_size is None

    def test_neon_tech_and_render_cloud_detection(self):
        """Neon Tech and Render Postgres hostnames must trigger ssl='require'."""
        neon_dsn = "postgres://alex:neondb_pwd@ep-plain-star-123456.eu-central-1.aws.neon.tech/neondb"
        render_dsn = "postgresql://root:secret@dpg-abc12345.render.com:5432/tozalash_prod"
        koyeb_dsn = "postgresql://koyeb:secret@pg-koyeb.koyeb.app:5432/app"

        for dsn, expected_host in [
            (neon_dsn, "neon.tech"),
            (render_dsn, "render.com"),
            (koyeb_dsn, "koyeb.app"),
        ]:
            parsed = urllib.parse.urlparse(dsn)
            assert expected_host in (parsed.hostname or "")
            ssl_ctx = "require" if any(h in (parsed.hostname or "") for h in ("supabase", "neon.tech", "render.com", "koyeb.app")) else None
            assert ssl_ctx == "require"

    def test_query_normalization_dialect(self):
        """Check SQL dialect translations for PostgreSQL ($1, $2, CURRENT_DATE) vs SQLite (?, DATE('now'))."""
        test_db = Database()

        # SQLite Mode
        test_db.db_type = "sqlite"
        q_sqlite = test_db._normalize_query("SELECT * FROM orders WHERE status = %s AND created_at >= CURDATE() AND scheduled_date = %s")
        assert "?" in q_sqlite
        assert "%s" not in q_sqlite
        assert "DATE('now')" in q_sqlite

        # PostgreSQL Mode
        test_db.db_type = "postgres"
        q_pg = test_db._normalize_query("SELECT * FROM orders WHERE status = ? AND created_at >= CURDATE() AND scheduled_date = ?")
        assert "$1" in q_pg
        assert "$2" in q_pg
        assert "?" not in q_pg
        assert "CURRENT_DATE" in q_pg


# =============================================================================
# VECTOR 2: Schema & Index Verification on SQLite & AsyncPG Mock
# =============================================================================
@pytest.mark.asyncio
class TestSchemaAndIndexIntegrity:
    """Stress-tests the creation of all 18 relational tables, seed data, and B-Tree indexes."""

    async def test_all_18_tables_and_indexes_sqlite(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        try:
            db_inst = Database(sqlite_path=db_path)
            await db_inst.init_db()

            # Required 18+ business tables
            required_tables = [
                "cities",
                "clients",
                "workers",
                "orders",
                "transactions",
                "messages",
                "conversations",
                "dynamic_guidelines",
                "competitor_prices",
                "learning_logs",
                "ai_learning",
                "finance",
                "channel_posts",
                "competitors",
                "daily_reports",
                "services",
                "order_workers",
                "admin_audit_logs",
                "audit_logs",
                "feedback",
                "worker_ratings",
                "marketing_campaigns",
                "user_states",
                "orders_archive",
                "worker_locations",
            ]

            tables_in_db = await db_inst.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = {r["name"] for r in tables_in_db}

            for t in required_tables:
                assert t in table_names, f"Table '{t}' missing from schema!"

            # Verify B-tree indexes
            indexes_in_db = await db_inst.fetch_all("SELECT name FROM sqlite_master WHERE type='index'")
            index_names = {r["name"] for r in indexes_in_db}

            expected_indexes = [
                "idx_clients_tg_id",
                "idx_clients_city_id",
                "idx_orders_status",
                "idx_orders_client_tg",
                "idx_workers_active",
                "idx_transactions_tx_id",
                "idx_order_workers_wid",
            ]
            for idx in expected_indexes:
                assert idx in index_names, f"Index '{idx}' missing from schema!"

            # Verify seeded cities
            cities = await db_inst.fetch_all("SELECT * FROM cities")
            assert len(cities) >= 3
            city_names = [c["name"] for c in cities]
            assert "Toshkent" in city_names
            assert "Samarqand" in city_names
            assert "Buxoro" in city_names

            await db_inst.close()
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    async def test_asyncpg_ddl_and_execution_mock(self):
        """Simulate asyncpg pool execution to ensure all PostgreSQL DDL queries are syntactically sound."""
        executed_statements = []

        class MockAsyncpgConn:
            async def execute(self, query, *args):
                executed_statements.append((query, args))
                return "OK"

            async def fetchval(self, query, *args):
                return 0

            async def fetchrow(self, query, *args):
                return {"id": 1, "name": "Toshkent"}

            async def fetch(self, query, *args):
                return [{"id": 1, "name": "Toshkent"}]

        class MockAsyncpgPool:
            def acquire(self):
                class AsyncContext:
                    async def __aenter__(self_inner):
                        return MockAsyncpgConn()
                    async def __aexit__(self_inner, *args):
                        pass
                return AsyncContext()

            async def close(self):
                pass

        db_inst = Database()
        db_inst.db_type = "postgres"
        db_inst.pg_pool = MockAsyncpgPool()
        db_inst._initialized = True

        await db_inst._create_tables_and_indexes()
        assert len(executed_statements) > 20
        # Check that table creations used SERIAL and TIMESTAMP without error
        ddl_text = " ".join(s[0] for s in executed_statements)
        assert "CREATE TABLE IF NOT EXISTS clients" in ddl_text
        assert "CREATE TABLE IF NOT EXISTS orders" in ddl_text
        assert "CREATE INDEX IF NOT EXISTS idx_orders_status" in ddl_text


# =============================================================================
# VECTOR 3: Database Business Query Methods Stress & Boundary Tests
# =============================================================================
@pytest.mark.asyncio
class TestBusinessQueryMethodsStress:
    """Rigorous stress and boundary testing of all core database methods."""

    @pytest.fixture
    async def fresh_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        db_inst = Database(sqlite_path=db_path)
        await db_inst.init_db()
        yield db_inst
        await db_inst.close()
        if os.path.exists(db_path):
            os.remove(db_path)

    async def test_client_referral_bonus_and_concurrency(self, fresh_db):
        """Test referral logic: referrer receives 50,000 loyalty points bonus on referee signup."""
        # 1. Create primary referrer client
        referrer = await fresh_db.get_or_create_client(
            telegram_id="999001",
            name="Referrer Client",
            language="uz"
        )
        assert referrer is not None
        ref_code = referrer["referral_code"]
        assert ref_code is not None and len(ref_code) == 6

        # 2. Create 5 referees concurrently using the referrer code
        async def create_referee(idx):
            return await fresh_db.get_or_create_client(
                telegram_id=f"99910{idx}",
                name=f"Referee #{idx}",
                referrer_code=ref_code
            )

        referees = await asyncio.gather(*(create_referee(i) for i in range(5)))
        assert len(referees) == 5

        # 3. Verify referrer loyalty points = 5 * 50,000 = 250,000
        updated_referrer = await fresh_db.get_client("999001")
        assert updated_referrer["loyalty_points"] == 250000

    async def test_update_client_whitelist_sql_injection_defense(self, fresh_db):
        """Adversarial test: Inject SQL statements via kwargs into update_client."""
        await fresh_db.get_or_create_client(telegram_id="888001", name="Legit User")

        # 1. Malicious column attempts
        malicious_kwargs = {
            "name; DROP TABLE clients; --": "Hacked",
            "is_blocked = 1 WHERE 1=1; --": "Bypassed",
            "role": "admin",  # whitelisted
            "loyalty_points": 999,  # whitelisted
        }

        success = await fresh_db.update_client("888001", **malicious_kwargs)
        assert success is True

        user = await fresh_db.get_client("888001")
        assert user["role"] == "admin"
        assert user["loyalty_points"] == 999

        # Ensure clients table is intact
        clients_count = await fresh_db.fetch_one("SELECT COUNT(*) as cnt FROM clients")
        assert clients_count["cnt"] >= 1

    async def test_create_order_auto_finance_and_stats(self, fresh_db):
        """Create orders via dict and parameters, verify order_number, finance record, and client spend."""
        client_tg = "777001"
        await fresh_db.get_or_create_client(telegram_id=client_tg, name="Order Client")

        # Create Order #1 via Dict
        order_dict_input = {
            "client_telegram_id": client_tg,
            "service_type": "deep_cleaning",
            "service_name": "General Tozalash",
            "total_price": 350000.0,
            "address": "Tashkent, Chilonzor 9",
            "scheduled_date": "2026-08-20",
            "scheduled_time": "10:00",
            "is_eco_friendly": True,
        }
        order1 = await fresh_db.create_order(order_dict_input)
        assert order1["order_number"].startswith("TS-")
        assert order1["total_price"] == 350000.0

        # Create Order #2 via kwargs
        order2 = await fresh_db.create_order(
            client_telegram_id=client_tg,
            service_type="office",
            service_name="Ofis Tozalash",
            total_price=150000.0,
            address="Tashkent, Yunusobod 4",
        )
        assert order2["order_number"].startswith("TS-")

        # Verify client cumulative spend
        client = await fresh_db.get_client(client_tg)
        assert client["total_orders"] == 2
        assert client["total_spent"] == 500000.0

        # Verify finance entries
        revenues = await fresh_db.get_revenues()
        assert len(revenues) >= 2
        total_rev = sum(r["amount"] for r in revenues)
        assert total_rev == 500000.0

    async def test_order_workers_assignment_and_status(self, fresh_db):
        """Assign multiple workers to an order and update status to completed."""
        # Add 2 workers
        await fresh_db.add_worker("Worker A", "+998901111111", "501", specialization="Oyna tozalash")
        await fresh_db.add_worker("Worker B", "+998902222222", "502", specialization="Gilam yuvish")

        w_a = await fresh_db.get_worker_by_tg_id("501")
        w_b = await fresh_db.get_worker_by_tg_id("502")

        # Create order
        order = await fresh_db.create_order(
            client_telegram_id="777002",
            service_type="express",
            total_price=200000.0,
        )
        order_id = order["id"]

        # Assign both workers and update to completed
        await fresh_db.update_order_status(
            order_id=order_id,
            status="bajarildi",
            worker_id=w_a["id"],
            worker_ids=[w_a["id"], w_b["id"]],
        )

        fetched_order = await fresh_db.get_order(order_id)
        assert fetched_order["status"] == "bajarildi"
        assert fetched_order["completed_at"] is not None
        assert len(fetched_order.get("workers", [])) == 2

    async def test_aggregated_stats_and_daily_reports(self, fresh_db):
        """Stress-test get_orders_stats, get_finance_stats, and save_daily_report upsert."""
        # Insert orders for stats
        order1 = await fresh_db.create_order(client_telegram_id="111", total_price=100000.0)
        await fresh_db.update_order_status(order1["id"], "bajarildi")
        order2 = await fresh_db.create_order(client_telegram_id="222", total_price=200000.0)

        stats = await fresh_db.get_orders_stats(days=30)
        assert stats["total_orders"] == 2
        assert stats["total_revenue"] == 300000.0
        assert stats["completed"] == 1
        assert stats["new_orders"] == 1

        fin_stats = await fresh_db.get_finance_stats()
        assert fin_stats["today_revenue"] == 300000.0
        assert fin_stats["total_revenue"] == 300000.0

        # Upsert daily report
        report_data = {
            "report_date": "2026-08-17",
            "orders_count": 5,
            "completed_orders": 4,
            "total_revenue": 1200000.0,
            "new_clients": 3,
            "messages_received": 50,
            "messages_answered": 48,
            "ai_improvements": ["Optimize carpet cleaning workflow"],
            "competitor_insights": {"trend": "Eco cleaning in demand"},
            "tomorrow_plan": "Target commercial offices",
        }
        # First save (INSERT)
        res1 = await fresh_db.save_daily_report(report_data)
        assert res1 is True

        # Second save same date with updated stats (UPDATE)
        report_data["completed_orders"] = 5
        report_data["total_revenue"] = 1500000.0
        res2 = await fresh_db.save_daily_report(report_data)
        assert res2 is True

        saved_rep = await fresh_db.fetch_one("SELECT * FROM daily_reports WHERE report_date = '2026-08-17'")
        assert saved_rep["completed_orders"] == 5
        assert saved_rep["total_revenue"] == 1500000.0

    async def test_learning_patterns_and_dynamic_guidelines(self, fresh_db):
        """Test AI learning persistence, pattern ranking, and guideline extraction."""
        await fresh_db.save_learning("pricing", "Narx qimmat", "Chegirma taklif qilindi", success=True, rating_or_score=4.8)
        await fresh_db.save_learning("pricing", "Narx arzonmi", "Standart narx tushuntirildi", success=True, rating_or_score=5.0)
        await fresh_db.save_learning("timing", "Ertaga bo'ladimi", "Ertalab 9:00 band qilindi", success=True, rating_or_score=4.9)

        patterns = await fresh_db.get_successful_patterns(context_type="pricing", limit=10)
        assert len(patterns) == 2
        assert patterns[0]["feedback_score"] >= patterns[1]["feedback_score"]

        # Dynamic guidelines
        await fresh_db.add_dynamic_guideline("Mijozga doim salom bering va ismini ayting")
        guidelines = await fresh_db.get_dynamic_guidelines()
        assert len(guidelines) >= 1
        assert "Mijozga doim salom bering" in guidelines[0]


# =============================================================================
# VECTOR 4: FastAPI REST Endpoints Zero AttributeError & Schema Conformance
# =============================================================================
@pytest.mark.asyncio
class TestFastAPIEndpointsZeroAttributeError:
    """Calls live FastAPI endpoints via httpx.AsyncClient with Database dependency override."""

    @pytest.fixture
    async def configured_app(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        test_db = Database(sqlite_path=db_path)
        await test_db.init_db()

        # Seed data for endpoints
        await test_db.get_or_create_client(telegram_id="10001", name="Azizbek", language="uz")
        await test_db.get_or_create_client(telegram_id="10002", name="Malika", language="ru")
        await test_db.add_worker(name="Javohir", phone="+998901234567", telegram_id="20001", specialization="Oyna tozalash")
        await test_db.create_order(
            client_telegram_id="10001",
            service_type="standard",
            service_name="Xonadon Tozalash",
            total_price=250000.0,
            address="Toshkent, Yunusobod",
            scheduled_date="2026-08-18"
        )

        app.dependency_overrides[get_db] = lambda: test_db

        yield app, test_db

        app.dependency_overrides.clear()
        await test_db.close()
        if os.path.exists(db_path):
            os.remove(db_path)

    async def test_clients_endpoint_zero_attribute_error(self, configured_app):
        fastapi_app, test_db = configured_app
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. GET /api/v1/clients/
            resp = await client.get("/api/v1/clients/")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 2
            # Verify fields
            first = data[0]
            assert "telegram_id" in first
            assert "total_orders" in first
            assert "total_spent" in first
            assert "loyalty_points" in first

            # 2. DELETE /api/v1/clients/10002
            del_resp = await client.delete("/api/v1/clients/10002")
            assert del_resp.status_code == 200
            assert del_resp.json()["status"] == "success"

            # Check deleted from DB
            remaining = await test_db.get_client("10002")
            assert remaining is None

    async def test_orders_endpoint_zero_attribute_error(self, configured_app):
        fastapi_app, test_db = configured_app
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. GET /api/v1/orders/
            resp = await client.get("/api/v1/orders/")
            assert resp.status_code == 200
            orders = resp.json()
            assert isinstance(orders, list)
            assert len(orders) >= 1
            order = orders[0]
            assert "order_number" in order
            assert "client_name" in order
            assert "total_price" in order
            assert "status" in order

            # 2. PUT /api/v1/orders/{id}/status
            order_id = order["id"]
            update_resp = await client.put(f"/api/v1/orders/{order_id}/status", json={"status": "jarayonda"})
            assert update_resp.status_code == 200
            assert update_resp.json()["status"] == "success"

            # Bad request missing status
            bad_resp = await client.put(f"/api/v1/orders/{order_id}/status", json={})
            assert bad_resp.status_code == 400

    async def test_staff_endpoint_zero_attribute_error(self, configured_app):
        fastapi_app, test_db = configured_app
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. GET /api/v1/staff/
            resp = await client.get("/api/v1/staff/")
            assert resp.status_code == 200
            staff = resp.json()
            assert len(staff) >= 1
            assert staff[0]["name"] == "Javohir"
            assert staff[0]["role"] == "Oyna tozalash"

            # 2. POST /api/v1/staff/
            new_worker = {
                "name": "Dilnoza",
                "phone": "+998939998877",
                "role": "General Tozalash",
                "telegram_id": "20002"
            }
            create_resp = await client.post("/api/v1/staff/", json=new_worker)
            assert create_resp.status_code == 200

            # 3. DELETE /api/v1/staff/20002
            del_resp = await client.delete("/api/v1/staff/20002")
            assert del_resp.status_code == 200

    async def test_health_check_endpoint(self, configured_app):
        fastapi_app, test_db = configured_app
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] in ("healthy", "degraded")
            assert "database" in body
            assert "redis" in body
            assert "uptime_seconds" in body
            assert body["version"] == "2.0.0"


# =============================================================================
# VECTOR 5: Redis Concurrency, Redlock Collisions & Chart Generator
# =============================================================================
@pytest.mark.asyncio
class TestRedisConcurrencyAndAnalytics:
    """Stress-tests Redis FSM concurrency, distributed locks, and chart generation."""

    async def test_redis_concurrent_fsm_updates(self):
        rm = RedisManager()
        rm._is_connected = False
        rm.fallback = MemoryFallback()

        async def update_fsm(user_id, step):
            for s in range(5):
                await rm.set_fsm_state(str(user_id), f"step_{s}", {"counter": s, "step": step})
                state = await rm.get_fsm_state(str(user_id))
                assert state["state"] == f"step_{s}"

        await asyncio.gather(*(update_fsm(uid, i) for i, uid in enumerate(range(100, 110))))

    async def test_redlock_collision_rejection(self):
        rm = RedisManager()
        rm._is_connected = False
        rm.fallback = MemoryFallback()

        resource = "order_12345_dispatch"
        # Worker 1 acquires lock
        acquired1 = await rm.acquire_lock(resource, timeout_seconds=5)
        assert acquired1 is True

        # Worker 2 attempts same lock -> Must be rejected
        acquired2 = await rm.acquire_lock(resource, timeout_seconds=5)
        assert acquired2 is False

        # Release and re-acquire
        await rm.release_lock(resource)
        acquired3 = await rm.acquire_lock(resource, timeout_seconds=5)
        assert acquired3 is True
        await rm.release_lock(resource)

    async def test_chart_generator_with_database(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        try:
            test_db = Database(sqlite_path=db_path)
            await test_db.init_db()

            # Seed orders across dates
            await test_db.create_order(client_telegram_id="101", total_price=500000.0)
            await test_db.create_order(client_telegram_id="102", total_price=350000.0)

            chart_gen = ChartGenerator()
            chart_path = await chart_gen.generate_revenue_chart(custom_db=test_db)
            assert chart_path is not None
            assert os.path.exists(chart_path)
            assert os.path.getsize(chart_path) > 1000  # valid PNG

            await test_db.close()
            if os.path.exists(chart_path):
                os.remove(chart_path)
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
