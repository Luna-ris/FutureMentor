from celery import Celery
from datetime import datetime
from database import fetch_data
from aiogram import Bot
from config import BOT_TOKEN

app = Celery('tasks', broker='redis://localhost:6379/0')
bot = Bot(token=BOT_TOKEN)

@app.task
def send_motivational_message():
    goals = fetch_data("goals", {})
    for goal in goals:
        send_date = datetime.fromisoformat(goal['message_send_date'])
        if send_date.date() == datetime.now().date():
            user = fetch_data("users", {"id": goal['user_id']})
            bot.send_message(user[0]['telegram_id'], f"💡 Your motivational message: {goal['motivational_message']}")

@app.task
def send_study_capsule_reminder():
    capsules = fetch_data("study_capsules", {})
    for capsule in capsules:
        send_date = datetime.fromisoformat(capsule['send_date'])
        if send_date.date() == datetime.now().date():
            user = fetch_data("users", {"id": capsule['user_id']})
            bot.send_message(user[0]['telegram_id'], f"📚 Time to study: {capsule['content']}")
            if capsule['test_questions']:
                bot.send_message(user[0]['telegram_id'], "Take the test: " + "\n".join([q['question'] for q in capsule['test_questions']]))
