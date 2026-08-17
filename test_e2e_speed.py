import asyncio
import time
import os
import logging
from ai_brain import AIBrain
import gemini_rotator

logging.basicConfig(level=logging.INFO)

async def run_test():
    brain = AIBrain()
    
    # Pre-warm AI Brain and Rotator
    print("Pre-warming Rotator...")
    # gemini_rotator module loads accounts automatically on import
    
    input_audio = "test_silero_opt.wav"
    output_audio = "test_response.wav"
    
    if not os.path.exists(input_audio):
        print(f"File {input_audio} topilmadi. Test to'xtatildi.")
        return
        
    print("\n--- Pipeline boshlandi ---")
    start_total = time.time()
    
    # 1. STT (Native Gemini Audio)
    stt_start = time.time()
    transcribed_text = await brain.analyze_audio(input_audio)
    stt_time = time.time() - stt_start
    print(f"[STT] Matn: {transcribed_text}")
    print(f"[STT] Vaqt: {stt_time:.2f}s")
    
    # 2. LLM Respond
    llm_start = time.time()
    response = await brain.respond(telegram_id="123456", user_message=transcribed_text, user_name="Test User")
    llm_time = time.time() - llm_start
    print(f"[LLM] Javob: {response.get('message')}")
    print(f"[LLM] Vaqt: {llm_time:.2f}s")
    
    # 3. TTS (Silero Optimized)
    tts_start = time.time()
    from uzbek_tts import generate_uzbek_voice
    await generate_uzbek_voice(response.get('message', 'Test'), output_audio)
    tts_time = time.time() - tts_start
    print(f"[TTS] Vaqt: {tts_time:.2f}s")
    
    total_time = time.time() - start_total
    print(f"\n--- UMUMIY VAQT: {total_time:.2f}s ---")

if __name__ == "__main__":
    asyncio.run(run_test())
