from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Available commands:\n/start — Start the bot\n/help — Show this help")


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Unknown command. Use /help for available commands.")
