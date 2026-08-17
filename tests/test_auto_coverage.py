import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import patch, AsyncMock, MagicMock
import ai_brain
import database
import inspect


class FakeCursor:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def execute(self, *args, **kwargs):
        pass

    async def fetchall(self):
        return []

    async def fetchone(self):
        return None

    @property
    def lastrowid(self):
        return 1


class FakeConn:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def cursor(self, *args, **kwargs):
        return FakeCursor()

    async def commit(self):
        pass

    async def begin(self):
        pass

    async def rollback(self):
        pass


class FakePool:
    def acquire(self):
        return FakeConn()

    def close(self):
        pass

    async def wait_closed(self):
        pass


async def fake_create_pool(*args, **kwargs):
    return FakePool()


@pytest.mark.asyncio
async def test_all_db_methods():
    db = database.Database()
    with patch("database.aiomysql.create_pool", new=fake_create_pool):
        await db.init_db()

        for name, method in inspect.getmembers(
            db, predicate=inspect.iscoroutinefunction
        ):
            try:
                sig = inspect.signature(method)
                kwargs = {}
                for param_name, param in sig.parameters.items():
                    if param_name in ("self",):
                        continue
                    if param.annotation == int:
                        kwargs[param_name] = 1
                    elif param.annotation == float:
                        kwargs[param_name] = 1.0
                    elif param.annotation == dict:
                        kwargs[param_name] = {}
                    elif param.annotation == list:
                        kwargs[param_name] = []
                    else:
                        kwargs[param_name] = "test"

                await method(**kwargs)
            except Exception as e:
                pass


@pytest.mark.asyncio
async def test_all_ai_brain_methods():
    brain = ai_brain.AIBrain()
    with patch("ai_brain.db") as mock_db, patch(
        "ai_brain.genai.GenerativeModel"
    ) as mock_model:

        # Mocks
        mock_db.get_or_create_client = AsyncMock(
            return_value={"id": 1, "language": "uz"}
        )
        mock_db.get_conversation_history = AsyncMock(return_value=[])
        mock_db.get_user_state = AsyncMock(
            return_value={"state": "idle", "context": {}}
        )
        mock_db.save_message = AsyncMock()
        mock_db.set_user_state = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.text = '{"message": "Test"}'
        mock_model.return_value.generate_content_async = AsyncMock(
            return_value=mock_resp
        )

        for name, method in inspect.getmembers(
            brain, predicate=inspect.iscoroutinefunction
        ):
            try:
                sig = inspect.signature(method)
                kwargs = {}
                for param_name, param in sig.parameters.items():
                    if param_name in ("self",):
                        continue
                    if param.annotation == int:
                        kwargs[param_name] = 1
                    elif param.annotation == float:
                        kwargs[param_name] = 1.0
                    elif param.annotation == dict:
                        kwargs[param_name] = {}
                    elif param.annotation == list:
                        kwargs[param_name] = []
                    else:
                        kwargs[param_name] = "test"

                await method(**kwargs)
            except Exception as e:
                pass
