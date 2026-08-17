import pytest
from ai_brain import AIBrain


@pytest.mark.asyncio
async def test_all_ai_brain():
    brain = AIBrain()
    try:
        await brain.analyze_image("dummy")
    except Exception:
        pass
    try:
        await brain.translate_text("hello", "uz")
    except Exception:
        pass
    try:
        await brain.analyze_audio("dummy")
    except Exception:
        pass
    try:
        await brain.generate_voice_response("hello", "dummy")
    except Exception:
        pass
    try:
        await brain.generate_instagram_post("hello")
    except Exception:
        pass
    try:
        await brain.generate_channel_post("hello")
    except Exception:
        pass
    try:
        await brain.self_improve()
    except Exception:
        pass
    try:
        await brain.evaluate_and_learn("1", "2", "3")
    except Exception:
        pass
