import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import patch, AsyncMock, MagicMock
import analytics.competitor_analyzer
from analytics.competitor_analyzer import CompetitorAnalyzer


@pytest.mark.asyncio
async def test_competitor_analyzer():
    analyzer = CompetitorAnalyzer()

    with patch("analytics.competitor_analyzer.ai_brain") as mock_brain, patch(
        "analytics.competitor_analyzer.httpx.AsyncClient"
    ) as mock_httpx, patch("analytics.competitor_analyzer.db") as mock_db:

        mock_db.get_conn = MagicMock()
        mock_conn = AsyncMock()
        mock_db.get_conn.return_value.__aenter__.return_value = mock_conn

        mock_brain.generate_response = AsyncMock(return_value='{"test": 123}')
        mock_brain.analyze_competitor = AsyncMock(return_value={"test": 1})

        # Test analyze_all_competitors
        await analyzer.analyze_all_competitors()

        # Test _analyze_single_competitor
        comp = {"url": "http://test.com", "name": "test", "platform": "web"}
        res = await analyzer._analyze_single_competitor(comp)
        assert res is not None

        # Test generate_competitive_report
        mock_genai = MagicMock()
        mock_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "report"
        mock_model.generate_content_async = AsyncMock(return_value=mock_resp)
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            res = await analyzer.generate_competitive_report()
            assert res is not None

        # Test search_new_competitors
        await analyzer.search_new_competitors()

        # Test send_weekly_report
        mock_client_instance = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client_instance
        await analyzer.send_weekly_report()
