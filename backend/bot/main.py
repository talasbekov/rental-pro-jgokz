import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.core.config import settings
from bot.handlers import common, start
from bot.middlewares.auth import AuthMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.message.middleware(AuthMiddleware())
    dp.include_router(start.router)
    dp.include_router(common.router)
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
