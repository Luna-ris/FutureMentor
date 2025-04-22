from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from datetime import datetime, timedelta
from database import post_data, fetch_data
from utils import get_message, analyze_motivational_message, analyze_progress

router = Router()

# Создание цели
class GoalStates(StatesGroup):
    TITLE = State()
    DEADLINE = State()
    MESSAGE = State()

@router.message(Command("create_goal"))
async def create_goal_start(message: Message, state: FSMContext):
    await message.reply(get_message("create_goal_title", message.from_user.id))
    await state.set_state(GoalStates.TITLE)

@router.message(GoalStates.TITLE)
async def process_goal_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.reply(get_message("create_goal_deadline", message.from_user.id))
    await state.set_state(GoalStates.DEADLINE)

@router.message(GoalStates.DEADLINE)
async def process_goal_deadline(message: Message, state: FSMContext):
    try:
        deadline = datetime.strptime(message.text, "%d.%m.%Y")
        await state.update_data(deadline=deadline)
        await message.reply(get_message("create_goal_message", message.from_user.id))
        await state.set_state(GoalStates.MESSAGE)
    except ValueError:
        await message.reply("Invalid date format! Use dd.mm.yyyy.")

@router.message(GoalStates.MESSAGE)
async def process_goal_message(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user = fetch_data("users", {"telegram_id": message.from_user.id})
    if not user:
        user_data = {
            "telegram_id": message.from_user.id,
            "username": message.from_user.username,
            "language": "en",
            "timezone": "UTC"
        }
        post_data("users", user_data)
        user = fetch_data("users", {"telegram_id": message.from_user.id})
    goal_data = {
        "user_id": user[0]['id'],
        "title": user_data['title'],
        "deadline": user_data['deadline'].isoformat(),
        "progress": 0.0,
        "category": "general",
        "motivational_message": message.text,
        "message_send_date": (user_data['deadline'] - timedelta(days=90)).isoformat(),
        "created_at": datetime.now().isoformat()
    }
    post_data("goals", goal_data)
    mood = analyze_motivational_message(message.text)
    await message.reply(f"✅ Goal '{user_data['title']}' created! Mood of your message: {mood}\nI'll remind you about the deadline one day before: {user_data['deadline'].strftime('%d.%m.%Y')}")
    await state.clear()

# Просмотр дедлайнов
@router.message(Command("view_deadlines"))
async def view_deadlines(message: Message):
    user = fetch_data("users", {"telegram_id": message.from_user.id})
    goals = fetch_data("goals", {"user_id": user[0]['id']})
    if not goals:
        await message.reply("You have no goals with deadlines yet. Create one with /create_goal.")
        return
    deadline_list = "\n".join([
        f"- {g['title']}: {datetime.fromisoformat(g['deadline']).strftime('%d.%m.%Y')}"
        for g in goals
    ])
    await message.reply(f"Your deadlines:\n{deadline_list}")

# Создание учебных капсул
class StudyCapsuleStates(StatesGroup):
    CONTENT = State()
    SEND_DATE = State()

@router.message(Command("add_study_capsule"))
async def add_study_capsule_start(message: Message, state: FSMContext):
    await message.reply(get_message("study_capsule_content", message.from_user.id))
    await state.set_state(StudyCapsuleStates.CONTENT)

@router.message(StudyCapsuleStates.CONTENT)
async def process_study_capsule_content(message: Message, state: FSMContext):
    await state.update_data(content=message.text)
    await message.reply(get_message("study_capsule_send_date", message.from_user.id))
    await state.set_state(StudyCapsuleStates.SEND_DATE)

@router.message(StudyCapsuleStates.SEND_DATE)
async def process_study_capsule_send_date(message: Message, state: FSMContext):
    try:
        send_date = datetime.strptime(message.text, "%d.%m.%Y")
        user_data = await state.get_data()
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        capsule_data = {
            "user_id": user[0]['id'],
            "content": user_data['content'],
            "send_date": send_date.isoformat(),
            "test_questions": [],
            "created_at": datetime.now().isoformat()
        }
        post_data("study_capsules", capsule_data)
        await message.reply("✅ Study capsule created! I’ll remind you later.")
        await state.clear()
    except ValueError:
        await message.reply("Invalid date format! Use dd.mm.yyyy.")

# Добавление тестов
class TestStates(StatesGroup):
    CAPSULE_ID = State()
    QUESTION = State()
    ANSWER = State()

@router.message(Command("add_test"))
async def add_test_start(message: Message, state: FSMContext):
    user = fetch_data("users", {"telegram_id": message.from_user.id})
    capsules = fetch_data("study_capsules", {"user_id": user[0]['id']})
    if not capsules:
        await message.reply("You have no study capsules yet. Create one with /add_study_capsule.")
        return
    capsule_list = "\n".join([f"{c['id']}. {c['content'][:30]}..." for c in capsules])
    await message.reply(f"Choose a capsule by ID:\n{capsule_list}")
    await state.set_state(TestStates.CAPSULE_ID)

@router.message(TestStates.CAPSULE_ID)
async def process_test_capsule_id(message: Message, state: FSMContext):
    try:
        capsule_id = int(message.text)
        await state.update_data(capsule_id=capsule_id)
        await message.reply("Enter the test question:")
        await state.set_state(TestStates.QUESTION)
    except ValueError:
        await message.reply("Please enter a valid capsule ID.")

@router.message(TestStates.QUESTION)
async def process_test_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.reply("Enter the correct answer:")
    await state.set_state(TestStates.ANSWER)

@router.message(TestStates.ANSWER)
async def process_test_answer(message: Message, state: FSMContext):
    user_data = await state.get_data()
    capsule = fetch_data("study_capsules", {"id": user_data['capsule_id']})[0]
    test_questions = capsule.get('test_questions', [])
    test_questions.append({"question": user_data['question'], "answer": message.text})
    post_data("study_capsules", {"id": user_data['capsule_id'], "test_questions": test_questions}, update=True)
    await message.reply(f"Test question added to capsule ID {user_data['capsule_id']}!")
    await state.clear()

# Мотивация
@router.message(Command("get_motivation"))
async def get_motivation(message: Message):
    user = fetch_data("users", {"telegram_id": message.from_user.id})
    analysis = analyze_progress(user[0]['id'])
    goals = fetch_data("goals", {"user_id": user[0]['id']})
    if goals:
        goal = goals[0]
        await message.reply(get_message("motivation_message", message.from_user.id, goal=goal['title'], progress=analysis['progress'], advice=analysis['advice']))
    else:
        await message.reply("Set a goal first with /create_goal!")

# Социальные функции
@router.message(Command("motivation_feed"))
async def show_motivation_feed(message: Message):
    user = fetch_data("users", {"telegram_id": message.from_user.id})
    friends = fetch_data("friends", {"user_id": user[0]['id']})
    activities = []
    for friend in friends:
        friend_goals = fetch_data("goals", {"user_id": friend['friend_id'], "progress": 100})
        friend_user = fetch_data("users", {"id": friend['friend_id']})
        for goal in friend_goals:
            activities.append(f"@{friend_user[0]['username']} achieved goal: {goal['title']} 🎉")
    await message.reply("\n".join(activities) or "No activity yet.")

# Геймификация
@router.message(Command("view_achievements"))
async def view_achievements(message: Message):
    user = fetch_data("users", {"telegram_id": message.from_user.id})
    achievements = fetch_data("achievements", {"user_id": user[0]['id']})
    if achievements:
        achievement_list = "\n".join([f"- {a['name']} (Awarded: {a['awarded_at']})" for a in achievements])
        await message.reply(f"Your achievements:\n{achievement_list}")
    else:
        await message.reply("No achievements yet. Keep working on your goals!")
