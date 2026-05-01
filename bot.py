import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import create_tables, seed_cases
from handlers import start, cases, games, inventory, top



# Включаем логи чтобы видеть ошибки
logging.basicConfig(level=logging.INFO)


async def main():
    # Создаём бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Создаём таблицы и заполняем начальными данными
    await create_tables()
    await seed_cases()

    # Подключаем обработчики команд
    dp.include_router(start.router)
    dp.include_router(cases.router)
    dp.include_router(games.router)
    dp.include_router(inventory.router)
    dp.include_router(top.router)
    print("✅ Бот запущен!")

    # Запускаем бота (polling = проверяет новые сообщения)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())