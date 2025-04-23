import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from handlers import setup_handlers  # Импортируем функцию setup_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Инициализация бота, хранилища и диспетчера
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set!")
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создание клавиатуры с основными командами
def get_main_menu():
    buttons = [
        KeyboardButton(text="/create_goal"),
        KeyboardButton(text="/add_study_capsule"),
        KeyboardButton(text="/get_motivation"),
        KeyboardButton(text="/view_achievements"),
        KeyboardButton(text="/join_challenge"),
        KeyboardButton(text="/connect_habitica"),
        KeyboardButton(text="/set_mentor_style"),
        KeyboardButton(text="/leaderboard")
    ]
    keyboard_rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True
    )
    return keyboard

@dp.message(CommandStart())
async def handle_start(message: Message):
    logger.info(f"Received /start from user {message.from_user.id}")
    await message.reply(
        "Привет! Я FutureMentor, твой наставник для достижения целей и обучения. "
        "Выбери действие на клавиатуре или используй команды:\n"
        "🎯 /create_goal - Создать цель\n"
        "📚 /add_study_capsule - Добавить учебную капсулу\n"
        "💡 /get_motivation - Получить мотивацию\n"
        "🏆 /view_achievements - Посмотреть достижения\n"
        "🌍 /join_challenge - Присоединиться к челленджу\n"
        "🎮 /connect_habitica - Подключить Habitica\n"
        "🧑‍🏫 /set_mentor_style - Выбрать стиль ментора\n"
        "🏅 /leaderboard - Таблица лидеров",
        reply_markup=get_main_menu()
    )

@dp.message()
async def handle_unknown_message(message: Message):
    logger.info(f"Received message: {message.text} from user {message.from_user.id}")
    await message.reply(
        "Неизвестная команда или сообщение. Используй кнопки или введи одну из команд:\n"
        "/create_goal, /add_study_capsule, /get_motivation, /view_achievements, "
        "/join_challenge, /connect_habitica, /set_mentor_style, /leaderboard",
        reply_markup=get_main_menu()
    )

async def on_startup(dispatcher: Dispatcher):
    webhook_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

async def on_shutdown(dispatcher: Dispatcher):
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Бот остановлен")

async def root_handler(request):
    return web.Response(text="Бот работает!")

def main():
    # Инициализируем обработчики из handlers.py, передавая bot и storage
    logger.info("Registering handlers from handlers.py")
    setup_handlers(dp, bot, storage)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    request_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    request_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
