import asyncio
from database import Database


async def reset_db():
    db = Database()
    async with db.get_conn() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            rows = await cursor.fetchall()

            await cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for row in rows:
                table = list(row.values())[0]
                try:
                    await cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                    print(f"Dropped {table}")
                except Exception as e:
                    print(f"Could not drop {table}: {e}")
            await cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Re-initialize
    await db.init_db()
    print("Database re-initialized with latest schema.")


if __name__ == "__main__":
    asyncio.run(reset_db())
