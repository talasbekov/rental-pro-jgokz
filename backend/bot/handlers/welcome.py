import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.handlers.search import start_demo_search_from_callback
from bot.keyboards.reply import _build_main_reply_keyboard

router = Router()

logger = logging.getLogger(__name__)

FAIL_SOFT_TEXT = (
    "Не получилось отправить подсказку. Попробуй ещё раз или напиши запрос текстом."
)


@router.callback_query(F.data == "try_search")
async def on_try_search(callback_query: CallbackQuery) -> None:
    try:
        await callback_query.answer()
    except Exception:
        logger.exception("Failed to answer callback query")

    try:
        await start_demo_search_from_callback(
            callback_query,
            query="квартира в центре на завтра до 20000₸",
        )
    except Exception:
        logger.exception("Failed to send try_search hint")
        try:
            if callback_query.message is not None:
                await callback_query.message.answer(
                    FAIL_SOFT_TEXT,
                    reply_markup=_build_main_reply_keyboard(),
                )
            else:
                bot = callback_query.bot
                if bot is not None and callback_query.from_user is not None:
                    await bot.send_message(
                        callback_query.from_user.id,
                        FAIL_SOFT_TEXT,
                        reply_markup=_build_main_reply_keyboard(),
                    )
        except Exception:
            logger.exception("Failed to send fail-soft message")
