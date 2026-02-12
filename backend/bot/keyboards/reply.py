"""ReplyKeyboard builders for persistent menu navigation (Story 1.1.5)."""

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def _build_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Build main ReplyKeyboard with 4 persistent buttons.

    Returns:
        ReplyKeyboardMarkup with 4 buttons:
        - 🔍 Поиск квартир
        - 📋 Мои бронирования
        - ❤️ Избранное
        - ❓ Помощь

    Configuration:
        - is_persistent=True: keyboard always visible
        - resize_keyboard=True: optimal size for mobile
        - input_field_placeholder: hint for user input
    """
    builder = ReplyKeyboardBuilder()

    # Add 4 main buttons (2x2 layout)
    builder.button(text="🔍 Поиск квартир")
    builder.button(text="📋 Мои бронирования")
    builder.button(text="❤️ Избранное")
    builder.button(text="❓ Помощь")

    # Adjust layout: 2 buttons per row
    builder.adjust(2)

    return builder.as_markup(
        is_persistent=True,
        resize_keyboard=True,
        input_field_placeholder="Напиши запрос или выбери действие",
    )
