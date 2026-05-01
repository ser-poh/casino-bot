import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import create_tables, seed_cases
from handlers import start, cases, games, inventory, top
from api import app as fastapi_app

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    await create_tables()
    await seed_cases()

    dp.include_router(start.router)
    dp.include_router(cases.router)
    dp.include_router(games.router)
    dp.include_router(inventory.router)
    dp.include_router(top.router)

    print("✅ Бот запущен!")

    # Запускаем FastAPI и бота одновременно
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(
        dp.start_polling(bot),
        server.serve()
    )

if __name__ == "__main__":
    asyncio.run(main())