from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.asyncio
async def test_menu_command_sends_main_menu_with_3_buttons() -> None:
    """Test /menu command displays main menu with exactly 3 buttons (Rule of 3)."""
    from bot.handlers.common import cmd_menu

    message = Mock()
    message.answer = AsyncMock()

    await cmd_menu(message)  # type: ignore[arg-type]

    assert message.answer.await_count == 1
    text = message.answer.await_args.args[0]
    assert isinstance(text, str)
    assert len(text) > 0

    reply_markup = message.answer.await_args.kwargs.get("reply_markup")
    assert reply_markup is not None

    # Verify Rule of 3: exactly 3 buttons
    buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
    assert len(buttons) == 3, "Main menu must have exactly 3 buttons (Rule of 3)"

    # Verify button labels
    button_texts = {btn.text for btn in buttons}
    assert "🔍 Поиск квартир" in button_texts
    assert "📋 Мои бронирования" in button_texts
    assert "❓ Помощь" in button_texts

    # Verify button callback data
    button_callbacks = {btn.callback_data for btn in buttons}
    assert "nav_search" in button_callbacks
    assert "nav_bookings" in button_callbacks
    assert "nav_help" in button_callbacks


@pytest.mark.asyncio
async def test_main_menu_callback_sends_main_menu() -> None:
    """Test callback main_menu displays main menu."""
    from bot.handlers.common import on_main_menu

    callback_query = Mock()
    callback_query.answer = AsyncMock()
    callback_query.message = Mock()
    callback_query.message.answer = AsyncMock()
    callback_query.from_user = Mock()
    callback_query.from_user.id = 123

    await on_main_menu(callback_query)  # type: ignore[arg-type]

    assert callback_query.answer.await_count == 1
    assert callback_query.message.answer.await_count == 1

    text = callback_query.message.answer.await_args.args[0]
    assert isinstance(text, str)
    assert len(text) > 0

    reply_markup = callback_query.message.answer.await_args.kwargs.get("reply_markup")
    assert reply_markup is not None

    buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
    assert len(buttons) == 3


@pytest.mark.asyncio
async def test_main_menu_callback_via_bot_when_message_missing() -> None:
    """Test callback main_menu sends via bot when callback.message is None."""
    from bot.handlers.common import on_main_menu

    bot = Mock()
    bot.send_message = AsyncMock()

    callback_query = Mock()
    callback_query.answer = AsyncMock()
    callback_query.message = None
    callback_query.bot = bot
    callback_query.from_user = Mock()
    callback_query.from_user.id = 123

    await on_main_menu(callback_query)  # type: ignore[arg-type]

    assert callback_query.answer.await_count == 1
    assert bot.send_message.await_count == 1
    assert bot.send_message.await_args.args[0] == 123

    text = bot.send_message.await_args.args[1]
    assert isinstance(text, str)
    assert len(text) > 0

    reply_markup = bot.send_message.await_args.kwargs.get("reply_markup")
    assert reply_markup is not None


@pytest.mark.asyncio
async def test_back_button_pops_navigation_stack_and_returns_to_previous_screen() -> None:
    """Test nav_back callback pops from nav stack and returns to previous state."""
    from bot.handlers.common import _NAVIGATION_STACK, _push_nav_state, on_back_button

    # Setup: push main_menu to navigation stack
    user_id = 456
    _push_nav_state(user_id, "main_menu")
    _push_nav_state(user_id, "nav_help")  # Simulating user went to help screen

    assert len(_NAVIGATION_STACK.get(user_id, [])) == 2

    callback_query = Mock()
    callback_query.answer = AsyncMock()
    callback_query.message = Mock()
    callback_query.message.answer = AsyncMock()
    callback_query.from_user = Mock()
    callback_query.from_user.id = user_id
    callback_query.data = "nav_back"

    await on_back_button(callback_query)  # type: ignore[arg-type]

    # Should pop current state and navigate back to main_menu
    assert callback_query.answer.await_count == 1
    # After going back, stack should have 1 item (main_menu)
    assert len(_NAVIGATION_STACK.get(user_id, [])) == 1


@pytest.mark.asyncio
async def test_back_button_handles_empty_navigation_stack() -> None:
    """Test nav_back with empty stack shows main menu."""
    from bot.handlers.common import _NAVIGATION_STACK, on_back_button

    user_id = 789
    # Ensure navigation stack is empty for this user
    _NAVIGATION_STACK.pop(user_id, None)

    callback_query = Mock()
    callback_query.answer = AsyncMock()
    callback_query.message = Mock()
    callback_query.message.answer = AsyncMock()
    callback_query.from_user = Mock()
    callback_query.from_user.id = user_id

    await on_back_button(callback_query)  # type: ignore[arg-type]

    assert callback_query.answer.await_count == 1
    # Should show main menu when stack is empty
    assert callback_query.message.answer.await_count == 1


@pytest.mark.asyncio
async def test_pd_consent_accept_sets_consent_to_true() -> None:
    """Test PD consent acceptance sets consent flag."""
    from bot.handlers.common import _PD_CONSENT, _check_pd_consent, on_pd_consent_accept

    user_id = 999
    # Ensure no consent initially
    _PD_CONSENT.pop(user_id, None)

    callback_query = Mock()
    callback_query.answer = AsyncMock()
    callback_query.message = Mock()
    callback_query.message.answer = AsyncMock()
    callback_query.from_user = Mock()
    callback_query.from_user.id = user_id

    await on_pd_consent_accept(callback_query)  # type: ignore[arg-type]

    assert callback_query.answer.await_count == 1
    assert callback_query.message.answer.await_count == 1
    assert "Спасибо" in callback_query.message.answer.await_args.args[0]
    assert _check_pd_consent(user_id) is True


@pytest.mark.asyncio
async def test_pd_consent_decline_shows_message() -> None:
    """Test PD consent decline shows appropriate message."""
    from bot.handlers.common import on_pd_consent_decline

    user_id = 888
    callback_query = Mock()
    callback_query.answer = AsyncMock()
    callback_query.message = Mock()
    callback_query.message.answer = AsyncMock()
    callback_query.from_user = Mock()
    callback_query.from_user.id = user_id

    await on_pd_consent_decline(callback_query)  # type: ignore[arg-type]

    assert callback_query.answer.await_count == 1
    assert callback_query.message.answer.await_count == 1
    text = callback_query.message.answer.await_args.args[0]
    assert "Без согласия" in text or "недоступны" in text


@pytest.mark.asyncio
async def test_pd_consent_request_shows_consent_dialog() -> None:
    """Test PD consent request shows dialog with two buttons."""
    from bot.handlers.common import _request_pd_consent

    callback_query = Mock()
    callback_query.message = Mock()
    callback_query.message.answer = AsyncMock()
    callback_query.from_user = Mock()
    callback_query.from_user.id = 777

    await _request_pd_consent(callback_query)  # type: ignore[arg-type]

    assert callback_query.message.answer.await_count == 1
    text = callback_query.message.answer.await_args.args[0]
    assert "Согласие" in text or "персональных данных" in text

    reply_markup = callback_query.message.answer.await_args.kwargs.get("reply_markup")
    assert reply_markup is not None
    buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
    assert len(buttons) == 2
    button_callbacks = {btn.callback_data for btn in buttons}
    assert "pd_consent_accept" in button_callbacks
    assert "pd_consent_decline" in button_callbacks
