import asyncio
import os
import time
from aiogram import Bot, Dispatcher

from bot.config import API_KEY
from bot.handlers import router


async def cleanup_old_files():
    """Удаляет файлы из папки downloads старше 7 дней"""
    while True:
        try:
            if os.path.exists("downloads"):
                now = time.time()
                for filename in os.listdir("downloads"):
                    filepath = os.path.join("downloads", filename)
                    if os.path.isfile(filepath):
                        # Проверяем возраст файла (7 дней = 7 * 24 * 3600 секунд)
                        if now - os.path.getmtime(filepath) > 7 * 24 * 3600:
                            os.remove(filepath)
                            print(f"Удален старый файл: {filename}")
        except Exception as e:
            print(f"Ошибка при очистке файлов: {e}")
        
        # Запускаем очистку раз в день
        await asyncio.sleep(86400)


async def main():
    bot = Bot(token=API_KEY)
    dp = Dispatcher()
    dp.include_router(router)

    # Запускаем фоновую задачу очистки
    asyncio.create_task(cleanup_old_files())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
