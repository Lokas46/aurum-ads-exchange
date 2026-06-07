import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routers import channels, transactions, users, webhooks, admin
from .routers.auth import router as auth_router
from .orders.router import router as orders_router
from .payments.router import router as payments_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_task = None
    if settings.bot_token:
        try:
            from aiogram import Bot, Dispatcher
            from aiogram.client.default import DefaultBotProperties
            from bot.handlers import start, channels as bot_channels, orders as bot_orders, wallet as bot_wallet, callbacks as bot_callbacks

            bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
            dp = Dispatcher()
            dp.include_router(bot_callbacks.router)
            dp.include_router(bot_channels.router)
            dp.include_router(bot_orders.router)
            dp.include_router(bot_wallet.router)
            dp.include_router(start.router)
            await bot.delete_webhook(drop_pending_updates=True)

            async def run_bot():
                try:
                    await dp.start_polling(bot)
                except Exception as e:
                    logger.error("Bot polling error: %s", e)

            bot_task = asyncio.create_task(run_bot())
            logger.info("Bot started in background")
        except Exception as e:
            logger.error("Failed to start bot: %s", e)
    yield
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Aurum Ads — Telegram Ad Exchange", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(orders_router, prefix="/api", tags=["orders"])
app.include_router(payments_router, prefix="/api", tags=["payments"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(auth_router, prefix="/api", tags=["auth"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    logger.error("Unhandled error: %s %s", type(exc).__name__, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/health")
async def health():
    return {"status": "ok"}