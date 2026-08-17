import speech_recognition as sr
from pydub import AudioSegment
import os
import time

def test_sr_uz():
    try:
        print("1. Generating edge-tts audio...")
        import edge_tts
        import asyncio
        async def make_audio():
            comm = edge_tts.Communicate("Assalomu alaykum, tozalash xizmati qancha turadi?", voice="uz-UZ-MadinaNeural")
            await comm.save("test_sr_uz.mp3")
        asyncio.run(make_audio())
        
        print("2. Converting to WAV...")
        audio = AudioSegment.from_file("test_sr_uz.mp3")
        audio.export("test_sr_uz.wav", format="wav")
        
        print("3. Recognizing with Google Web Speech API...")
        start = time.time()
        recognizer = sr.Recognizer()
        with sr.AudioFile("test_sr_uz.wav") as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uz-UZ")
            print(f"Recognized in {time.time()-start:.2f}s!")
            # encode safely for windows console
            print("Text:", text.encode('utf-8', 'replace').decode('utf-8'))
    except Exception as e:
        print("ERROR:", e)

test_sr_uz()
