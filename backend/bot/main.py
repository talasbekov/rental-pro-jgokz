import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.core.config import settings
from bot.handlers import common, search, start, welcome
from bot.keyboards.reply import _build_main_reply_keyboard
from bot.middlewares.auth import AuthMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FAIL_SOFT_ERROR_TEXT = (
    "Кажется, что-то пошло не так. Попробуй ещё раз или отправь /start."
)


async def on_error(event: ErrorEvent, bot: Bot) -> None:
    logger.error(
        "Unhandled exception while processing update",
        exc_info=event.exception,
    )

    update = event.update
    reply_markup = _build_main_reply_keyboard()
    try:
        if update.callback_query is not None and update.callback_query.from_user is not None:
            try:
                await update.callback_query.answer()
            except Exception:
                logger.exception("Failed to answer callback query in error handler")
            await bot.send_message(
                update.callback_query.from_user.id,
                FAIL_SOFT_ERROR_TEXT,
                reply_markup=reply_markup,
            )
            return

        if update.message is not None:
            await bot.send_message(
                update.message.chat.id,
                FAIL_SOFT_ERROR_TEXT,
                reply_markup=reply_markup,
            )
            return

        if update.edited_message is not None:
            await bot.send_message(
                update.edited_message.chat.id,
                FAIL_SOFT_ERROR_TEXT,
                reply_markup=reply_markup,
            )
            return

        if update.channel_post is not None:
            await bot.send_message(
                update.channel_post.chat.id,
                FAIL_SOFT_ERROR_TEXT,
                reply_markup=reply_markup,
            )
            return

        if update.edited_channel_post is not None:
            await bot.send_message(
                update.edited_channel_post.chat.id,
                FAIL_SOFT_ERROR_TEXT,
                reply_markup=reply_markup,
            )
    except Exception:
        logger.exception("Failed to send fail-soft error message")


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.update.middleware(AuthMiddleware())
    dp.errors.register(on_error)
    dp.include_router(start.router)
    dp.include_router(welcome.router)
    dp.include_router(common.router)
    dp.include_router(search.router)
    return dp


async def on_startup(bot: Bot) -> None:
    webhook_url = settings.TELEGRAM_WEBHOOK_URL
    logger.info("Setting webhook to %s", webhook_url)
    await bot.set_webhook(
        webhook_url,
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
    )


def main() -> None:
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dispatcher()
    dp.startup.register(on_startup)

    app = web.Application()
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
    )
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=settings.BOT_PORT)


if __name__ == "__main__":
    main()
