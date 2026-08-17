import asyncio
from database import db


async def alter():
    await db.connect()
    async with db.get_conn() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "ALTER TABLE clients ADD COLUMN gold_status_notified BOOLEAN DEFAULT FALSE"
                )
                print("Column added.")
            except Exception as e:
                print("Error adding column:", e)


if __name__ == "__main__":
    asyncio.run(alter())
