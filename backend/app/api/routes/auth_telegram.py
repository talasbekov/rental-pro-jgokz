import hashlib
import hmac
import json
from datetime import timedelta
from urllib.parse import parse_qs, unquote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.core.config import settings
from app.core.security import create_access_token
from shared.crud.users import get_or_create_by_telegram_id
from shared.models import Token

router = APIRouter(prefix="/auth", tags=["auth"])


class TelegramAuthRequest(BaseModel):
    init_data: str


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """Validate Telegram WebApp initData using HMAC-SHA256."""
    parsed = parse_qs(init_data)
    received_hash = parsed.get("hash", [None])[0]
    if not received_hash:
        return None

    # Build data-check-string: sorted key=value pairs (URL-decoded), excluding hash
    data_pairs = []
    for pair in init_data.split("&"):
        key, _, value = pair.partition("=")
        if key != "hash":
            data_pairs.append(f"{key}={unquote(value)}")
    data_pairs.sort()
    data_check_string = "\n".join(data_pairs)

    # HMAC: secret_key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # Extract user data
    user_raw = parsed.get("user", [None])[0]
    if not user_raw:
        return None

    return json.loads(user_raw)


@router.post("/telegram", response_model=Token)
async def telegram_auth(body: TelegramAuthRequest, session: SessionDep) -> Token:
    """Authenticate via Telegram WebApp initData (silent auth)."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Telegram bot not configured")

    user_data = validate_init_data(body.init_data, settings.TELEGRAM_BOT_TOKEN)
    if user_data is None:
        raise HTTPException(status_code=401, detail="Invalid Telegram auth data")

    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Invalid Telegram auth data")

    first_name = user_data.get("first_name", "")
    last_name = user_data.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()

    user = await get_or_create_by_telegram_id(
        session=session, telegram_id=telegram_id, full_name=full_name or None
    )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    return Token(access_token=access_token)
