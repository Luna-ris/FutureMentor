import json
from datetime import datetime
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
