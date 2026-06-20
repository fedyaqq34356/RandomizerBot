import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from logger import setup_logger
from handlers import start, accounts, giveaway, participants, draw, broadcast

logger = setup_logger()


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(start.router)
    dp.include_router(accounts.router)
    dp.include_router(giveaway.router)
    dp.include_router(participants.router)
    dp.include_router(draw.router)
    dp.include_router(broadcast.router)
    
    logger.info("Бот запущено")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
