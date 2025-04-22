import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import dp
from database import init_db

bot = Bot(token=BOT_TOKEN)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
