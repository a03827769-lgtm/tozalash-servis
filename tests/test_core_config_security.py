import pytest
from app.core.config import Settings, settings
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
)
from datetime import timedelta
import asyncio
from fastapi import HTTPException


def test_config_database_url_property():
    s = Settings()
    s.SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    assert s.get_database_url == "sqlite:///test.db"


def test_create_access_token_with_delta():
    token = create_access_token("test_user", timedelta(minutes=5))
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_get_current_user_invalid():
    with pytest.raises(HTTPException):
        await get_current_user("invalid.token.here")


from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
)
import pytest
from fastapi import HTTPException
from datetime import timedelta


def test_security_full():
    token = create_access_token("testuser")
    assert isinstance(token, str)

    token_td = create_access_token("testuser", timedelta(minutes=5))
    assert isinstance(token_td, str)

    pw_hash = get_password_hash("password")
    assert verify_password("password", pw_hash)


@pytest.mark.asyncio
async def test_get_current_user():
    token = create_access_token("testuser")
    user = await get_current_user(token)
    assert user == "testuser"

    with pytest.raises(HTTPException):
        await get_current_user("invalid_token")
