# Handoff Report — DB Pool & Schema Fixes (M1 Explorer 2)

## 1. Observation

Direct observations from codebase inspection:

1. **Import-Time `asyncio.Lock()` Instantiation in `database.py`**:
   - File: `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\database.py`
   - Line 29: `self._lock = asyncio.Lock()` inside `Database.__init__()`.
   - Line 858: `db = Database()` instantiated at global module level.
   - Verbatim code at line 28-30:
     ```python
     self.pool = None
     self._lock = asyncio.Lock()
     ```
   - Line 34: `async with self._lock:` inside `async def get_conn(self):`.

2. **Column Mismatch in `competitor_prices` Query**:
   - File: `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\database.py`
   - Line 582:
     ```python
     "SELECT * FROM competitor_prices WHERE service_name = %s ORDER BY created_at DESC"
     ```
   - File: `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\migrations\009_gamification_and_ratings.sql`
   - Lines 25-32:
     ```sql
     CREATE TABLE IF NOT EXISTS competitor_prices (
         id INTEGER PRIMARY KEY AUTO_INCREMENT,
         competitor_name VARCHAR(100) NOT NULL,
         service_name VARCHAR(100) NOT NULL,
         price DECIMAL(10, 2) NOT NULL,
         detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         source_url VARCHAR(255)
     );
     ```
   - Observed error when executing query: MySQL Error 1054 (`Unknown column 'created_at' in 'order clause'`).

3. **Unsafe `db.pool` Access in `ws_server.py` `/health` Endpoint**:
   - File: `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\ws_server.py`
   - Line 260-266:
     ```python
     from database import db
     db_status = "ok"
     try:
         # Oddiy tekshiruv so'rovi
         async with db.pool.acquire() as conn:
             async with conn.cursor() as cursor:
                 await cursor.execute("SELECT 1")
     ```
   - Observed behavior: If `db.pool` is `None` (uninitialized pool at server startup), `db.pool.acquire()` raises `AttributeError: 'NoneType' object has no attribute 'acquire'`.


## 2. Logic Chain

1. **Import-Time Lock Initialization**:
   - In Python 3.10+, instantiating `asyncio.Lock()` at module import time (`db = Database()`) when no event loop is running causes lock binding to a non-existent or stale loop.
   - When coroutines run under Pyrogram / PTB / FastAPI event loops later, acquiring `self._lock` throws `RuntimeError: Got a different loop` or `RuntimeError: There is no running event loop`.
   - By setting `self._lock = None` in `__init__` and creating the `asyncio.Lock()` lazily on first access inside an active loop via `@property def lock(self) -> asyncio.Lock:`, we guarantee the lock is bound to the currently running event loop safely without race conditions.

2. **Database Column Mismatch (`competitor_prices`)**:
   - Migration `009_gamification_and_ratings.sql` established the table schema with `detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`.
   - The query in `database.py:582` attempts to sort by `created_at DESC`, which does not exist in the table definition.
   - Changing `created_at` to `detected_at` in the `SELECT` query aligns the Python ORM method with the actual database schema defined in migration 009.

3. **Unsafe Pool Acquisition in `/health` Endpoint**:
   - Direct access to `db.pool.acquire()` assumes `db.pool` is an active `aiomysql.Pool` object.
   - When the `/health` endpoint is requested prior to any database operation, `db.pool` remains `None`.
   - Replacing `async with db.pool.acquire()` with `async with db.get_conn()` delegates pool lifecycle management to `Database.get_conn()`, which lazily initializes `db.pool` under `self.lock` if it is `None`, or properly fails with connection errors rather than `AttributeError`.


## 3. Caveats

- **Existing DB Connections**: If MySQL is unreachable, `db.get_conn()` in `/health` will catch and return `db_status = f"error: {e}"`. This is expected behavior for health check reporting.
- **Backwards Compatibility**: No public interfaces of `Database` or `/health` are altered; changes are strictly internal safety and schema alignment fixes.


## 4. Conclusion & Recommended Edits for Worker

### Recommendation 1: Lazy Lock Initialization in `database.py`

**Target File**: `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\database.py`

Replace lines 28-35 in `database.py`:
```python
<<<<
        self.pool = None
        self._lock = asyncio.Lock()

    @contextlib.asynccontextmanager
    async def get_conn(self):
        if self.pool is None:
            async with self._lock:
====
        self.pool = None
        self._lock: Optional[asyncio.Lock] = None

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def get_pool(self) -> aiomysql.Pool:
        if self.pool is None:
            raise RuntimeError("Database connection pool is not initialized.")
        return self.pool

    @contextlib.asynccontextmanager
    async def get_conn(self):
        if self.pool is None:
            async with self.lock:
>>>>
```

---

### Recommendation 2: Schema Fix for `competitor_prices` Query in `database.py`

**Target File**: `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\database.py`

Replace line 582 in `database.py`:
```python
<<<<
                    await cursor.execute(
                        "SELECT * FROM competitor_prices WHERE service_name = %s ORDER BY created_at DESC",
                        (service_name,)
                    )
====
                    await cursor.execute(
                        "SELECT * FROM competitor_prices WHERE service_name = %s ORDER BY detected_at DESC",
                        (service_name,)
                    )
>>>>
```

---

### Recommendation 3: Safe Pool Access in `ws_server.py` `/health` Endpoint

**Target File**: `C:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\ws_server.py`

Replace lines 262-267 in `ws_server.py`:
```python
<<<<
        try:
            # Oddiy tekshiruv so'rovi
            async with db.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
====
        try:
            # Oddiy tekshiruv so'rovi (safely initialize pool if None)
            async with db.get_conn() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
>>>>
```


## 5. Verification Method

1. **Python Syntax & Import Verification**:
   Execute the following command to verify syntax correctness of modified files:
   ```pwsh
   python -m py_compile database.py ws_server.py
   ```

2. **Async Lock Event Loop Test**:
   Run python one-liner to verify `Database` instantiation outside loop and lazy lock acquisition inside loop:
   ```pwsh
   python -c "import asyncio, database; db = database.db; print('Init lock:', db._lock); asyncio.run(db.get_conn().__aenter__())"
   ```
   *Expected result*: `Init lock: None`, followed by connection attempt without `RuntimeError: Got a different loop`.

3. **SQL Query Column Verification**:
   Verify column names in `migrations/009_gamification_and_ratings.sql` vs `database.py`:
   ```pwsh
   Select-String -Path "migrations\009_gamification_and_ratings.sql" -Pattern "detected_at"
   Select-String -Path "database.py" -Pattern "detected_at"
   ```

4. **Health Endpoint Verification**:
   Inspect `ws_server.py` line 264 to confirm `db.get_conn()` is used instead of direct `db.pool.acquire()`.
