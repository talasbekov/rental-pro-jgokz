"""Tests for ReplyKeyboard persistent menu navigation (Story 1.1.5)."""

from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import ReplyKeyboardMarkup

from bot.keyboards.reply import _build_main_reply_keyboard


class TestReplyKeyboardBuilder:
    """Test ReplyKeyboard builder function."""

    def test_build_main_reply_keyboard_returns_markup(self):
        """Test that builder returns ReplyKeyboardMarkup."""
        keyboard = _build_main_reply_keyboard()
        assert isinstance(keyboard, ReplyKeyboardMarkup)

    def test_build_main_reply_keyboard_has_4_buttons(self):
        """Test that keyboard has exactly 4 buttons."""
        keyboard = _build_main_reply_keyboard()
        # Count all buttons across all rows
        total_buttons = sum(len(row) for row in keyboard.keyboard)
        assert total_buttons == 4

    def test_build_main_reply_keyboard_has_correct_button_text(self):
        """Test that keyboard has correct button labels."""
        keyboard = _build_main_reply_keyboard()
        # Flatten all buttons to a list
        all_buttons = [btn for row in keyboard.keyboard for btn in row]
        button_texts = [btn.text for btn in all_buttons]

        assert "🔍 Поиск квартир" in button_texts
        assert "📋 Мои бронирования" in button_texts
        assert "❤️ Избранное" in button_texts
        assert "❓ Помощь" in button_texts

    def test_build_main_reply_keyboard_is_persistent(self):
        """Test that keyboard is persistent."""
        keyboard = _build_main_reply_keyboard()
        assert keyboard.is_persistent is True

    def test_build_main_reply_keyboard_is_resizable(self):
        """Test that keyboard is resizable."""
        keyboard = _build_main_reply_keyboard()
        assert keyboard.resize_keyboard is True

    def test_build_main_reply_keyboard_has_placeholder(self):
        """Test that keyboard has input field placeholder."""
        keyboard = _build_main_reply_keyboard()
        assert keyboard.input_field_placeholder is not None
        assert len(keyboard.input_field_placeholder) > 0


class TestReplyKeyboardHandlers:
    """Test message handlers for ReplyKeyboard buttons."""

    @pytest.mark.asyncio
    async def test_search_button_triggers_search_flow(self):
        """Test that 'Поиск квартир' button triggers search flow."""
        from bot.handlers.common import on_search_button

        message = Mock()
        message.answer = AsyncMock()
        message.answer_photo = AsyncMock()
        message.from_user = Mock()
        message.from_user.id = 123

        await on_search_button(message)  # type: ignore[arg-type]

        assert message.answer.await_count == 1
        text = message.answer.await_args.args[0]
        assert "Напиши, что ищешь" in text or "район, даты, бюджет" in text

        # Verify ReplyKeyboard is included
        reply_markup = message.answer.await_args.kwargs.get("reply_markup")
        assert reply_markup is not None
        assert isinstance(reply_markup, ReplyKeyboardMarkup)

        # And the demo search flow sends a card
        assert message.answer_photo.await_count == 1

    @pytest.mark.asyncio
    async def test_bookings_button_shows_placeholder(self):
        """Test that 'Мои бронирования' button shows Epic 4 placeholder."""
        from bot.handlers.common import on_bookings_button

        message = Mock()
        message.answer = AsyncMock()

        await on_bookings_button(message)  # type: ignore[arg-type]

        assert message.answer.await_count == 1
        text = message.answer.await_args.args[0]
        assert "Epic 4" in text

        # Verify ReplyKeyboard is included
        reply_markup = message.answer.await_args.kwargs.get("reply_markup")
        assert reply_markup is not None
        assert isinstance(reply_markup, ReplyKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_favorites_button_shows_placeholder(self):
        """Test that 'Избранное' button shows Epic 3 placeholder."""
        from bot.handlers.common import on_favorites_button

        message = Mock()
        message.answer = AsyncMock()

        await on_favorites_button(message)  # type: ignore[arg-type]

        assert message.answer.await_count == 1
        text = message.answer.await_args.args[0]
        assert "Epic 3" in text

        # Verify ReplyKeyboard is included
        reply_markup = message.answer.await_args.kwargs.get("reply_markup")
        assert reply_markup is not None
        assert isinstance(reply_markup, ReplyKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_help_button_shows_help(self):
        """Test that 'Помощь' button shows help message."""
        from bot.handlers.common import on_help_button

        message = Mock()
        message.answer = AsyncMock()

        await on_help_button(message)  # type: ignore[arg-type]

        assert message.answer.await_count == 1
        text = message.answer.await_args.args[0]
        assert "Помощь" in text

        # Verify ReplyKeyboard is included
        reply_markup = message.answer.await_args.kwargs.get("reply_markup")
        assert reply_markup is not None
        assert isinstance(reply_markup, ReplyKeyboardMarkup)


class TestReplyKeyboardPersistence:
    """Test that ReplyKeyboard remains visible across interactions."""

    @pytest.mark.asyncio
    async def test_keyboard_persists_after_search(self):
        """Test that callback text responses default to ReplyKeyboard."""
        from bot.handlers.search import _send_callback_text

        callback = Mock()
        callback.from_user = Mock()
        callback.from_user.id = 123
        callback.bot = Mock()
        callback.bot.send_message = AsyncMock()
        callback.message = Mock()
        callback.message.answer = AsyncMock()

        await _send_callback_text(callback, "ok")  # type: ignore[arg-type]

        assert callback.message.answer.await_count == 1
        reply_markup = callback.message.answer.await_args.kwargs.get("reply_markup")
        assert isinstance(reply_markup, ReplyKeyboardMarkup)


class TestReplyKeyboardFailSoft:
    """Test fail-soft behavior for ReplyKeyboard handlers."""

    @pytest.mark.asyncio
    async def test_exception_in_handler_returns_fail_soft_message(self):
        """Test that exception in handler returns fail-soft message with ReplyKeyboard."""
        from bot.handlers.common import on_bookings_button

        message = Mock()
        message.answer = AsyncMock(side_effect=[RuntimeError("boom"), None])

        await on_bookings_button(message)  # type: ignore[arg-type]

        assert message.answer.await_count == 2
        text = message.answer.await_args_list[1].args[0]
        assert isinstance(text, str)
        assert "что-то пошло не так" in text

        reply_markup = message.answer.await_args_list[1].kwargs.get("reply_markup")
        assert isinstance(reply_markup, ReplyKeyboardMarkup)
