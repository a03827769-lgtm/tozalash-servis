import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai
import time

async def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API key")
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Let's generate a test mp3 using gTTS (English just to test pipeline)
    try:
        from gtts import gTTS
        tts = gTTS("Hello, this is a test audio message for the AI system.", lang='en')
        tts.save("test_audio.mp3")
        
        print("Uploading to Gemini API...")
        start = time.time()
        
        # In genai, we upload the file first
        audio_file = genai.upload_file(path="test_audio.mp3")
        
        print("Generating content...")
        response = await model.generate_content_async([
            "Transcribe this audio exactly.",
            audio_file
        ])
        
        print(f"RESPONSE (took {time.time()-start:.2f}s):", response.text)
        
        # Cleanup
        genai.delete_file(audio_file.name)
    except Exception as e:
        print("ERROR:", e)

asyncio.run(main())
