from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.asyncio
async def test_search_text_query_sends_first_card_with_actions() -> None:
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    message = Mock()
    message.text = "квартира в центре до 20000₸"
    message.from_user = Mock()
    message.from_user.id = 123
    message.chat = Mock()
    message.chat.id = 123
    message.answer_photo = AsyncMock()
    message.answer = AsyncMock()

    await search_handler.on_search_query(message)  # type: ignore[arg-type]

    assert message.answer_photo.await_count == 1
    caption = message.answer_photo.await_args.kwargs.get("caption")
    assert isinstance(caption, str)
    assert "Цена" in caption
    assert "Район" in caption
    assert "Рейтинг" in caption

    reply_markup = message.answer_photo.await_args.kwargs.get("reply_markup")
    assert reply_markup is not None

    buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
    texts = {b.text for b in buttons}
    callback_data = {b.callback_data for b in buttons}

    assert {"Следующая", "Подробнее", "Забронировать", "❤️"} <= texts
    assert {"search_next", "search_details", "search_book", "search_favorite"} <= callback_data
    assert len(buttons) == 4


@pytest.mark.asyncio
async def test_search_next_sends_next_card() -> None:
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    message = Mock()
    message.text = "квартира"
    message.from_user = Mock()
    message.from_user.id = 123
    message.chat = Mock()
    message.chat.id = 123
    message.answer_photo = AsyncMock()
    message.answer = AsyncMock()

    await search_handler.start_demo_search_from_message(message, "квартира в центре до 20000₸")  # type: ignore[arg-type]

    callback = Mock()
    callback.data = "search_next"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.bot = Mock()
    callback.bot.send_message = AsyncMock()
    callback.bot.send_photo = AsyncMock()
    callback.message = Mock()
    callback.message.answer = AsyncMock()
    callback.message.answer_photo = AsyncMock()

    await search_handler.on_search_next(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    assert callback.message.answer_photo.await_count == 1


@pytest.mark.asyncio
async def test_search_too_short_query_returns_no_results_fallback() -> None:
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    message = Mock()
    message.text = "а"
    message.from_user = Mock()
    message.from_user.id = 123
    message.chat = Mock()
    message.chat.id = 123
    message.answer_photo = AsyncMock()
    message.answer = AsyncMock()

    await search_handler.on_search_query(message)  # type: ignore[arg-type]

    assert message.answer_photo.await_count == 0
    assert message.answer.await_count == 1
    text = message.answer.await_args.args[0]
    assert isinstance(text, str)
    assert "Попробуй упростить" in text
    reply_markup = message.answer.await_args.kwargs.get("reply_markup")
    assert reply_markup is not None
    buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
    callback_data = {b.callback_data for b in buttons}
    assert {"search_flow_center", "search_flow_budget", "search_flow_family"} <= callback_data


@pytest.mark.asyncio
async def test_search_budget_too_low_returns_no_results_fallback() -> None:
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    message = Mock()
    message.text = "квартира до 1000₸"
    message.from_user = Mock()
    message.from_user.id = 123
    message.chat = Mock()
    message.chat.id = 123
    message.answer_photo = AsyncMock()
    message.answer = AsyncMock()

    await search_handler.on_search_query(message)  # type: ignore[arg-type]

    assert message.answer_photo.await_count == 0
    assert message.answer.await_count == 1


@pytest.mark.asyncio
async def test_search_exception_returns_fail_soft() -> None:
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    message = Mock()
    message.text = "квартира в центре"
    message.from_user = Mock()
    message.from_user.id = 123
    message.chat = Mock()
    message.chat.id = 123
    message.answer_photo = AsyncMock(side_effect=RuntimeError("boom"))
    message.answer = AsyncMock()

    await search_handler.on_search_query(message)  # type: ignore[arg-type]

    assert message.answer.await_count == 1
    text = message.answer.await_args.args[0]
    assert isinstance(text, str)
    assert "/start" in text


@pytest.mark.asyncio
async def test_search_details_sends_photo_gallery_and_description() -> None:
    """Test happy path: search_details sends photo gallery + detailed card with inline keyboard."""
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    callback = Mock()
    callback.data = "search_details"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.bot = Mock()
    callback.bot.send_media_group = AsyncMock()
    callback.bot.send_message = AsyncMock()

    search_handler._SESSIONS[123] = search_handler.SearchSession(
        results=search_handler._DEMO_APARTMENTS[:1],
        index=0,
    )

    await search_handler.on_search_details(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1

    # Photo gallery sent
    assert callback.bot.send_media_group.await_count == 1
    media_group = callback.bot.send_media_group.await_args.kwargs.get("media")
    assert media_group is not None
    assert len(media_group) >= 2  # At least 2 photos

    # Detailed message sent with keyboard
    assert callback.bot.send_message.await_count == 1
    sent_text = callback.bot.send_message.await_args.args[1]
    assert "Описание" in sent_text
    assert "Удобства" in sent_text
    assert "Цена" in sent_text

    reply_markup = callback.bot.send_message.await_args.kwargs.get("reply_markup")
    assert reply_markup is not None
    buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
    texts = {b.text for b in buttons}
    callback_data = {b.callback_data for b in buttons}
    assert {"Забронировать", "❤️ В избранное", "◀️ Назад к поиску"} <= texts
    assert {"search_book", "search_favorite", "search_back"} <= callback_data


@pytest.mark.asyncio
async def test_search_details_single_photo_uses_send_photo() -> None:
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    callback = Mock()
    callback.data = "search_details"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.bot = Mock()
    callback.bot.send_media_group = AsyncMock()
    callback.bot.send_photo = AsyncMock()
    callback.bot.send_message = AsyncMock()

    apartment = search_handler.DemoApartment(
        id="single-photo",
        title="Тестовая квартира",
        district="Центр",
        price_kzt=12000,
        rating=4.5,
        photo_url="https://example.com/photo-main.jpg",
        description="Описание",
        amenities=("Wi-Fi",),
        photos=("https://example.com/photo-main.jpg",),
    )
    search_handler._SESSIONS[123] = search_handler.SearchSession(results=[apartment], index=0)

    await search_handler.on_search_details(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    assert callback.bot.send_media_group.await_count == 0
    assert callback.bot.send_photo.await_count == 1
    assert callback.bot.send_message.await_count == 1


@pytest.mark.asyncio
async def test_search_book_falls_back_to_bot_when_message_send_fails() -> None:
    from bot.handlers import search as search_handler

    callback = Mock()
    callback.data = "search_book"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.bot = Mock()
    callback.bot.send_message = AsyncMock()
    callback.message = Mock()
    callback.message.answer = AsyncMock(side_effect=RuntimeError("boom"))

    await search_handler.on_search_book(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    assert callback.bot.send_message.await_count == 1
    assert callback.bot.send_message.await_args.args[0] == 123
    sent_text = callback.bot.send_message.await_args.args[1]
    assert "Бронирование" in sent_text or "/start" in sent_text


@pytest.mark.asyncio
async def test_search_book_uses_epic_4_placeholder_text() -> None:
    from bot.handlers import search as search_handler

    callback = Mock()
    callback.data = "search_book"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.bot = Mock()
    callback.bot.send_message = AsyncMock()
    callback.message = Mock()
    callback.message.answer = AsyncMock()

    await search_handler.on_search_book(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    assert callback.message.answer.await_count == 1
    sent_text = callback.message.answer.await_args.args[0]
    assert "Epic 4" in sent_text
    assert "вернуться к поиску" in sent_text


@pytest.mark.asyncio
async def test_search_back_returns_to_preview_card() -> None:
    """Test search_back returns user to preview card with correct index."""
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    # Setup session with 3 results, index=1
    search_handler._SESSIONS[123] = search_handler.SearchSession(
        results=search_handler._DEMO_APARTMENTS[:3],
        index=1,
    )

    callback = Mock()
    callback.data = "search_back"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.message = Mock()
    callback.message.answer_photo = AsyncMock()

    await search_handler.on_search_back(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    assert callback.message.answer_photo.await_count == 1

    # Verify correct apartment shown (index 1)
    caption = callback.message.answer_photo.await_args.kwargs.get("caption")
    assert isinstance(caption, str)
    assert "2/3" in caption  # index 1 in list of 3 results

    # Verify preview keyboard (not detail keyboard)
    reply_markup = callback.message.answer_photo.await_args.kwargs.get("reply_markup")
    assert reply_markup is not None
    buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
    texts = {b.text for b in buttons}
    assert "Следующая" in texts
    assert "Подробнее" in texts


@pytest.mark.asyncio
async def test_search_details_session_expired_shows_message() -> None:
    """Test search_details when session doesn't exist shows session expired message."""
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    callback = Mock()
    callback.data = "search_details"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 999  # No session for this user
    callback.bot = Mock()
    callback.bot.send_message = AsyncMock()
    callback.message = Mock()
    callback.message.answer = AsyncMock()

    await search_handler.on_search_details(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    assert callback.message.answer.await_count == 1

    sent_text = callback.message.answer.await_args.args[0]
    assert "устарел" in sent_text or "/start" in sent_text


@pytest.mark.asyncio
async def test_search_back_session_expired_shows_message() -> None:
    """Test search_back when session doesn't exist shows session expired message."""
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    callback = Mock()
    callback.data = "search_back"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 999  # No session for this user
    callback.bot = Mock()
    callback.bot.send_message = AsyncMock()
    callback.message = Mock()
    callback.message.answer = AsyncMock()

    await search_handler.on_search_back(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    assert callback.message.answer.await_count == 1

    sent_text = callback.message.answer.await_args.args[0]
    assert "устарел" in sent_text or "/start" in sent_text


@pytest.mark.asyncio
async def test_search_favorite_answers_callback_first() -> None:
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()
    search_handler._SESSIONS[123] = search_handler.SearchSession(
        results=search_handler._DEMO_APARTMENTS[:1],
        index=0,
    )

    callback = Mock()
    callback.data = "search_favorite"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.bot = Mock()
    callback.bot.send_message = AsyncMock()
    callback.message = Mock()
    callback.message.answer = AsyncMock()

    await search_handler.on_search_favorite(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    assert callback.message.answer.await_count == 1
    assert "Сохранено" in callback.message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_search_details_exception_returns_fail_soft() -> None:
    """Test search_details exception handling sends fail-soft message."""
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    search_handler._SESSIONS[123] = search_handler.SearchSession(
        results=search_handler._DEMO_APARTMENTS[:1],
        index=0,
    )

    callback = Mock()
    callback.data = "search_details"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.bot = Mock()
    callback.bot.send_media_group = AsyncMock(side_effect=RuntimeError("boom"))
    callback.bot.send_message = AsyncMock()
    callback.message = Mock()
    callback.message.answer = AsyncMock()

    await search_handler.on_search_details(callback)  # type: ignore[arg-type]

    assert callback.answer.await_count == 1
    # Fail-soft message sent via message.answer or bot.send_message
    assert callback.message.answer.await_count >= 1 or callback.bot.send_message.await_count >= 1


@pytest.mark.asyncio
async def test_search_details_escapes_html_user_content() -> None:
    from bot.handlers import search as search_handler

    search_handler._SESSIONS.clear()

    callback = Mock()
    callback.data = "search_details"
    callback.answer = AsyncMock()
    callback.from_user = Mock()
    callback.from_user.id = 123
    callback.bot = Mock()
    callback.bot.send_media_group = AsyncMock()
    callback.bot.send_message = AsyncMock()

    apartment = search_handler.DemoApartment(
        id="html-escape",
        title="A < B",
        district="Центр & Восток",
        price_kzt=13000,
        rating=4.5,
        photo_url="https://example.com/photo-main.jpg",
        description="Описание с <b>тегом</b>",
        amenities=("Wi-Fi", "<script>alert(1)</script>"),
        photos=(
            "https://example.com/photo-main.jpg",
            "https://example.com/photo-2.jpg",
        ),
    )
    search_handler._SESSIONS[123] = search_handler.SearchSession(results=[apartment], index=0)

    await search_handler.on_search_details(callback)  # type: ignore[arg-type]

    sent_text = callback.bot.send_message.await_args.args[1]
    assert "&lt;" in sent_text
    assert "&amp;" in sent_text


def test_preview_keyboard_layout_mobile_friendly() -> None:
    from bot.handlers import search as search_handler

    markup = search_handler._build_card_keyboard()
    rows = markup.inline_keyboard
    assert len(rows) == 2
    assert all(len(row) == 2 for row in rows)

    row_1_callbacks = [button.callback_data for button in rows[0]]
    row_2_callbacks = [button.callback_data for button in rows[1]]
    assert row_1_callbacks == ["search_next", "search_details"]
    assert row_2_callbacks == ["search_book", "search_favorite"]


def test_detail_keyboard_layout_mobile_friendly() -> None:
    from bot.handlers import search as search_handler

    markup = search_handler._build_detail_card_keyboard()
    rows = markup.inline_keyboard
    assert len(rows) == 3
    assert all(len(row) == 1 for row in rows)
