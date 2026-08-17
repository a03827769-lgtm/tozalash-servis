import asyncio
from database import Database

async def run_in_loop1(db_instance):
    async with db_instance.lock:
        print("Loop 1 acquired lock")

async def run_in_loop2(db_instance):
    async with db_instance.lock:
        print("Loop 2 acquired lock")

def main():
    db_inst = Database()
    asyncio.run(run_in_loop1(db_inst))
    try:
        asyncio.run(run_in_loop2(db_inst))
        print("SUCCESS: Lock worked across event loops!")
    except Exception as e:
        print(f"FAILED with exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
