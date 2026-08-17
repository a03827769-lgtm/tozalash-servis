import sqlite3
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()


def migrate_data():
    sqlite_db_path = os.getenv("DATABASE_PATH", "data/tozalash.db")
    if not os.path.exists(sqlite_db_path):
        print(f"SQLite database not found at {sqlite_db_path}. Skipping migration.")
        return

    print("Connecting to SQLite...")
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()

    print("Connecting to MySQL...")
    try:
        mysql_conn = pymysql.connect(
            host=os.getenv(
                "DB_HOST", "localhost"
            ),  # Use localhost if running locally, or mysql if in docker
            user=os.getenv("DB_USERNAME", "tozalash_user"),
            password=os.getenv("DB_PASSWORD", "tozalash_password"),
            database=os.getenv("DB_DATABASE", "tozalash_db"),
            port=int(os.getenv("DB_PORT", 3306)),
            cursorclass=pymysql.cursors.DictCursor,
        )
        mysql_cursor = mysql_conn.cursor()
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        return

    # Tables to migrate
    tables = [
        "users",
        "orders",
        "cleaning_sessions",
        "feedback",
        "user_preferences",
        "analytics_cache",
        "bot_settings",
    ]

    for table in tables:
        print(f"Migrating table {table}...")
        try:
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            if not rows:
                print(f"  No data found in {table}.")
                continue

            # Get column names
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns_info = sqlite_cursor.fetchall()
            columns = [col[1] for col in columns_info]

            placeholders = ", ".join(["%s"] * len(columns))
            columns_str = ", ".join(columns)

            insert_query = (
                f"INSERT IGNORE INTO {table} ({columns_str}) VALUES ({placeholders})"
            )

            mysql_cursor.executemany(insert_query, rows)
            mysql_conn.commit()
            print(f"  Successfully migrated {len(rows)} rows to {table}.")
        except Exception as e:
            print(f"  Error migrating table {table}: {e}")

    mysql_conn.close()
    sqlite_conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate_data()
