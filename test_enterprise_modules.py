"""
Tozalash Servis — Enterprise Modules Verification Test Suite (UTF-8 Safe)
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from uzbek_phonetics import number_to_uzbek_words, normalize_uzbek_speech_text
from app.core.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenException
from app.ai.sentiment import sentiment_analyzer
from app.ai.upselling import upselling_engine
from smart_dispatch import smart_dispatcher


async def run_tests():
    print("========================================")
    print("[TEST] ENTERPRISE TEST SUITE BOSHLANDI")
    print("========================================")

    # 1. Phonetics Tests
    assert number_to_uzbek_words(150000) == "bir yuz ellik ming", f"Xato: {number_to_uzbek_words(150000)}"
    norm = normalize_uzbek_speech_text("Buyurtma narxi 250 000 so'm, maydoni 80 kv.m")
    print(f"[PASS] Phonetics test: {norm}")

    # 2. Circuit Breaker Tests
    cb = CircuitBreaker("TestBreaker", failure_threshold=2, recovery_timeout=0.5)
    async def bad_func():
        raise ValueError("Simulated network error")

    try:
        await cb.call(bad_func)
    except ValueError:
        pass

    try:
        await cb.call(bad_func)
    except ValueError:
        pass

    assert cb.state == CircuitState.OPEN, f"Breaker holati kutilganidek OPEN emas: {cb.state}"
    print("[PASS] Circuit Breaker OPEN state test")

    # 3. Sentiment Tests
    neg = sentiment_analyzer.analyze_message("Sizlar juda yomon tozaladingiz, pulimni qaytaring, shikoyat qilaman!")
    assert neg["label"] == "CRITICAL_DISPUTE", f"Sentiment label: {neg}"
    assert neg["needs_escalation"] is True

    pos = sentiment_analyzer.analyze_message("Katta rahmat, juda zor toza boldi, baraka toping!")
    assert pos["label"] == "POSITIVE"
    print("[PASS] Sentiment & Escalation test")

    # 4. Upselling Tests
    pitch = upselling_engine.get_upsell_pitch("regular_cleaning")
    assert "20%" in pitch or "chegirma" in pitch
    print(f"[PASS] Upselling pitch test: {pitch[:50]}...")

    # 5. Smart Dispatch Tests
    score = await smart_dispatcher.calculate_worker_score(
        {"rating": 4.9, "completed_orders": 30, "skills": "regular_cleaning, universal", "current_lat": 41.31, "current_lon": 69.24},
        {"lat": 41.31, "lon": 69.24, "service_type": "regular_cleaning"}
    )
    assert score > 80.0, f"Ball: {score}"
    surge = smart_dispatcher.calculate_surge_multiplier(10, 2)
    assert surge >= 1.0, f"Surge: {surge}"
    print(f"[PASS] Smart Dispatch & Surge Pricing test: Score={score}, Surge={surge}")

    print("========================================")
    print("[SUCCESS] BARCHA 5 TA TEST 100% MUVAFFAQISHLI O'TDI!")
    print("========================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
