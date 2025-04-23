from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def init_db():
    logger.info("Инициализация базы данных...")
    tables = [
        {
            "name": "users",
            "schema": {
                "telegram_id": "integer",
                "username": "varchar",
                "language": "varchar",
                "timezone": "varchar",
                "mentor_style": "varchar",
                "habitica_credentials": "varchar"
            }
        },
        {
            "name": "goals",
            "schema": {
                "id": "serial primary key",
                "user_id": "integer",
                "title": "varchar",
                "description": "varchar",
                "deadline": "timestamp",
                "progress": "float",
                "category": "varchar",
                "motivational_message": "varchar",
                "message_send_date": "timestamp",
                "created_at": "timestamp"
            }
        },
        {
            "name": "steps",
            "schema": {
                "id": "serial primary key",
                "goal_id": "integer",
                "user_id": "integer",
                "title": "varchar",
                "completed": "boolean",
                "created_at": "timestamp"
            }
        },
        {
            "name": "study_capsules",
            "schema": {
                "id": "serial primary key",
                "user_id": "integer",
                "content": "varchar",
                "send_date": "timestamp",
                "test_questions": "jsonb",
                "created_at": "timestamp"
            }
        },
        {
            "name": "achievements",
            "schema": {
                "id": "serial primary key",
                "user_id": "integer",
                "name": "varchar",
                "awarded_at": "timestamp"
            }
        },
        {
            "name": "points",
            "schema": {
                "id": "serial primary key",
                "user_id": "integer",
                "points": "integer",
                "earned_at": "timestamp"
            }
        },
        {
            "name": "friends",
            "schema": {
                "id": "serial primary key",
                "user_id": "integer",
                "friend_id": "integer",
                "created_at": "timestamp"
            }
        },
        {
            "name": "challenges",
            "schema": {
                "id": "serial primary key",
                "title": "varchar",
                "description": "varchar",
                "start_date": "timestamp",
                "end_date": "timestamp",
                "participants": "jsonb",
                "created_at": "timestamp"
            }
        },
        {
            "name": "group_goals",
            "schema": {
                "id": "serial primary key",
                "title": "varchar",
                "deadline": "timestamp",
                "participants": "jsonb",
                "created_at": "timestamp"
            }
        },
        {
            "name": "calendar_events",
            "schema": {
                "id": "serial primary key",
                "user_id": "integer",
                "event_name": "varchar",
                "event_date": "timestamp",
                "created_at": "timestamp"
            }
        },
        {
            "name": "test_results",
            "schema": {
                "id": "serial primary key",
                "user_id": "integer",
                "capsule_id": "integer",
                "correct_answers": "integer",
                "total_questions": "integer",
                "created_at": "timestamp"
            }
        }
    ]
    
    for table in tables:
        try:
            supabase.table(table["name"]).select("*").limit(1).execute()
            logger.info(f"Таблица {table['name']} уже существует")
        except Exception as e:
            logger.warning(f"Таблица {table['name']} не существует, создание...")
            logger.error(f"Создание таблицы {table['name']} не реализовано в коде. Создайте таблицу в Supabase Dashboard.")

def fetch_data(table: str, filters: dict):
    query = supabase.table(table).select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute().data
    
def post_data(table: str, data: dict, update: bool = False):
    if update:
        supabase.table(table).update(data).eq("id", data['id']).execute()
    else:
        supabase.table(table).insert(data).execute()
