import asyncio
import speech_recognition as sr
import os
from pydub import AudioSegment
import time

def test_stt():
    try:
        from gtts import gTTS
        # Generate audio in Russian to bypass gTTS 'uz' limit
        tts = gTTS("Привет, как дела?", lang='ru')
        tts.save("test_stt.mp3")
        
        start = time.time()
        # Convert to wav for speech_recognition
        audio = AudioSegment.from_file("test_stt.mp3")
        audio.export("test_stt.wav", format="wav")
        
        recognizer = sr.Recognizer()
        with sr.AudioFile("test_stt.wav") as source:
            audio_data = recognizer.record(source)
            # Tell speech_recognition it's Russian so it works
            text = recognizer.recognize_google(audio_data, language="ru-RU")
            print(f"Recognized (took {time.time()-start:.2f}s): {text}")
    except Exception as e:
        print("ERROR:", e)

test_stt()
