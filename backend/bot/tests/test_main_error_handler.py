from __future__ import annotations

import os
from unittest.mock import AsyncMock, Mock

import pytest

# Required settings for importing bot.main in isolated test context.
os.environ.setdefault("PROJECT_NAME", "test-project")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "test-password")
os.environ.setdefault("POSTGRES_DB", "app")
os.environ.setdefault("FIRST_SUPERUSER", "admin@example.com")
os.environ.setdefault("FIRST_SUPERUSER_PASSWORD", "test-password")

from bot.main import FAIL_SOFT_ERROR_TEXT, on_error
from aiogram.types import ReplyKeyboardMarkup


@pytest.mark.asyncio
async def test_on_error_callback_query_answers_and_sends_message() -> None:
    event = Mock()
    event.exception = RuntimeError("boom")

    update = Mock()
    callback_query = Mock()
    callback_query.answer = AsyncMock()
    callback_query.from_user = Mock()
    callback_query.from_user.id = 321
    update.callback_query = callback_query
    update.message = None
    update.edited_message = None
    update.channel_post = None
    update.edited_channel_post = None
    event.update = update

    bot = Mock()
    bot.send_message = AsyncMock()

    await on_error(event, bot)

    assert callback_query.answer.await_count == 1
    assert bot.send_message.await_count == 1
    assert bot.send_message.await_args.args[0] == 321
    assert bot.send_message.await_args.args[1] == FAIL_SOFT_ERROR_TEXT
    reply_markup = bot.send_message.await_args.kwargs.get("reply_markup")
    assert isinstance(reply_markup, ReplyKeyboardMarkup)


@pytest.mark.asyncio
async def test_on_error_message_sends_fail_soft_text() -> None:
    event = Mock()
    event.exception = RuntimeError("boom")

    update = Mock()
    update.callback_query = None
    update.message = Mock()
    update.message.chat = Mock()
    update.message.chat.id = 999
    update.edited_message = None
    update.channel_post = None
    update.edited_channel_post = None
    event.update = update

    bot = Mock()
    bot.send_message = AsyncMock()

    await on_error(event, bot)

    assert bot.send_message.await_count == 1
    assert bot.send_message.await_args.args[0] == 999
    assert bot.send_message.await_args.args[1] == FAIL_SOFT_ERROR_TEXT
    reply_markup = bot.send_message.await_args.kwargs.get("reply_markup")
    assert isinstance(reply_markup, ReplyKeyboardMarkup)


@pytest.mark.asyncio
async def test_on_error_edited_message_sends_fail_soft_text() -> None:
    event = Mock()
    event.exception = RuntimeError("boom")

    update = Mock()
    update.callback_query = None
    update.message = None
    update.edited_message = Mock()
    update.edited_message.chat = Mock()
    update.edited_message.chat.id = 111
    update.channel_post = None
    update.edited_channel_post = None
    event.update = update

    bot = Mock()
    bot.send_message = AsyncMock()

    await on_error(event, bot)

    assert bot.send_message.await_count == 1
    assert bot.send_message.await_args.args[0] == 111
    assert bot.send_message.await_args.args[1] == FAIL_SOFT_ERROR_TEXT
    reply_markup = bot.send_message.await_args.kwargs.get("reply_markup")
    assert isinstance(reply_markup, ReplyKeyboardMarkup)
