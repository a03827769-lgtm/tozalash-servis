"""
Test Retention Engine & Uzbek TTS Normalization
"""

import os
import pytest
from retention_engine import retention_engine
from uzbek_tts import number_to_uzbek_words, normalize_uzbek_text_for_tts
from database import Database


def test_number_to_uzbek_words():
    assert number_to_uzbek_words(0) == "nol"
    assert number_to_uzbek_words(5) == "besh"
    assert number_to_uzbek_words(18) == "o'n sakkiz"
    assert number_to_uzbek_words(500000) == "besh yuz ming"
    assert number_to_uzbek_words(1500000) == "bir million besh yuz ming"


def test_normalize_uzbek_text_for_tts():
    raw_text = "Assalomu alaykum! Narxi 500000 so'm, 12 kv.m maydon."
    normalized = normalize_uzbek_text_for_tts(raw_text)
    assert "besh yuz ming" in normalized
    assert "kvadrat metr" in normalized


@pytest.mark.asyncio
async def test_retention_scan():
    test_db_file = "test_isolated_retention.db"
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

    test_db = Database()
    test_db.sqlite_path = test_db_file
    test_db.db_type = "sqlite"
    await test_db.init_db()

    notifications = await retention_engine.scan_and_generate_reactivations(db_inst=test_db)
    assert isinstance(notifications, list)

    await test_db.close()
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass
