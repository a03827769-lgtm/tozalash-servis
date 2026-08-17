import asyncio
from ai_brain import AIBrain


async def main():
    try:
        brain = AIBrain()
        print("Starting analysis...")
        res = await brain.analyze_image("test_img.jpg", "qancha boladi?")
        print("Result:", res)
    except Exception as e:
        print("Fatal error:", repr(e))


if __name__ == "__main__":
    asyncio.run(main())
