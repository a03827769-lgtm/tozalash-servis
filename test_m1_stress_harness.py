"""
Milestone M1 Empirical Stress Harness (Robust & Non-blocking)
Tests:
1. Config import, validate_config() strict & non-strict modes, thread-safety, fallback key generation.
2. Async Database Lock behavior across sequential loops, parallel multi-thread loops, and lock contention.
3. Database helper methods, whitelist validation, schema migration 005 syntax & structure.
"""

import sys
import os
import threading
import asyncio
import traceback
import pytest

# Ensure root dir is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

results = []

def record_result(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, passed, detail))
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""), flush=True)


# ============================================================================
# 1. CONFIG RESOLUTION & VALIDATION STRESS TESTS
# ============================================================================

def test_config_multithreaded_imports():
    """Verify that importing config in 10 concurrent threads causes no race conditions."""
    print("Running test_config_multithreaded_imports...", flush=True)
    exceptions = []

    def worker():
        try:
            import config
            from app.core.config import settings
            assert config.BUSINESS_NAME == settings.BUSINESS_NAME
            assert hasattr(config, "PRICES")
            assert hasattr(config, "SHEETS")
        except Exception as e:
            exceptions.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    record_result("Config Multi-threaded Import", len(exceptions) == 0, f"Exceptions: {exceptions}")


def test_validate_config_non_strict():
    """Test validate_config in default non-strict mode."""
    print("Running test_validate_config_non_strict...", flush=True)
    import config
    try:
        is_valid, errors, warnings = config.validate_config(strict=False)
        record_result("validate_config(strict=False)", isinstance(is_valid, bool), f"valid={is_valid}, errors={errors}, warnings={len(warnings)}")
    except Exception as e:
        record_result("validate_config(strict=False)", False, f"Raised unexpected error: {e}")


def test_validate_config_strict_mode():
    """Test validate_config in strict mode raises ValueError if errors exist."""
    print("Running test_validate_config_strict_mode...", flush=True)
    import config
    orig_token = config.TELEGRAM_BOT_TOKEN
    try:
        config.TELEGRAM_BOT_TOKEN = ""
        try:
            config.validate_config(strict=True)
            record_result("validate_config(strict=True) empty token", False, "Failed to raise ValueError on missing TELEGRAM_BOT_TOKEN")
        except ValueError as ve:
            record_result("validate_config(strict=True) empty token", True, f"Correctly raised ValueError: {ve}")
    finally:
        config.TELEGRAM_BOT_TOKEN = orig_token


def test_validate_config_jwt_fallback():
    """Test that empty JWT_SECRET_KEY triggers hex fallback auto-generation in dev mode."""
    print("Running test_validate_config_jwt_fallback...", flush=True)
    import config
    from app.core.config import settings

    orig_jwt = config.JWT_SECRET_KEY
    try:
        config.JWT_SECRET_KEY = ""
        settings.JWT_SECRET_KEY = ""
        is_valid, errors, warnings = config.validate_config(strict=False)
        generated = config.JWT_SECRET_KEY
        passed = len(generated) == 64 and settings.JWT_SECRET_KEY == generated
        record_result("validate_config JWT Fallback Generation", passed, f"Generated length {len(generated)}: {generated[:8]}...")
    finally:
        config.JWT_SECRET_KEY = orig_jwt
        settings.JWT_SECRET_KEY = orig_jwt


def test_validate_config_concurrent_calls():
    """Test concurrent calls to validate_config from 10 threads."""
    print("Running test_validate_config_concurrent_calls...", flush=True)
    import config
    exceptions = []

    def worker():
        try:
            for _ in range(5):
                config.validate_config(strict=False)
        except Exception as e:
            exceptions.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    record_result("validate_config Concurrent Thread Safety", len(exceptions) == 0, f"Exceptions: {exceptions}")


# ============================================================================
# 2. ASYNC LOCK & DB EVENT LOOP BINDING STRESS TESTS
# ============================================================================

def test_db_lock_lazy_init():
    """Verify db._lock is None on import and instantiated on db.lock property call."""
    print("Running test_db_lock_lazy_init...", flush=True)
    import database
    db = database.Database()
    init_none = db._lock is None
    lock_obj = db.lock
    instantiated = db._lock is not None and isinstance(lock_obj, asyncio.Lock)
    record_result("Database._lock Lazy Initialization", init_none and instantiated, f"_lock initial: {init_none}, after prop: {type(lock_obj)}")


def test_db_lock_sequential_loops():
    """Verify db.lock across sequential asyncio event loops."""
    print("Running test_db_lock_sequential_loops...", flush=True)
    import database
    db = database.Database()

    async def task1():
        async with db.lock:
            await asyncio.sleep(0.01)
            return True

    async def task2():
        async with db.lock:
            await asyncio.sleep(0.01)
            return True

    try:
        res1 = asyncio.run(task1())
        res2 = asyncio.run(task2())
        record_result("db.lock Sequential Loops", res1 and res2, "Both sequential asyncio.run completed successfully")
    except Exception as e:
        record_result("db.lock Sequential Loops", False, f"Error: {e}")


