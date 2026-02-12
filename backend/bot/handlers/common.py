from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.handlers.search import start_demo_search_from_message
from bot.keyboards.reply import _build_main_reply_keyboard

router = Router()
logger = logging.getLogger(__name__)

_FAIL_SOFT_TEXT = "Кажется, что-то пошло не так. Попробуй ещё раз или отправь /start."

_HELP_TEXT = (
    "❓ <b>Помощь</b>\n\n"
    "🔍 <b>Поиск квартир</b> — нажми кнопку «🔍 Поиск квартир» в меню или просто напиши запрос.\n"
    "Пример: «квартира в центре на завтра до 20000₸»\n\n"
    "📋 <b>Мои бронирования</b> — появится в Epic 4.\n"
    "❤️ <b>Избранное</b> — появится в Epic 3.\n\n"
    "Если что-то зависло — отправь /start."
)

_MAIN_MENU_TEXT = "Главное меню всегда доступно внизу. Выбери действие или напиши запрос."


@router.callback_query(F.data == "main_menu")
async def on_main_menu(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        logger.exception("Failed to answer callback query")

    try:
        if callback.message is not None:
            await callback.message.answer(
                _MAIN_MENU_TEXT,
                reply_markup=_build_main_reply_keyboard(),
            )
        elif callback.bot is not None and callback.from_user is not None:
            await callback.bot.send_message(
                callback.from_user.id,
                _MAIN_MENU_TEXT,
                reply_markup=_build_main_reply_keyboard(),
            )
    except Exception:
        logger.exception("Failed to send main menu message")
        try:
            if callback.message is not None:
                await callback.message.answer(
                    _FAIL_SOFT_TEXT,
                    reply_markup=_build_main_reply_keyboard(),
                )
            elif callback.bot is not None and callback.from_user is not None:
                await callback.bot.send_message(
                    callback.from_user.id,
                    _FAIL_SOFT_TEXT,
                    reply_markup=_build_main_reply_keyboard(),
                )
        except Exception:
            logger.exception("Failed to send fail-soft message in on_main_menu")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        _HELP_TEXT,
        parse_mode="HTML",
        reply_markup=_build_main_reply_keyboard(),
    )


@router.message(F.text == "🔍 Поиск квартир")
async def on_search_button(message: Message) -> None:
    try:
        await message.answer(
            "Напиши, что ищешь: район, даты, бюджет",
            reply_markup=_build_main_reply_keyboard(),
        )
        await start_demo_search_from_message(
            message,
            query="квартира в центре на завтра до 20000₸",
        )
    except Exception:
        logger.exception("Failed to handle search button")
        try:
            await message.answer(
                _FAIL_SOFT_TEXT,
                reply_markup=_build_main_reply_keyboard(),
            )
        except Exception:
            logger.exception("Failed to send fail-soft message in on_search_button")


@router.message(F.text == "📋 Мои бронирования")
async def on_bookings_button(message: Message) -> None:
    try:
        await message.answer(
            "Раздел 'Мои бронирования' появится в Epic 4. Пока можешь попробовать поиск.",
            reply_markup=_build_main_reply_keyboard(),
        )
    except Exception:
        logger.exception("Failed to handle bookings button")
        try:
            await message.answer(
                _FAIL_SOFT_TEXT,
                reply_markup=_build_main_reply_keyboard(),
            )
        except Exception:
            logger.exception("Failed to send fail-soft message in on_bookings_button")


@router.message(F.text == "❤️ Избранное")
async def on_favorites_button(message: Message) -> None:
    try:
        await message.answer(
            "Раздел 'Избранное' появится в Epic 3. Пока можешь попробовать поиск.",
            reply_markup=_build_main_reply_keyboard(),
        )
    except Exception:
        logger.exception("Failed to handle favorites button")
        try:
            await message.answer(
                _FAIL_SOFT_TEXT,
                reply_markup=_build_main_reply_keyboard(),
            )
        except Exception:
            logger.exception("Failed to send fail-soft message in on_favorites_button")


@router.message(F.text == "❓ Помощь")
async def on_help_button(message: Message) -> None:
    try:
        await cmd_help(message)
    except Exception:
        logger.exception("Failed to handle help button")
        try:
            await message.answer(
                _FAIL_SOFT_TEXT,
                reply_markup=_build_main_reply_keyboard(),
            )
        except Exception:
            logger.exception("Failed to send fail-soft message in on_help_button")


@router.message(F.text.startswith("/"))
async def fallback(message: Message) -> None:
    await message.answer(
        "Не понял команду. Нажми /start или используй /help.",
        reply_markup=_build_main_reply_keyboard(),
    )
