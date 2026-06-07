import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.config import settings
from .handlers import start, channels, orders, wallet, callbacks

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(callbacks.router)
    dp.include_router(channels.router)
    dp.include_router(orders.router)
    dp.include_router(wallet.router)

    # Delete webhook before polling to avoid conflicts
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(1)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