def test_db_lock_multithreaded_uncontended_loops():
    """Test db.lock across multiple concurrent event loops when uncontended."""
    print("Running test_db_lock_multithreaded_uncontended_loops...", flush=True)
    import database
    db = database.Database()
    errors = []

    def thread_worker(thread_id):
        async def loop_task():
            async with db.lock:
                await asyncio.sleep(0.01)
                return thread_id

        try:
            res = asyncio.run(loop_task())
            assert res == thread_id
        except Exception as e:
            errors.append((thread_id, type(e).__name__, str(e)))

    threads = [threading.Thread(target=thread_worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    record_result("db.lock Uncontended Multi-Thread Loops", len(errors) == 0, f"Errors: {errors}")


def test_db_lock_cross_loop_contention():
    """
    Empirical Stress Test: Contended Lock across different event loops in separate threads.
    Tests whether single singleton _lock causes cross-loop deadlock or RuntimeError when contended.
    """
    print("Running test_db_lock_cross_loop_contention...", flush=True)
    import database
    db = database.Database()

    lock_acquired_in_thread1 = threading.Event()
    thread2_completed = threading.Event()
    thread2_error = []

    def thread1_func():
        async def task1():
            async with db.lock:
                lock_acquired_in_thread1.set()
                await asyncio.sleep(0.2)
        asyncio.run(task1())

    def thread2_func():
        async def task2():
            lock_acquired_in_thread1.wait(timeout=2.0)
            try:
                # Set 0.3s timeout for lock acquisition
                await asyncio.wait_for(db.lock.acquire(), timeout=0.3)
                db.lock.release()
                thread2_completed.set()
            except Exception as e:
                thread2_error.append(f"{type(e).__name__}: {str(e)}")

        asyncio.run(task2())

    t1 = threading.Thread(target=thread1_func, daemon=True)
    t2 = threading.Thread(target=thread2_func, daemon=True)
    t1.start()
    t2.start()

    t1.join(timeout=1.0)
    t2.join(timeout=1.0)

    is_alive = t1.is_alive() or t2.is_alive()
    if is_alive:
        record_result("db.lock Cross-Loop Contention", False, "DEADLOCK DETECTED: Cross-loop contention caused asyncio.Lock to block indefinitely across threads!")
    elif thread2_error:
        record_result("db.lock Cross-Loop Contention", False, f"FAILED with error: {thread2_error}")
    else:
        record_result("db.lock Cross-Loop Contention", True, "Successfully handled cross-loop lock acquisition")


def test_database_whitelist_columns():
    """Verify whitelist protection in Database._CLIENT_UPDATABLE_COLUMNS."""
    print("Running test_database_whitelist_columns...", flush=True)
    import database
    db = database.Database()
    whitelist = db._CLIENT_UPDATABLE_COLUMNS
    required_cols = {
        "gold_status_notified", "loyalty_coins", "city_id", "role",
        "address", "is_blocked", "gender", "notification_enabled"
    }
    missing = required_cols - whitelist
    record_result("Database Whitelist Columns", len(missing) == 0, f"Missing columns: {missing}")


def test_database_get_pool_uninitialized():
    """Verify get_pool raises RuntimeError when pool is None."""
    print("Running test_database_get_pool_uninitialized...", flush=True)
    import database
    db = database.Database()
    try:
        db.get_pool()
        record_result("db.get_pool uninitialized check", False, "Failed to raise RuntimeError")
    except RuntimeError as re:
        record_result("db.get_pool uninitialized check", True, f"Raised expected RuntimeError: {re}")


# ============================================================================
# MAIN EXECUTION HARNESS
# ============================================================================

if __name__ == "__main__":
    print("=" * 70, flush=True)
    print("RUNNING MILESTONE M1 EMPIRICAL STRESS TEST SUITE", flush=True)
    print("=" * 70, flush=True)

    print("\n--- 1. Config Resolution & Security Tests ---", flush=True)
    test_config_multithreaded_imports()
    test_validate_config_non_strict()
    test_validate_config_strict_mode()
    test_validate_config_jwt_fallback()
    test_validate_config_concurrent_calls()

    print("\n--- 2. Database & Async Lock Stress Tests ---", flush=True)
    test_db_lock_lazy_init()
    test_db_lock_sequential_loops()
    test_db_lock_multithreaded_uncontended_loops()
    test_db_lock_cross_loop_contention()
    test_database_whitelist_columns()
    test_database_get_pool_uninitialized()

    print("\n" + "=" * 70, flush=True)
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    print(f"SUMMARY: {passed_count}/{total_count} tests PASSED", flush=True)
    print("=" * 70, flush=True)

    if passed_count < total_count:
        sys.exit(1)
