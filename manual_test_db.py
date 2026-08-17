import asyncio
from unittest.mock import patch, MagicMock
import sys
import os

import database
import migrations_runner


class MockCursor:
    def __init__(self):
        self.execute_calls = []
        self.execute = self.mock_execute

    async def mock_execute(self, query, args=None):
        self.execute_calls.append((query, args))

    async def fetchall(self):
        return []

    async def fetchone(self):
        return {"count": 0}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockConn:
    def __init__(self):
        self.cursor_obj = MockCursor()

    def cursor(self):
        return self.cursor_obj

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockPool:
    def __init__(self):
        self.conn = MockConn()

    def acquire(self):
        return self.conn

    async def close(self):
        pass

    async def wait_closed(self):
        pass


async def test_create():
    print("Testing Database Migrations and DB Connection Pattern...")

    mock_pool = MockPool()

    async def mock_create_pool(*args, **kwargs):
        return mock_pool

    with patch("aiomysql.create_pool", new=mock_create_pool):
        # 1. Test database initialization
        db = database.Database()

        # 2. Test running migrations
        await db.init_db()
        print("init_db() successfully invoked migrations_runner.py")

        # Verify that cursor.execute was called with schema creation
        execute_calls = mock_pool.conn.cursor_obj.execute_calls
        assert len(execute_calls) > 0, "No SQL queries were executed during init_db()"

        # Extract all query strings
        queries = [call[0] for call in execute_calls]

        # Verify schema_migrations table creation was executed
        assert any("CREATE TABLE IF NOT EXISTS schema_migrations" in q for q in queries)
        print("schema_migrations logic executed")

        # Verify the migration sql file contents were executed
        # migrations/001_initial.sql has 'CREATE TABLE IF NOT EXISTS clients'
        assert any("clients" in q for q in queries)
        print("001_initial.sql logic executed")

        # 3. Test get_conn context manager pattern
        async with db.get_conn() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                print("get_conn() connection pattern works correctly")

    print("All database and migration tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(test_create())
