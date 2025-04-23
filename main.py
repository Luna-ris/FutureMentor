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
    logger.info("Сброс существующих вебхуков...")
    await bot.delete_webhook()
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
