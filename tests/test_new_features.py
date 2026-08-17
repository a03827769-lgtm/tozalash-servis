import pytest
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.mark.asyncio
async def test_ai_brain_analyze_image():
    from ai_brain import AIBrain
    brain = AIBrain()
    
    with patch.object(brain.vision_model, 'generate_content_async') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = '{"estimated_area": 50, "stain_severity": "high", "room_type": "living_room"}'
        mock_generate.return_value = mock_response
        
        result = await brain.analyze_image("test.jpg")
        
        assert "estimated_area" in result
        assert result["estimated_area"] == 50
        assert result["stain_severity"] == "high"

@pytest.mark.asyncio
async def test_b2b_setup_subscription():
    from enterprise_b2b import b2b_manager
    
    await b2b_manager.setup_subscription("TestCorp", "Oylik")
    assert b2b_manager.corporate_subscriptions["TestCorp"] == "Oylik"

@pytest.mark.asyncio
async def test_b2b_generate_invoice():
    from enterprise_b2b import b2b_manager
    
    with patch('invoice_generator.generate_invoice') as mock_pdf:
        output_path = await b2b_manager.generate_invoice("TestCorp", ["General Cleaning"], 500000.0)
        assert output_path.endswith(".pdf")
        assert "INV-" in output_path
        mock_pdf.assert_called_once()

@pytest.mark.asyncio
async def test_database_referral_logic():
    from database import db
    import pytest_asyncio
    
    # We mock the database connection to avoid hitting a real DB in this unit test
    with patch.object(db, 'get_conn') as mock_get_conn:
        mock_conn = MagicMock()
        mock_get_conn.return_value.__aenter__.return_value = mock_conn
        
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        
        # Test finding existing client
        mock_cursor.fetchone.return_value = {"id": 1, "telegram_id": "123456", "name": "Test Client"}
        
        client = await db.get_or_create_client("123456", name="Test Client")
        assert client["name"] == "Test Client"
        
        # Test creating new client with referral
        mock_cursor.fetchone.side_effect = [
            None, # First call: client not found
            {"id": 2}, # Second call: referrer found
            {"id": 3, "telegram_id": "999999", "name": "New Client", "loyalty_points": 0} # Third call: fetch newly created client
        ]
        
        client = await db.get_or_create_client("999999", name="New Client", referrer_code="REFER_ME")
        assert client["name"] == "New Client"
