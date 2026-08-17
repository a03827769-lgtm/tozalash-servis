import asyncio
import time
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_pipeline():
    try:
        from ai_brain import ai_brain
        from uzbek_tts import tts_edge_ssml
        from pydub import AudioSegment
        
        print("=== Step 1: Generate dummy audio with edge-tts ===")
        tts_start = time.time()
        dummy_mp3 = "test_dummy.mp3"
        await tts_edge_ssml("Salom, qandaysan, tozalash xizmati narxi qancha", dummy_mp3)
        print(f"Generated (took {time.time()-tts_start:.2f}s)")
        
        # Convert to OGG (simulating Telegram)
        audio = AudioSegment.from_file(dummy_mp3)
        audio.export("test_telegram.ogg", format="ogg")
        
        print("\n=== Step 2: Test analyze_audio() ===")
        stt_start = time.time()
        text = await ai_brain.analyze_audio("test_telegram.ogg")
        print(f"Recognized (took {time.time()-stt_start:.2f}s): {text}")
        
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test_pipeline())
