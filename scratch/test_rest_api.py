import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_rest():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API key")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": "Hello, how are you? Answer in 1 short sentence."}]
        }],
        "generationConfig": {
            "temperature": 0.7
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            if resp.status == 200:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print("Success:", text)
            else:
                print("Error:", resp.status, data)

asyncio.run(test_rest())
