from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlmodel.ext.asyncio.session import AsyncSession

from shared.crud.users import get_or_create_by_telegram_id
from shared.db import async_engine


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        # Extract Telegram user from any update type
        tg_user = None
        if event.message and event.message.from_user:
            tg_user = event.message.from_user
        elif event.callback_query and event.callback_query.from_user:
            tg_user = event.callback_query.from_user
        elif event.inline_query and event.inline_query.from_user:
            tg_user = event.inline_query.from_user

        if tg_user is None:
            return await handler(event, data)

        async with AsyncSession(async_engine) as session:
            user = await get_or_create_by_telegram_id(
                session=session,
                telegram_id=tg_user.id,
                full_name=tg_user.full_name or None,
            )
            data["db_user"] = user

        return await handler(event, data)
