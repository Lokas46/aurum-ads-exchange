import asyncio
import logging

import uvicorn
from app.config import settings

logging.basicConfig(level=logging.INFO)


async def run_bot():
    from bot.main import main as bot_main
    await bot_main()


async def run_api():
    config = uvicorn.Config(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(run_api(), run_bot())


if __name__ == "__main__":
    asyncio.run(main())
