import asyncio
from ai_brain import ai_brain


async def test_ai():
    print("Testing AI Brain...")
    result = await ai_brain.respond(
        "12345", "Salom, menga uy tozalash kerak.", "TestUser"
    )
    print("Result:", result)
    if result.get("action") == "error":
        print("FAILED: AI returned an error.")
        exit(1)
    else:
        print("SUCCESS: AI responded correctly.")


if __name__ == "__main__":
    asyncio.run(test_ai())
