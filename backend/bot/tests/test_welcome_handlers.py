from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.asyncio
async def test_start_sends_ru_welcome_with_try_search_button() -> None:
    from bot.handlers.start import cmd_start

    message = Mock()
    message.answer = AsyncMock()

    await cmd_start(message)  # type: ignore[arg-type]

    # Story 1.1.5: Now sends 2 messages (welcome + ReplyKeyboard, then inline buttons)
    assert message.answer.await_count == 2

    # First call: welcome text with ReplyKeyboard
    first_call_text = message.answer.await_args_list[0].args[0]
    assert isinstance(first_call_text, str)
    assert "Привет" in first_call_text
    assert "напиши запрос" in first_call_text or "напишите запрос" in first_call_text

    first_call_markup = message.answer.await_args_list[0].kwargs.get("reply_markup")
    assert first_call_markup is not None
    # First message should have ReplyKeyboard
    from aiogram.types import ReplyKeyboardMarkup
    assert isinstance(first_call_markup, ReplyKeyboardMarkup)

    # Second call: inline buttons
    second_call_markup = message.answer.await_args_list[1].kwargs.get("reply_markup")
    assert second_call_markup is not None

    # aiogram InlineKeyboardMarkup has `inline_keyboard: list[list[InlineKeyboardButton]]`
    buttons = [btn for row in second_call_markup.inline_keyboard for btn in row]
    assert len(buttons) == 2
    assert buttons[0].text == "Попробовать поиск"
    assert buttons[0].callback_data == "try_search"
    assert buttons[1].text == "📋 Главное меню"
    assert buttons[1].callback_data == "main_menu"


@pytest.mark.asyncio
async def test_try_search_answers_callback_and_starts_demo_search_via_message() -> None:
    from bot.handlers.welcome import on_try_search

    callback_query = Mock()
    callback_query.answer = AsyncMock()

    callback_query.message = Mock()
    callback_query.message.answer_photo = AsyncMock()
    callback_query.from_user = Mock()
    callback_query.from_user.id = 123

    await on_try_search(callback_query)  # type: ignore[arg-type]

    assert callback_query.answer.await_count == 1
    assert callback_query.message.answer_photo.await_count == 1
    caption = callback_query.message.answer_photo.await_args.kwargs.get("caption")
    assert isinstance(caption, str)
    assert "Цена" in caption
    assert "Район" in caption
    assert "Рейтинг" in caption


@pytest.mark.asyncio
async def test_try_search_starts_demo_search_via_bot_when_callback_message_missing() -> None:
    from bot.handlers.welcome import on_try_search

    bot = Mock()
    bot.send_photo = AsyncMock()

    callback_query = Mock()
    callback_query.answer = AsyncMock()
    callback_query.message = None
    callback_query.bot = bot
    callback_query.from_user = Mock()
    callback_query.from_user.id = 123

    await on_try_search(callback_query)  # type: ignore[arg-type]

    assert callback_query.answer.await_count == 1
    assert bot.send_photo.await_count == 1
    assert bot.send_photo.await_args.args[0] == 123
    caption = bot.send_photo.await_args.kwargs.get("caption")
    assert isinstance(caption, str)
    assert "Цена" in caption
    assert "Район" in caption
    assert "Рейтинг" in caption


@pytest.mark.asyncio
async def test_help_command_still_responds() -> None:
    from bot.handlers.common import cmd_help

    message = Mock()
    message.answer = AsyncMock()

    await cmd_help(message)  # type: ignore[arg-type]

    assert message.answer.await_count == 1


@pytest.mark.asyncio
async def test_fallback_still_responds() -> None:
    from bot.handlers.common import fallback

    message = Mock()
    message.answer = AsyncMock()

    await fallback(message)  # type: ignore[arg-type]

    assert message.answer.await_count == 1
