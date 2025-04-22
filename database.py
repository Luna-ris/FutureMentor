from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def init_db():
    await supabase.table("users").create({
        "telegram_id": "integer",
        "username": "varchar",
        "language": "varchar",
        "timezone": "varchar"
    }).execute()
    
    await supabase.table("goals").create({
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
    }).execute()
    
    await supabase.table("steps").create({
        "id": "serial primary key",
        "goal_id": "integer",
        "title": "varchar",
        "completed": "boolean",
        "created_at": "timestamp"
    }).execute()
    
    await supabase.table("study_capsules").create({
        "id": "serial primary key",
        "user_id": "integer",
        "content": "varchar",
        "send_date": "timestamp",
        "test_questions": "jsonb",
        "created_at": "timestamp"
    }).execute()
    
    await supabase.table("achievements").create({
        "id": "serial primary key",
        "user_id": "integer",
        "name": "varchar",
        "awarded_at": "timestamp"
    }).execute()
    
    await supabase.table("points").create({
        "id": "serial primary key",
        "user_id": "integer",
        "points": "integer",
        "earned_at": "timestamp"
    }).execute()
    
    await supabase.table("friends").create({
        "id": "serial primary key",
        "user_id": "integer",
        "friend_id": "integer",
        "created_at": "timestamp"
    }).execute()
    
    await supabase.table("challenges").create({
        "id": "serial primary key",
        "title": "varchar",
        "description": "varchar",
        "start_date": "timestamp",
        "end_date": "timestamp",
        "participants": "jsonb",
        "created_at": "timestamp"
    }).execute()

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
