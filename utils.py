from datetime import datetime
from transformers import pipeline
import pandas as pd
from database import fetch_data
from localization import LOCALIZATION
import os
import warnings

# Игнорирование предупреждений от huggingface_hub
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")

# Кэширование моделей
os.environ["TRANSFORMERS_CACHE"] = "/app/.cache"

def get_message(key: str, user_id: int, **kwargs) -> str:
    user = fetch_data("users", {"telegram_id": user_id})
    language = user[0]['language'] if user else "ru"
    message = LOCALIZATION.get(language, {}).get(key, key)
    return message.format(**kwargs)

# AI-аналитика
def get_sentiment_analyzer():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", revision="714eb0f")

def analyze_motivational_message(message: str) -> str:
    sentiment_analyzer = get_sentiment_analyzer()
    result = sentiment_analyzer(message)[0]
    return result['label']

def analyze_progress(user_id: int) -> dict:
    goals = fetch_data("goals", {"user_id": user_id})
    if not goals:
        return {"progress": 0, "advice": "Пока нет целей."}
    df = pd.DataFrame(goals)
    avg_progress = df['progress'].mean()
    if avg_progress < 50:
        advice = "Ты отстаёшь от своих целей. Попробуй уделять хотя бы 30 минут в день!"
    else:
        advice = "Отличная работа! Продолжай в том же духе! 🚀"
    return {"progress": avg_progress, "advice": advice}
