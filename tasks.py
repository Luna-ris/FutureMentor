from celery import Celery
from datetime import datetime, timedelta
from database import fetch_data, post_data
from aiogram import Bot
import os
import nest_asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Применение nest_asyncio для корректной работы асинхронных вызовов
nest_asyncio.apply()

# Инициализация Celery
app = Celery('tasks')
app.config_from_object('celeryconfig')

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

@app.task
async def send_motivational_message():
    logger.info("Отправка мотивационных сообщений...")
    goals = fetch_data("goals", {})
    for goal in goals:
        send_date = datetime.fromisoformat(goal['message_send_date'])
        if send_date.date() == datetime.now().date():
            user = fetch_data("users", {"id": goal['user_id']})
            await bot.send_message(user[0]['telegram_id'], f"💡 Your motivational message: {goal['motivational_message']}")

@app.task
async def send_study_capsule_reminder():
    logger.info("Отправка напоминаний о учебных капсулах...")
    capsules = fetch_data("study_capsules", {})
    for capsule in capsules:
        send_date = datetime.fromisoformat(capsule['send_date'])
        if send_date.date() == datetime.now().date():
            user = fetch_data("users", {"id": capsule['user_id']})
            await bot.send_message(user[0]['telegram_id'], f"📚 Time to study: {capsule['content']}")
            if capsule['test_questions']:
                await bot.send_message(user[0]['telegram_id'], "Take the test: " + "\n".join([q['question'] for q in capsule['test_questions']]))

@app.task
async def send_deadline_reminder():
    logger.info("Отправка напоминаний о дедлайнах...")
    goals = fetch_data("goals", {})
    for goal in goals:
        deadline = datetime.fromisoformat(goal['deadline'])
        reminder_date = deadline - timedelta(days=1)
        if reminder_date.date() == datetime.now().date():
            user = fetch_data("users", {"id": goal['user_id']})
            await bot.send_message(
                user[0]['telegram_id'],
                f"⏰ Reminder: Your goal '{goal['title']}' is due tomorrow! Deadline: {deadline.strftime('%d.%m.%Y')}"
            )

@app.task
async def send_calendar_reminder():
    logger.info("Отправка напоминаний о событиях в календаре...")
    events = fetch_data("calendar_events", {})
    for event in events:
        event_date = datetime.fromisoformat(event['event_date'])
        if event_date.date() == datetime.now().date():
            user = fetch_data("users", {"id": event['user_id']})
            await bot.send_message(user[0]['telegram_id'], f"🗓 Reminder: {event['event_name']} is today!")
