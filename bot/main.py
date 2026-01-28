import asyncio
from aiogram import Bot, Dispatcher

from bot.config import API_KEY
from bot.handlers import router

async def main():
    bot = Bot(token=API_KEY)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
