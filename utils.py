import json
from datetime import datetime, timedelta
import aiohttp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from transformers import pipeline
import pandas as pd
from database import fetch_data

# Локализация
def load_localization():
    with open("localization.py", "r", encoding="utf-8") as f:
        return json.load(f)

LOCALIZATION = load_localization()

def get_message(key: str, user_id: int, **kwargs) -> str:
    user = fetch_data("users", {"telegram_id": user_id})
    language = user[0]['language'] if user else "en"
    message = LOCALIZATION.get(language, {}).get(key, key)
    return message.format(**kwargs)

# Интеграция с Google Calendar
def add_to_google_calendar(user_id: int, goal_title: str, deadline: datetime):
    creds = Credentials.from_authorized_user_file("google_credentials.json")
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': goal_title,
        'start': {'dateTime': deadline.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': (deadline + timedelta(hours=1)).isoformat(), 'timeZone': 'UTC'},
    }
    service.events().insert(calendarId='primary', body=event).execute()

# Интеграция с Coursera API
async def get_recommended_courses(category: str) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.coursera.org/api/courses?category={category}") as response:
            data = await response.json()
            return [course['name'] for course in data['elements'][:3]]

# AI-аналитика
sentiment_analyzer = pipeline("sentiment-analysis")

def analyze_motivational_message(message: str) -> str:
    result = sentiment_analyzer(message)[0]
    return result['label']

def analyze_progress(user_id: int) -> dict:
    goals = fetch_data("goals", {"user_id": user_id})
    if not goals:
        return {"progress": 0, "advice": "No goals yet."}
    df = pd.DataFrame(goals)
    avg_progress = df['progress'].mean()
    if avg_progress < 50:
        advice = "You’re behind on your goals. Try dedicating 30 minutes a day!"
    else:
        advice = "Great job! Keep up the momentum! 🚀"
    return {"progress": avg_progress, "advice": advice}
