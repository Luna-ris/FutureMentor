from datetime import datetime, timedelta
from transformers import pipeline
import pandas as pd
from database import fetch_data, post_data
from localization import LOCALIZATION
from crypto import encrypt_data, decrypt_data
import os
import warnings
import requests

# Игнорирование предупреждений от huggingface_hub
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")

# Кэширование моделей
os.environ["TRANSFORMERS_CACHE"] = "/app/.cache"

def get_message(key: str, user_id: int, **kwargs) -> str:
    user = fetch_data("users", {"telegram_id": user_id})
    language = user[0]['language'] if user else "ru"
    mentor_style = user[0].get('mentor_style', 'friendly')
    if key == "motivation_message" and mentor_style != "friendly":
        key = f"{mentor_style}_mentor_advice"
    message = LOCALIZATION.get(language, {}).get(key, key)
    return message.format(**kwargs)

def get_sentiment_analyzer():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", revision="714eb0f")

def analyze_motivational_message(message: str) -> str:
    sentiment_analyzer = get_sentiment_analyzer()
    result = sentiment_analyzer(message)[0]
    if result['label'] == "NEGATIVE":
        return f"{result['label']} (Сделай перерыв, ты выглядишь уставшим!)"
    return result['label']

def analyze_progress(user_id: int) -> dict:
    goals = fetch_data("goals", {"user_id": user_id})
    recent_activity = fetch_data("steps", {"user_id": user_id, "created_at": f">= {(datetime.now() - timedelta(days=14)).isoformat()}"})
    if not goals:
        return {"progress": 0, "advice": "Пока нет целей."}
    df = pd.DataFrame(goals)
    avg_progress = df['progress'].mean()
    missed_deadlines = len([g for g in goals if datetime.fromisoformat(g['deadline']) < datetime.now() and g['progress'] < 100])
    if missed_deadlines > 0:
        advice = f"Ты пропустил {missed_deadlines} дедлайнов. Давай продлим сроки или сосредоточимся на текущих задачах!"
    elif not recent_activity and avg_progress < 50:
        advice = "Ты неактивен последние 2 недели. Попробуй выделить 30 минут в день!"
    elif avg_progress < 50:
        advice = "Ты отстаёшь от своих целей. Попробуй уделять хотя бы 30 минут в день!"
    else:
        advice = "Отличная работа! Продолжай в том же духе! 🚀"
    return {"progress": avg_progress, "advice": advice}

def recommend_courses(goal: str) -> str:
    # Статический список курсов для примера (можно расширить или подключить RSS-ленту)
    courses_db = {
        "python": ["- Python for Everybody (Coursera): https://www.coursera.org/specializations/python", 
                   "- Learn Python (Udemy): https://www.udemy.com/course/python-for-beginners/"],
        "ielts": ["- IELTS Prep Course (Udemy): https://www.udemy.com/course/ielts-preparation/", 
                  "- IELTS Academic Test Prep (Coursera): https://www.coursera.org/learn/ielts-academic"],
        "developer": ["- Full Stack Web Development (Coursera): https://www.coursera.org/specializations/full-stack", 
                      "- The Web Developer Bootcamp (Udemy): https://www.udemy.com/course/the-web-developer-bootcamp/"]
    }
    goal = goal.lower()
    for key in courses_db:
        if key in goal:
            return "\n".join(courses_db[key])
    return "Курсы не найдены. Попробуй уточнить цель!"

def add_to_habitica(task_name: str, user_id: int):
    user = fetch_data("users", {"telegram_id": user_id})
    if not user[0].get("habitica_credentials"):
        return "Habitica не подключен. Используй /connect_habitica."
    try:
        credentials = decrypt_data(user[0]["habitica_credentials"], str(user_id)).split(":")
        user_id_habitica, api_token = credentials
        headers = {"x-api-user": user_id_habitica, "x-api-key": api_token}
        task_data = {"text": task_name, "type": "todo", "priority": 1.5}
        response = requests.post("https://habitica.com/api/v3/tasks/user", json=task_data, headers=headers)
        return "Задача добавлена в Habitica!" if response.status_code == 201 else "Ошибка добавления задачи в Habitica."
    except Exception as e:
        return f"Ошибка: {str(e)}"

def add_to_local_calendar(event_name: str, event_date: str, user_id: int):
    user = fetch_data("users", {"telegram_id": user_id})
    event_data = {
        "user_id": user[0]["id"],
        "event_name": event_name,
        "event_date": event_date,
        "created_at": datetime.now().isoformat()
    }
    post_data("calendar_events", event_data)
    return f"Событие '{event_name}' добавлено в ваш календарь на {event_date}."
