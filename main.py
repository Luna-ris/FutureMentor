import asyncio
from config import BOT_TOKEN
from handlers import dp
from database import init_db
from aiogram import Bot
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)

async def main():
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("Сброс существующих сессий getUpdates...")
    try:
        await bot.get_updates(offset=-1)  # Сбрасываем все существующие сессии
    except Exception as e:
        logger.warning(f"Ошибка при сбросе сессии getUpdates: {e}")
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
