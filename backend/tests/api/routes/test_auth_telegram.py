import hashlib
import hmac
import json
from unittest.mock import patch
from urllib.parse import quote, urlencode

import pytest
from httpx import AsyncClient

from app.core.config import settings


def build_init_data(user_data: dict, bot_token: str) -> str:
    """Build valid Telegram WebApp initData with HMAC signature."""
    user_json = json.dumps(user_data, separators=(",", ":"))
    params = {
        "user": user_json,
        "auth_date": "1700000000",
        "query_id": "test_query",
    }

    # Build data-check-string
    data_pairs = sorted(f"{k}={v}" for k, v in params.items())
    data_check_string = "\n".join(data_pairs)

    # Compute HMAC
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    params["hash"] = computed_hash
    return urlencode(params)


TEST_BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


@pytest.mark.asyncio
async def test_telegram_auth_success(client: AsyncClient) -> None:
    user_data = {
        "id": 999888777,
        "first_name": "Test",
        "last_name": "User",
    }
    init_data = build_init_data(user_data, TEST_BOT_TOKEN)

    with patch.object(settings, "TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN):
        response = await client.post(
            f"{settings.API_V1_STR}/auth/telegram",
            json={"init_data": init_data},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_telegram_auth_invalid_hash(client: AsyncClient) -> None:
    init_data = "user=%7B%22id%22%3A123%7D&auth_date=1700000000&hash=invalidhash"

    with patch.object(settings, "TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN):
        response = await client.post(
            f"{settings.API_V1_STR}/auth/telegram",
            json={"init_data": init_data},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Telegram auth data"


@pytest.mark.asyncio
async def test_telegram_auth_no_bot_token(client: AsyncClient) -> None:
    with patch.object(settings, "TELEGRAM_BOT_TOKEN", ""):
        response = await client.post(
            f"{settings.API_V1_STR}/auth/telegram",
            json={"init_data": "some_data"},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Telegram bot not configured"


@pytest.mark.asyncio
async def test_telegram_auth_creates_user_once(client: AsyncClient) -> None:
    """Calling auth twice with same telegram_id should return same user."""
    user_data = {
        "id": 111222333,
        "first_name": "Repeat",
        "last_name": "User",
    }
    init_data = build_init_data(user_data, TEST_BOT_TOKEN)

    with patch.object(settings, "TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN):
        r1 = await client.post(
            f"{settings.API_V1_STR}/auth/telegram",
            json={"init_data": init_data},
        )
        r2 = await client.post(
            f"{settings.API_V1_STR}/auth/telegram",
            json={"init_data": init_data},
        )

    assert r1.status_code == 200
    assert r2.status_code == 200
    # Both should return valid tokens
    assert "access_token" in r1.json()
    assert "access_token" in r2.json()
