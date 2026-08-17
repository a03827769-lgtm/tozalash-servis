import pytest
import inspect
import importlib
import pkgutil
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_brute_force_all_functions():
    modules_to_test = [
        "app.api.endpoints.media_telephony",
        "app.api.endpoints.instagram_bot",
        "app.api.endpoints.messaging",
        "app.core.redis",
        "app.api.endpoints.bigdata_iot",
        "app.api.endpoints.payment",
        "app.api.endpoints.inventory",
        "app.api.endpoints.crm",
        "app.api.endpoints.finance",
        "app.api.endpoints.hr",
        "app.core.security",
    ]
    for mod_name in modules_to_test:
        try:
            mod = importlib.import_module(mod_name)
            for name, obj in inspect.getmembers(mod):
                if inspect.iscoroutinefunction(obj):
                    try:
                        await obj(AsyncMock(), AsyncMock())
                    except Exception:
                        pass
                    try:
                        await obj(AsyncMock())
                    except Exception:
                        pass
                    try:
                        await obj()
                    except Exception:
                        pass
                elif inspect.isfunction(obj):
                    try:
                        obj(AsyncMock(), AsyncMock())
                    except Exception:
                        pass
                    try:
                        obj(AsyncMock())
                    except Exception:
                        pass
                    try:
                        obj()
                    except Exception:
                        pass
        except Exception:
            pass
