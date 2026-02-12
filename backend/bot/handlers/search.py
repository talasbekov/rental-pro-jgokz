from __future__ import annotations

import logging
import re
from html import escape
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery, InputMediaPhoto, Message, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.reply import _build_main_reply_keyboard

router = Router()

logger = logging.getLogger(__name__)

_FAIL_SOFT_TEXT = (
    "Кажется, что-то пошло не так. Попробуй ещё раз или отправь /start."
)

_NO_RESULTS_TEXT = (
    "Пока не нашёл подходящих вариантов по запросу.\n"
    "Попробуй упростить: район + даты или бюджет.\n"
    "Пример: “1 комната в центре на завтра до 15000₸”."
)

_SESSION_EXPIRED_TEXT = (
    "Похоже, поиск устарел. Напиши запрос ещё раз или отправь /start."
)

_MENU_BUTTON_TEXTS = {
    "🔍 Поиск квартир",
    "📋 Мои бронирования",
    "❤️ Избранное",
    "❓ Помощь",
}


@dataclass(frozen=True)
class DemoApartment:
    id: str
    title: str
    district: str
    price_kzt: int
    rating: float
    photo_url: str  # First photo for backward compatibility
    description: str = ""
    amenities: tuple[str, ...] = ()
    photos: tuple[str, ...] = ()  # Full photo gallery (2-4 photos)


@dataclass
class SearchSession:
    results: list[DemoApartment]
    index: int = 0
    favorites: set[str] | None = None

    def __post_init__(self) -> None:
        if self.favorites is None:
            self.favorites = set()


_SESSIONS: dict[int, SearchSession] = {}

_STRUCTURED_FALLBACK_QUERIES: dict[str, str] = {
    "search_flow_center": "1 комната в центре на завтра до 20000₸",
    "search_flow_budget": "квартира до 15000₸ на завтра",
    "search_flow_family": "2-комнатная для семьи на завтра до 25000₸",
}

_DEMO_APARTMENTS: list[DemoApartment] = [
    DemoApartment(
        id="demo-apt-1",
        title="Уютная 1-комнатная в центре",
        district="Центр",
        price_kzt=14500,
        rating=4.8,
        photo_url="https://picsum.photos/seed/rental-pro-demo-1/640/360",
        description="Светлая квартира в самом центре города. Идеально для бизнес-поездок. Рядом кафе и метро.",
        amenities=("Wi-Fi", "Кухня", "Стиральная машина", "Кондиционер"),
        photos=(
            "https://picsum.photos/seed/rental-pro-demo-1/640/360",
            "https://picsum.photos/seed/rental-pro-demo-1a/640/360",
            "https://picsum.photos/seed/rental-pro-demo-1b/640/360",
        ),
    ),
    DemoApartment(
        id="demo-apt-2",
        title="Студия рядом с метро",
        district="Алмалинский",
        price_kzt=12000,
        rating=4.6,
        photo_url="https://picsum.photos/seed/rental-pro-demo-2/640/360",
        description="Компактная студия с удобной планировкой. 5 минут пешком от метро Абая.",
        amenities=("Wi-Fi", "Кухня", "Холодильник"),
        photos=(
            "https://picsum.photos/seed/rental-pro-demo-2/640/360",
            "https://picsum.photos/seed/rental-pro-demo-2a/640/360",
        ),
    ),
    DemoApartment(
        id="demo-apt-3",
        title="2-комнатная для семьи",
        district="Бостандыкский",
        price_kzt=17500,
        rating=4.7,
        photo_url="https://picsum.photos/seed/rental-pro-demo-3/640/360",
        description="Просторная квартира с двумя спальнями. Подходит для семьи с детьми. Тихий район.",
        amenities=("Wi-Fi", "Кухня", "Стиральная машина", "Парковка", "Детская кроватка"),
        photos=(
            "https://picsum.photos/seed/rental-pro-demo-3/640/360",
            "https://picsum.photos/seed/rental-pro-demo-3a/640/360",
            "https://picsum.photos/seed/rental-pro-demo-3b/640/360",
            "https://picsum.photos/seed/rental-pro-demo-3c/640/360",
        ),
    ),
    DemoApartment(
        id="demo-apt-4",
        title="Апартаменты с видом на горы",
        district="Медеуский",
        price_kzt=22000,
        rating=4.9,
        photo_url="https://picsum.photos/seed/rental-pro-demo-4/640/360",
        description="Премиум-квартира с панорамными окнами и видом на горы. Современный ремонт и техника.",
        amenities=("Wi-Fi", "Кухня", "Стиральная машина", "Кондиционер", "Балкон", "Парковка"),
        photos=(
            "https://picsum.photos/seed/rental-pro-demo-4/640/360",
            "https://picsum.photos/seed/rental-pro-demo-4a/640/360",
            "https://picsum.photos/seed/rental-pro-demo-4b/640/360",
        ),
    ),
]


