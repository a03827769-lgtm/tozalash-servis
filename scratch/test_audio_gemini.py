import asyncio
from pyrogram import Client
from gemini_webapi import GeminiClient
from loguru import logger
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    psid = os.getenv("GEMINI_COOKIE_1_PSID")
    psidts = os.getenv("GEMINI_COOKIE_1_PSIDTS")
    if not psid:
        print("No PSID found. Cannot test.")
        return
        
    client = GeminiClient(secure_1psid=psid, secure_1psidts=psidts)
    await client.init(auto_close=False)
    
    # Let's create a test text and convert it to mp3 using gTTS just to have a valid audio file
    try:
        from gtts import gTTS
        tts = gTTS("Salom, qandaysan, tozalash xizmati narxi qancha", lang='uz')
        tts.save("test_audio.mp3")
        
        print("Testing gemini-webapi with audio file...")
        response = await client.generate_content(
            "Ushbu ovozli xabarni so'zma-so'z matnga o'girib ber",
            files=["test_audio.mp3"]
        )
        print("RESPONSE:", response.text)
    except Exception as e:
        print("ERROR:", e)

asyncio.run(main())
