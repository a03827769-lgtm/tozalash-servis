import asyncio
import os
from gemini_rotator import rotator

async def test_rotator():
    print("Rotator accounts:", rotator.total)
    if rotator.total > 0:
        print("Testing ask()...")
        resp = await rotator.ask("Salom, kimsiz?")
        print("Response:", resp)
    else:
        print("No accounts loaded.")

if __name__ == "__main__":
    asyncio.run(test_rotator())