def _user_id_from_message(message: Message) -> int:
    if message.from_user is not None:
        return message.from_user.id
    return message.chat.id


def _user_id_from_callback(callback: CallbackQuery) -> int:
    if callback.from_user is not None:
        return callback.from_user.id
    raise RuntimeError("CallbackQuery.from_user is required for search flow")


def _bot_from_callback(callback: CallbackQuery) -> Any:
    bot = callback.bot
    if bot is None:
        raise RuntimeError("CallbackQuery.bot is required for search flow")
    return bot


def _build_card_keyboard() -> Any:
    """Build inline keyboard for search result card."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Следующая", callback_data="search_next")
    keyboard.button(text="Подробнее", callback_data="search_details")
    keyboard.button(text="Забронировать", callback_data="search_book")
    keyboard.button(text="❤️", callback_data="search_favorite")
    keyboard.adjust(2)  # Two rows to keep card controls compact
    return keyboard.as_markup()


def _build_no_results_keyboard() -> Any:
    """Build inline keyboard for no results fallback (Rule of 3 + back button)."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Центр до 20000₸", callback_data="search_flow_center")
    keyboard.button(text="До 15000₸", callback_data="search_flow_budget")
    keyboard.button(text="Для семьи", callback_data="search_flow_family")
    keyboard.button(text="◀️ Назад", callback_data="nav_back")
    keyboard.adjust(1)
    return keyboard.as_markup()


def _build_detail_card_keyboard() -> Any:
    """Build inline keyboard for detail card (Rule of 3: max 3 buttons)."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Забронировать", callback_data="search_book")
    keyboard.button(text="❤️ В избранное", callback_data="search_favorite")
    keyboard.button(text="◀️ Назад к поиску", callback_data="search_back")
    keyboard.adjust(1)  # 3 buttons, one per row for better mobile UX
    return keyboard.as_markup()


def _format_caption(apartment: DemoApartment, index: int, total: int) -> str:
    return (
        f"🏠 {apartment.title}\n"
        f"💰 Цена: {apartment.price_kzt}₸/сутки\n"
        f"📍 Район: {apartment.district}\n"
        f"⭐ Рейтинг: {apartment.rating:.1f}\n\n"
        f"{index + 1}/{total}"
    )


def _format_detail_card(apartment: DemoApartment) -> str:
    """Format detailed apartment card with description and amenities."""
    amenities_text = (
        ", ".join(escape(amenity) for amenity in apartment.amenities)
        if apartment.amenities
        else "—"
    )
    title = escape(apartment.title)
    district = escape(apartment.district)
    description = escape(apartment.description)
    return (
        f"<b>🏠 {title}</b>\n\n"
        f"💰 <b>Цена:</b> {apartment.price_kzt}₸/сутки\n"
        f"📍 <b>Район:</b> {district}\n"
        f"⭐ <b>Рейтинг:</b> {apartment.rating:.1f}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"✨ <b>Удобства:</b>\n{amenities_text}"
    )


def _extract_budget_kzt(query: str) -> int | None:
    m = re.search(r"\bдо\s*(\d{4,7})\b", query.lower())
    if m:
        return int(m.group(1))

    nums = re.findall(r"\b(\d{4,7})\b", query)
    if nums:
        return int(nums[-1])
    return None


def _extract_district_hint(query: str) -> str | None:
    q = query.lower()
    for district in {"центр", "алмалин", "бостан", "медеу"}:
        if district in q:
            return district
    return None


def _demo_search(query: str) -> list[DemoApartment]:
    q = query.strip()
    if len(q) < 3:
        return []

    budget = _extract_budget_kzt(q)
    district_hint = _extract_district_hint(q)

    def score(apartment: DemoApartment) -> tuple[int, int]:
        district_score = 1 if district_hint and district_hint in apartment.district.lower() else 0
        budget_score = 1 if budget is not None and apartment.price_kzt <= budget else 0
        return (district_score, budget_score)

    filtered: Iterable[DemoApartment] = _DEMO_APARTMENTS
    if budget is not None:
        filtered = [a for a in filtered if a.price_kzt <= budget]
        if not filtered:
            return []

    return sorted(filtered, key=lambda a: score(a), reverse=True)


async def _send_apartment_card(
    *,
    send_photo: Any,
    apartment: DemoApartment,
    index: int,
    total: int,
) -> None:
    photo = URLInputFile(apartment.photo_url)
    caption = _format_caption(apartment, index=index, total=total)
    await send_photo(
        photo=photo,
        caption=caption,
        reply_markup=_build_card_keyboard(),
    )


async def _send_callback_text(callback: CallbackQuery, text: str, *, reply_markup: Any | None = None) -> None:
    """Send text message to user via callback with optional markup.

    If no reply_markup provided, uses main ReplyKeyboard to ensure it persists.
    """
    user_id = _user_id_from_callback(callback)
    # Use ReplyKeyboard by default if no markup specified
    if reply_markup is None:
        reply_markup = _build_main_reply_keyboard()

    if callback.message is not None:
        try:
            await callback.message.answer(text, reply_markup=reply_markup)
            return
        except Exception:
            logger.exception("Failed to answer callback via message")

    bot = _bot_from_callback(callback)
    await bot.send_message(user_id, text, reply_markup=reply_markup)


async def start_demo_search_from_message(message: Message, query: str) -> None:
    user_id = _user_id_from_message(message)
    results = _demo_search(query)
    if not results:
        await message.answer(
            _NO_RESULTS_TEXT,
            reply_markup=_build_no_results_keyboard(),
        )
        return

    _SESSIONS[user_id] = SearchSession(results=results, index=0)
    await _send_apartment_card(
        send_photo=message.answer_photo,
        apartment=results[0],
        index=0,
        total=len(results),
    )


async def start_demo_search_from_callback(callback: CallbackQuery, query: str) -> None:
    user_id = _user_id_from_callback(callback)
    results = _demo_search(query)
    if not results:
        await _send_callback_text(
            callback,
            _NO_RESULTS_TEXT,
            reply_markup=_build_no_results_keyboard(),
        )
        return

    _SESSIONS[user_id] = SearchSession(results=results, index=0)
    if callback.message is not None:
        await _send_apartment_card(
            send_photo=callback.message.answer_photo,
            apartment=results[0],
            index=0,
            total=len(results),
        )
    else:
        bot = _bot_from_callback(callback)
        await bot.send_photo(
            user_id,
            photo=URLInputFile(results[0].photo_url),
            caption=_format_caption(results[0], index=0, total=len(results)),
            reply_markup=_build_card_keyboard(),
        )


@router.message(
    F.text & ~F.text.startswith("/") & ~F.text.in_(_MENU_BUTTON_TEXTS)
)
async def on_search_query(message: Message) -> None:
    try:
        await start_demo_search_from_message(message, message.text or "")
    except Exception:
        logger.exception("Search flow failed")
        try:
            await message.answer(
                _FAIL_SOFT_TEXT,
                reply_markup=_build_main_reply_keyboard(),
            )
        except Exception:
            logger.exception("Failed to send fail-soft message in search handler")


@router.callback_query(F.data == "search_next")
async def on_search_next(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        logger.exception("Failed to answer callback query")

    try:
        user_id = _user_id_from_callback(callback)
        session = _SESSIONS.get(user_id)
        if session is None:
            await _send_callback_text(callback, _SESSION_EXPIRED_TEXT)
            return

        session.index += 1
        if session.index >= len(session.results):
            session.index = len(session.results) - 1
            text = "Это были все варианты. Напиши новый запрос или отправь /start."
            await _send_callback_text(callback, text)
            return

        apartment = session.results[session.index]
        if callback.message is not None:
            await _send_apartment_card(
                send_photo=callback.message.answer_photo,
                apartment=apartment,
                index=session.index,
                total=len(session.results),
            )
        else:
            bot = _bot_from_callback(callback)
            await bot.send_photo(
                user_id,
                photo=URLInputFile(apartment.photo_url),
                caption=_format_caption(apartment, index=session.index, total=len(session.results)),
                reply_markup=_build_card_keyboard(),
            )
    except Exception:
        logger.exception("Failed to process search_next")
        try:
            await _send_callback_text(callback, _FAIL_SOFT_TEXT)
        except Exception:
            logger.exception("Failed to send fail-soft message in search_next")


@router.callback_query(F.data == "search_details")
async def on_search_details(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        logger.exception("Failed to answer callback query")

    try:
        user_id = _user_id_from_callback(callback)
        session = _SESSIONS.get(user_id)
        if session is None:
            await _send_callback_text(callback, _SESSION_EXPIRED_TEXT)
            return

        apartment = session.results[session.index]
        bot = _bot_from_callback(callback)

        # Send photo gallery if multiple photos available, otherwise send a single photo.
        photos = apartment.photos or ((apartment.photo_url,) if apartment.photo_url else ())
        if len(photos) >= 2:
            media_group = [
                InputMediaPhoto(media=URLInputFile(photo_url))
                for photo_url in photos
            ]
            await bot.send_media_group(user_id, media=media_group)
        elif len(photos) == 1:
            await bot.send_photo(user_id, photo=URLInputFile(photos[0]))

        # Send detailed description with inline keyboard
        detail_text = _format_detail_card(apartment)
        await bot.send_message(
            user_id,
            detail_text,
            parse_mode="HTML",
            reply_markup=_build_detail_card_keyboard(),
        )
    except Exception:
        logger.exception("Failed to process search_details")
        try:
            await _send_callback_text(callback, _FAIL_SOFT_TEXT)
        except Exception:
            logger.exception("Failed to send fail-soft message in search_details")


@router.callback_query(F.data == "search_back")
async def on_search_back(callback: CallbackQuery) -> None:
    """Return to search results (preview card) from detail view."""
    try:
        await callback.answer()
    except Exception:
        logger.exception("Failed to answer callback query")

    try:
        user_id = _user_id_from_callback(callback)
        session = _SESSIONS.get(user_id)
        if session is None:
            await _send_callback_text(callback, _SESSION_EXPIRED_TEXT)
            return

        # Show current apartment in preview format
        apartment = session.results[session.index]
        if callback.message is not None:
            await _send_apartment_card(
                send_photo=callback.message.answer_photo,
                apartment=apartment,
                index=session.index,
                total=len(session.results),
            )
        else:
            bot = _bot_from_callback(callback)
            await bot.send_photo(
                user_id,
                photo=URLInputFile(apartment.photo_url),
                caption=_format_caption(apartment, index=session.index, total=len(session.results)),
                reply_markup=_build_card_keyboard(),
            )
    except Exception:
        logger.exception("Failed to process search_back")
        try:
            await _send_callback_text(callback, _FAIL_SOFT_TEXT)
        except Exception:
            logger.exception("Failed to send fail-soft message in search_back")


@router.callback_query(F.data == "search_book")
async def on_search_book(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        logger.exception("Failed to answer callback query")

    try:
        text = (
            "Бронирование появится в следующих историях (Epic 4). "
            "Пока можешь вернуться к поиску."
        )
        await _send_callback_text(callback, text)
    except Exception:
        logger.exception("Failed to process search_book")
        try:
            await _send_callback_text(callback, _FAIL_SOFT_TEXT)
        except Exception:
            logger.exception("Failed to send fail-soft message in search_book")


@router.callback_query(F.data == "search_favorite")
async def on_search_favorite(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        logger.exception("Failed to answer callback query")

    try:
        user_id = _user_id_from_callback(callback)

        session = _SESSIONS.get(user_id)
        if session is None:
            await _send_callback_text(callback, "Поиск устарел. Напиши запрос ещё раз.")
            return

        apartment = session.results[session.index]
        assert session.favorites is not None
        session.favorites.add(apartment.id)
        await _send_callback_text(callback, "Сохранено ❤️")
    except Exception:
        logger.exception("Failed to process search_favorite")
        try:
            await _send_callback_text(callback, "Не получилось сохранить. Попробуй ещё раз.")
        except Exception:
            logger.exception("Failed to send fail-soft message in search_favorite")


@router.callback_query(F.data.in_(set(_STRUCTURED_FALLBACK_QUERIES)))
async def on_structured_fallback_choice(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        logger.exception("Failed to answer callback query")

    try:
        query = _STRUCTURED_FALLBACK_QUERIES.get(callback.data or "")
        if query is None:
            await _send_callback_text(callback, "Не нашёл шаблон. Напиши запрос текстом или отправь /start.")
            return
        await start_demo_search_from_callback(callback, query)
    except Exception:
        logger.exception("Failed to process structured fallback choice")
        try:
            await _send_callback_text(callback, _FAIL_SOFT_TEXT)
        except Exception:
            logger.exception("Failed to send fail-soft message in structured fallback choice")
