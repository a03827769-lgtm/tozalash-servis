import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace aiomysql with aiosqlite
content = content.replace('import aiomysql', 'import aiosqlite')
content = content.replace('aiomysql.IntegrityError', 'aiosqlite.IntegrityError')
content = content.replace('aiomysql.Error', 'aiosqlite.Error')
content = content.replace('aiomysql.Pool', 'aiosqlite.Connection')

# 2. Replace %s with ?
# We can safely replace %s with ? in this codebase as %s is only used for SQL parameters.
content = content.replace('%s', '?')

# 3. Rewrite the Database class connection logic
db_class_pattern = re.compile(r'class Database:.*?async def init_db\(self\):', re.DOTALL)

new_db_class = '''class Database:
    """Asosiy ma'lumotlar bazasi klassi (Async SQLite)"""

    def __init__(self):
        self.db_path = os.getenv("DATABASE_PATH", "tozalash.db")
        self._conn = None
        self._lock: Optional[asyncio.Lock] = None

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @contextlib.asynccontextmanager
    async def get_conn(self):
        async with self.lock:
            if self._conn is None:
                self._conn = await aiosqlite.connect(self.db_path)
                self._conn.row_factory = aiosqlite.Row
        yield self._conn

    async def init_db(self):'''

content = db_class_pattern.sub(new_db_class, content)

# 4. Handle dict conversion since aiosqlite.Row is not a pure dict
content = content.replace('return user', 'return dict(user) if user else None')
content = content.replace('return result', 'return dict(result) if result else None')

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactoring complete.")
