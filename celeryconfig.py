from celery.schedules import crontab
import os

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = broker_url

beat_schedule = {
    'send-motivational-messages': {
        'task': 'tasks.send_motivational_message',
        'schedule': crontab(hour=0, minute=0),  # Каждый день в полночь
    },
    'send-study-capsule-reminders': {
        'task': 'tasks.send_study_capsule_reminder',
        'schedule': crontab(hour=0, minute=0),  # Каждый день в полночь
    },
    'send-deadline-reminders': {
        'task': 'tasks.send_deadline_reminder',
        'schedule': crontab(hour=0, minute=0),  # Каждый день в полночь
    },
}
