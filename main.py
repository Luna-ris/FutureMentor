import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()  # <- без аргументов

# Обработчик команды /start
@dp.message()
async def handle_message(message: Message):
    if message.text == "/start":
        await message.reply("Привет! Бот запущен.")

# Функции startup и shutdown
async def on_startup(dispatcher: Dispatcher):
    webhook_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

async def on_shutdown(dispatcher: Dispatcher):
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Бот остановлен")

# Корневой маршрут
async def root_handler(request):
    return web.Response(text="Бот работает!")

def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Настройка веб-приложения
    app = web.Application()
    app.router.add_get("/", root_handler)  # Добавляем корневой маршрут
    request_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    request_handler.register(app, path="/webhook")
    setup_application(app, dp)
    
    # Запуск приложения
    port = int(os.getenv("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
