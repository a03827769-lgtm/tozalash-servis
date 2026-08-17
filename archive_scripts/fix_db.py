import asyncio
from database import Database


async def fix_db():
    db = Database()
    # It might create pool automatically in get_conn if not created?
    # Let's just call init_db which sets up the pool and creates tables
    await db.init_db()
    async with db.get_conn() as conn:
        async with conn.cursor() as cursor:
            print("Checking schema...")
            await cursor.execute("SHOW CREATE TABLE orders")
            print((await cursor.fetchone())["Create Table"])

            try:
                await cursor.execute(
                    "ALTER TABLE orders ADD COLUMN client_telegram_id VARCHAR(255)"
                )
                print("Added client_telegram_id to orders")
            except Exception as e:
                print("Error adding client_telegram_id:", e)

            try:
                await cursor.execute(
                    "ALTER TABLE orders ADD COLUMN is_eco_friendly BOOLEAN DEFAULT FALSE"
                )
                print("Added is_eco_friendly to orders")
            except Exception as e:
                pass

            try:
                await cursor.execute(
                    "ALTER TABLE orders ADD COLUMN custom_checklist TEXT"
                )
                print("Added custom_checklist to orders")
            except Exception as e:
                pass


if __name__ == "__main__":
    asyncio.run(fix_db())
