import re
import os

with open("database.py", "r", encoding="utf-8") as f:
    code = f.read()

# Imports
code = code.replace("import aiosqlite", "import aiomysql\nimport os")

# Class init
init_sqlite = """    def __init__(self):
        self.db_path = DATABASE_PATH"""
init_mysql = """    def __init__(self):
        self.host = os.getenv("DB_HOST", "mysql")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.user = os.getenv("DB_USERNAME", "tozalash_user")
        self.password = os.getenv("DB_PASSWORD", "tozalash_password")
        self.db_name = os.getenv("DB_DATABASE", "tozalash_db")
        self.pool = None
"""
code = code.replace(init_sqlite, init_mysql)

# Connection wrapper
get_conn_sqlite = """    @contextlib.asynccontextmanager
    async def get_conn(self):
        \"\"\"Ma'lumotlar bazasiga asinxron ulanish\"\"\"
        async with aiosqlite.connect(self.db_path, timeout=20.0) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn"""

get_conn_mysql = """    @contextlib.asynccontextmanager
    async def get_conn(self):
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                host=self.host, port=self.port,
                user=self.user, password=self.password, db=self.db_name,
                cursorclass=aiomysql.DictCursor, autocommit=True,
                charset='utf8mb4'
            )
        async with self.pool.acquire() as conn:
            yield conn"""
code = code.replace(get_conn_sqlite, get_conn_mysql)

# AUTOINCREMENT to AUTO_INCREMENT
code = code.replace("AUTOINCREMENT", "AUTO_INCREMENT")
# INSERT OR IGNORE to INSERT IGNORE
code = code.replace("INSERT OR IGNORE", "INSERT IGNORE")
# INSERT OR REPLACE to REPLACE
code = code.replace("INSERT OR REPLACE", "REPLACE")

# Replace date('now') with CURDATE()
code = code.replace("date('now')", "CURDATE()")
code = code.replace("datetime('now', ?)", "DATE_SUB(NOW(), INTERVAL %s DAY)")
# The query has: datetime('now', f'-{days} days') which doesn't work in MySQL nicely with %s if we pass string.
# We will just replace it manually below.

# In aiomysql, we can't do `await conn.execute(...)`. We must do `async with conn.cursor() as cursor: await cursor.execute(...)`
# Also `async with conn.execute(...) as cursor:` becomes `async with conn.cursor() as cursor: await cursor.execute(...)`
# Let's fix this by implementing a custom execute method on the Database class.
code = code.replace(
    "async with self.get_conn() as conn:",
    "async with self.get_conn() as conn:\n            async with conn.cursor() as cursor:",
)
code = code.replace("await conn.execute", "await cursor.execute")
code = code.replace("async with conn.execute", "await cursor.execute")

# Fix missing cursor context for "async with conn.execute" which was replaced to "await cursor.execute"
# Since we added `async with conn.cursor() as cursor:` at the beginning of the `with conn` block, we don't need `async with conn.execute` anymore.
# We just replace:
# async with conn.execute("SELECT ...") as cursor:
# to
# await cursor.execute("SELECT ...")

code = re.sub(
    r"async with conn\.execute\((.*?)\) as cursor:",
    r"await cursor.execute(\1)",
    code,
    flags=re.DOTALL,
)

# Fix await conn.commit() to await conn.commit() (which works, but aiomysql autocommit is True, so it's optional. But we can leave it).

# ? to %s
code = code.replace("?", "%s")
code = code.replace("date('now')", "CURDATE()")

# Manual fix for `datetime('now', %s)` -> `DATE_SUB(NOW(), INTERVAL %s DAY)`
# The original code had: WHERE created_at >= datetime('now', %s)
code = code.replace("datetime('now', %s)", "DATE_SUB(NOW(), INTERVAL %s DAY)")
# And it passed `(f'-{days} days',)` -> we just pass `(days,)`
code = code.replace("(f'-{days} days',)", "(days,)")

with open("database_new.py", "w", encoding="utf-8") as f:
    f.write(code)
