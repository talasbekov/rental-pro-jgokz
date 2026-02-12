from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.reply import _build_main_reply_keyboard

router = Router()

WELCOME_TEXT = (
    "Привет! Помогу найти квартиру посуточно.\n"
    "Нажми кнопку ниже или напиши запрос (например: “квартира в центре на завтра до 15000₸”)."
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    # Show welcome message with ReplyKeyboard (persistent menu)
    await message.answer(
        WELCOME_TEXT,
        reply_markup=_build_main_reply_keyboard(),
    )

    # Optionally show inline buttons for quick actions
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Попробовать поиск", callback_data="try_search")
    keyboard.button(text="📋 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)  # One button per row

    await message.answer(
        "Выбери действие:",
        reply_markup=keyboard.as_markup(),
    )
