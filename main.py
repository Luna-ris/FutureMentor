import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start_command(message):
    await message.reply("Привет! Бот запущен.")

# Функции startup и shutdown
async def on_startup(_):
    webhook_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

async def on_shutdown(_):
    await bot.delete_webhook()
    await bot.get_session().close()
    logger.info("Бот остановлен")

def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Настройка веб-приложения
    app = web.Application()
    request_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    request_handler.register(app, path="/webhook")
    setup_application(app, dp)

    # Запуск приложения
    port = int(os.getenv("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
