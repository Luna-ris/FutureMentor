from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
from database import post_data, fetch_data
from utils import get_message, analyze_motivational_message, analyze_progress, recommend_courses, add_to_habitica, add_to_local_calendar
from crypto import encrypt_data, decrypt_data
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для инициализации обработчиков
def setup_handlers(dp: Dispatcher, bot, storage):
    # Создание клавиатуры для возврата в главное меню
    def get_back_to_menu():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton(text="Вернуться в меню"))
        return keyboard

    # Создание цели
    class GoalStates(StatesGroup):
        TITLE = State()
        DEADLINE = State()
        MESSAGE = State()

    @dp.message(Command("create_goal"))
    async def create_goal_start(message: types.Message, state: FSMContext):
        await message.reply(get_message("create_goal_title", message.from_user.id), reply_markup=get_back_to_menu())
        await state.set_state(GoalStates.TITLE)

    @dp.message(state=GoalStates.TITLE)
    async def process_goal_title(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        await state.update_data(title=message.text)
        await message.reply(get_message("create_goal_deadline", message.from_user.id), reply_markup=get_back_to_menu())
        await state.set_state(GoalStates.DEADLINE)

    @dp.message(state=GoalStates.DEADLINE)
    async def process_goal_deadline(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        try:
            deadline = datetime.strptime(message.text, "%d.%m.%Y")
            await state.update_data(deadline=deadline)
            await message.reply(get_message("create_goal_message", message.from_user.id), reply_markup=get_back_to_menu())
            await state.set_state(GoalStates.MESSAGE)
        except ValueError:
            await message.reply("Неверный формат даты! Используйте дд.мм.гггг.", reply_markup=get_back_to_menu())

    @dp.message(state=GoalStates.MESSAGE)
    async def process_goal_message(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        user_data = await state.get_data()
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        if not user:
            user_data_db = {
                "telegram_id": message.from_user.id,
                "username": message.from_user.username or f"user_{message.from_user.id}",
                "language": "ru",
                "timezone": "UTC"
            }
            post_data("users", user_data_db)
            user = fetch_data("users", {"telegram_id": message.from_user.id})
        goal_data = {
            "user_id": user[0]['id'],
            "title": user_data['title'],
            "deadline": user_data['deadline'].isoformat(),
            "progress": 0.0,
            "category": "general",
            "motivational_message": encrypt_data(message.text, str(message.from_user.id)),
            "message_send_date": (user_data['deadline'] - timedelta(days=30)).isoformat(),
            "created_at": datetime.now().isoformat()
        }
        post_data("goals", goal_data)
        mood = analyze_motivational_message(message.text)
        await message.reply(
            f"✅ Цель '{user_data['title']}' создана! Настроение сообщения: {mood}\n"
            f"Напомню о дедлайне за день: {user_data['deadline'].strftime('%d.%m.%Y')}",
            reply_markup=get_main_menu()
        )
        await add_to_habitica(f"Цель: {user_data['title']}", message.from_user.id)
        await add_to_local_calendar(user_data['title'], user_data['deadline'].isoformat(), message.from_user.id)
        post_data("points", {"user_id": user[0]['id'], "points": 10, "earned_at": datetime.now().isoformat()})
        await state.finish()

    # Добавление шага к цели
    class StepStates(StatesGroup):
        GOAL_ID = State()
        TITLE = State()

    @dp.message(Command("add_step"))
    async def add_step_start(message: types.Message, state: FSMContext):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        goals = fetch_data("goals", {"user_id": user[0]['id']})
        if not goals:
            await message.reply("У вас нет целей. Создайте одну с /create_goal.", reply_markup=get_main_menu())
            return
        goal_list = "\n".join([f"{g['id']}. {g['title']}" for g in goals])
        await message.reply(f"Выберите ID цели:\n{goal_list}", reply_markup=get_back_to_menu())
        await state.set_state(StepStates.GOAL_ID)

    @dp.message(state=StepStates.GOAL_ID)
    async def process_step_goal_id(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        try:
            goal_id = int(message.text)
            goal = fetch_data("goals", {"id": goal_id})[0]
            await state.update_data(goal_id=goal_id)
            await message.reply(get_message("add_step", message.from_user.id, goal=goal['title']), reply_markup=get_back_to_menu())
            await state.set_state(StepStates.TITLE)
        except (ValueError, IndexError):
            await message.reply("Неверный ID цели.", reply_markup=get_back_to_menu())

    @dp.message(state=StepStates.TITLE)
    async def process_step_title(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        user_data = await state.get_data()
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        step_data = {
            "goal_id": user_data['goal_id'],
            "user_id": user[0]['id'],
            "title": message.text,
            "completed": False,
            "created_at": datetime.now().isoformat()
        }
        post_data("steps", step_data)
        await message.reply(f"Шаг '{message.text}' добавлен к цели!", reply_markup=get_main_menu())
        await add_to_habitica(f"Шаг: {message.text}", message.from_user.id)
        post_data("points", {"user_id": user[0]['id'], "points": 5, "earned_at": datetime.now().isoformat()})
        steps = fetch_data("steps", {"goal_id": user_data['goal_id']})
        if len(steps) >= 5:
            post_data("achievements", {"user_id": user[0]['id'], "name": "Пять шагов вперед", "awarded_at": datetime.now().isoformat()})
            await message.reply(get_message("achievement_earned", message.from_user.id, achievement="Пять шагов вперед"), reply_markup=get_main_menu())
        await state.finish()

    # Просмотр дедлайнов
    @dp.message(Command("view_deadlines"))
    async def view_deadlines(message: types.Message):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        goals = fetch_data("goals", {"user_id": user[0]['id']})
        if not goals:
            await message.reply("У вас нет целей с дедлайнами. Создайте одну с /create_goal.", reply_markup=get_main_menu())
            return
        deadline_list = "\n".join([
            f"- {g['title']}: {datetime.fromisoformat(g['deadline']).strftime('%d.%m.%Y')}"
            for g in goals
        ])
        await message.reply(f"Ваши дедлайны:\n{deadline_list}", reply_markup=get_main_menu())

    # Создание учебных капсул
    class StudyCapsuleStates(StatesGroup):
        CONTENT = State()
        SEND_DATE = State()

    @dp.message(Command("add_study_capsule"))
    async def add_study_capsule_start(message: types.Message, state: FSMContext):
        await message.reply(get_message("study_capsule_content", message.from_user.id), reply_markup=get_back_to_menu())
        await state.set_state(StudyCapsuleStates.CONTENT)

    @dp.message(state=StudyCapsuleStates.CONTENT)
    async def process_study_capsule_content(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        content = message.text or message.caption or "Медиа-контент"
        if message.photo or message.video:
            content += f" (Медиа: {message.photo[-1].file_id if message.photo else message.video.file_id})"
        await state.update_data(content=content)
        await message.reply(get_message("study_capsule_send_date", message.from_user.id), reply_markup=get_back_to_menu())
        await state.set_state(StudyCapsuleStates.SEND_DATE)

    @dp.message(state=StudyCapsuleStates.SEND_DATE)
    async def process_study_capsule_send_date(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        try:
            send_date = datetime.strptime(message.text, "%d.%m.%Y")
            user_data = await state.get_data()
            user = fetch_data("users", {"telegram_id": message.from_user.id})
            capsule_data = {
                "user_id": user[0]['id'],
                "content": encrypt_data(user_data['content'], str(message.from_user.id)),
                "send_date": send_date.isoformat(),
                "test_questions": [],
                "created_at": datetime.now().isoformat()
            }
            post_data("study_capsules", capsule_data)
            await message.reply("✅ Учебная капсула создана! Напомню позже.", reply_markup=get_main_menu())
            post_data("points", {"user_id": user[0]['id'], "points": 5, "earned_at": datetime.now().isoformat()})
            await state.finish()
        except ValueError:
            await message.reply("Неверный формат даты! Используйте дд.мм.гггг.", reply_markup=get_back_to_menu())

    # Добавление тестов
    class TestStates(StatesGroup):
        CAPSULE_ID = State()
        QUESTION = State()
        ANSWER = State()

    @dp.message(Command("add_test"))
    async def add_test_start(message: types.Message, state: FSMContext):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        capsules = fetch_data("study_capsules", {"user_id": user[0]['id']})
        if not capsules:
            await message.reply("У вас нет учебных капсул. Создайте одну с /add_study_capsule.", reply_markup=get_main_menu())
            return
        capsule_list = "\n".join([f"{c['id']}. {decrypt_data(c['content'], str(message.from_user.id))[:30]}..." for c in capsules])
        await message.reply(f"Выберите ID капсулы:\n{capsule_list}", reply_markup=get_back_to_menu())
        await state.set_state(TestStates.CAPSULE_ID)

    @dp.message(state=TestStates.CAPSULE_ID)
    async def process_test_capsule_id(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        try:
            capsule_id = int(message.text)
            await state.update_data(capsule_id=capsule_id)
            await message.reply("Введите вопрос теста:", reply_markup=get_back_to_menu())
            await state.set_state(TestStates.QUESTION)
        except ValueError:
            await message.reply("Введите корректный ID капсулы.", reply_markup=get_back_to_menu())

    @dp.message(state=TestStates.QUESTION)
    async def process_test_question(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        await state.update_data(question=message.text)
        await message.reply("Введите правильный ответ:", reply_markup=get_back_to_menu())
        await state.set_state(TestStates.ANSWER)

    @dp.message(state=TestStates.ANSWER)
    async def process_test_answer(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        user_data = await state.get_data()
        capsule = fetch_data("study_capsules", {"id": user_data['capsule_id']})[0]
        test_questions = capsule.get('test_questions', [])
        test_questions.append({"question": user_data['question'], "answer": message.text})
        post_data("study_capsules", {"id": user_data['capsule_id'], "test_questions": test_questions}, update=True)
        await message.reply(f"Вопрос теста добавлен к капсуле ID {user_data['capsule_id']}!", reply_markup=get_main_menu())
        await state.finish()

    # Прохождение теста
    class TakeTestStates(StatesGroup):
        CAPSULE_ID = State()
        ANSWER = State()

    @dp.message(Command("take_test"))
    async def take_test_start(message: types.Message, state: FSMContext):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        capsules = fetch_data("study_capsules", {"user_id": user[0]['id']})
        if not capsules:
            await message.reply("У вас нет учебных капсул с тестами.", reply_markup=get_main_menu())
            return
        capsule_list = "\n".join([f"{c['id']}. {decrypt_data(c['content'], str(message.from_user.id))[:30]}..." for c in capsules if c['test_questions']])
        await message.reply(f"Выберите ID капсулы для теста:\n{capsule_list}", reply_markup=get_back_to_menu())
        await state.set_state(TakeTestStates.CAPSULE_ID)

    @dp.message(state=TakeTestStates.CAPSULE_ID)
    async def process_test_capsule_id(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        try:
            capsule_id = int(message.text)
            capsule = fetch_data("study_capsules", {"id": capsule_id})[0]
            if not capsule['test_questions']:
                await message.reply("У этой капсулы нет тестов.", reply_markup=get_main_menu())
                await state.finish()
                return
            await state.update_data(capsule_id=capsule_id, questions=capsule['test_questions'], current_question=0, correct=0)
            await message.reply(capsule['test_questions'][0]['question'], reply_markup=get_back_to_menu())
            await state.set_state(TakeTestStates.ANSWER)
        except (ValueError, IndexError):
            await message.reply("Неверный ID капсулы.", reply_markup=get_back_to_menu())

    @dp.message(state=TakeTestStates.ANSWER)
    async def process_test_answer(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        user_data = await state.get_data()
        questions = user_data['questions']
        current = user_data['current_question']
        correct = user_data['correct']
        if message.text.lower() == questions[current]['answer'].lower():
            correct += 1
        current += 1
        if current < len(questions):
            await state.update_data(current_question=current, correct=correct)
            await message.reply(questions[current]['question'], reply_markup=get_back_to_menu())
        else:
            user = fetch_data("users", {"telegram_id": message.from_user.id})
            test_result = {
                "user_id": user[0]['id'],
                "capsule_id": user_data['capsule_id'],
                "correct_answers": correct,
                "total_questions": len(questions),
                "created_at": datetime.now().isoformat()
            }
            post_data("test_results", test_result)
            await message.reply(get_message("test_result", message.from_user.id, correct=correct, total=len(questions)), reply_markup=get_main_menu())
            post_data("points", {"user_id": user[0]['id'], "points": correct * 2, "earned_at": datetime.now().isoformat()})
            await state.finish()

    # Мотивация
    @dp.message(Command("get_motivation"))
    async def get_motivation(message: types.Message):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        analysis = analyze_progress(user[0]['id'])
        goals = fetch_data("goals", {"user_id": user[0]['id']})
        if goals:
            goal = goals[0]
            await message.reply(
                get_message("motivation_message", message.from_user.id, goal=goal['title'], progress=analysis['progress'], advice=analysis['advice']),
                reply_markup=get_main_menu()
            )
        else:
            await message.reply("Сначала создайте цель с /create_goal!", reply_markup=get_main_menu())

    # Рекомендации курсов
    @dp.message(Command("recommend_course"))
    async def recommend_course(message: types.Message):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        goals = fetch_data("goals", {"user_id": user[0]['id']})
        if not goals:
            await message.reply("У вас нет целей. Создайте одну с /create_goal.", reply_markup=get_main_menu())
            return
        courses = recommend_courses(goals[0]['title'])
        await message.reply(
            get_message("recommend_course", message.from_user.id, goal=goals[0]['title'], courses=courses),
            reply_markup=get_main_menu()
        )

    # Подключение Habitica
    class HabiticaStates(StatesGroup):
        CREDENTIALS = State()

    @dp.message(Command("connect_habitica"))
    async def connect_habitica_start(message: types.Message, state: FSMContext):
        await message.reply(get_message("connect_habitica", message.from_user.id), reply_markup=get_back_to_menu())
        await state.set_state(HabiticaStates.CREDENTIALS)

    @dp.message(state=HabiticaStates.CREDENTIALS)
    async def process_habitica_credentials(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        if ":" not in message.text:
            await message.reply("Неверный формат. Используйте: user_id:api_token", reply_markup=get_back_to_menu())
            return
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        encrypted_credentials = encrypt_data(message.text, str(message.from_user.id))
        post_data("users", {"id": user[0]['id'], "habitica_credentials": encrypted_credentials}, update=True)
        await message.reply(get_message("habitica_connected", message.from_user.id), reply_markup=get_main_menu())
        await state.finish()

    # Установка стиля ментора
    @dp.message(Command("set_mentor_style"))
    async def set_mentor_style(message: types.Message):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        style = message.text.split()[-1].lower() if len(message.text.split()) > 1 else None
        if style not in ["strict", "friendly", "humorous"]:
            await message.reply(
                get_message("set_mentor_style", message.from_user.id) + "\nПример: /set_mentor_style strict",
                reply_markup=get_main_menu()
            )
            return
        post_data("users", {"id": user[0]['id'], "mentor_style": style}, update=True)
        await message.reply(f"Стиль ментора установлен: {style}", reply_markup=get_main_menu())

    # Создание групповой цели
    class GroupGoalStates(StatesGroup):
        TITLE = State()
        DEADLINE = State()

    @dp.message(Command("create_group_goal"))
    async def create_group_goal_start(message: types.Message, state: FSMContext):
        await message.reply(get_message("create_goal_title", message.from_user.id), reply_markup=get_back_to_menu())
        await state.set_state(GroupGoalStates.TITLE)

    @dp.message(state=GroupGoalStates.TITLE)
    async def process_group_goal_title(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        await state.update_data(title=message.text)
        await message.reply(get_message("create_goal_deadline", message.from_user.id), reply_markup=get_back_to_menu())
        await state.set_state(GroupGoalStates.DEADLINE)

    @dp.message(state=GroupGoalStates.DEADLINE)
    async def process_group_goal_deadline(message: types.Message, state: FSMContext):
        if message.text == "Вернуться в меню":
            await message.reply("Возвращаемся в меню!", reply_markup=get_main_menu())
            await state.finish()
            return
        try:
            deadline = datetime.strptime(message.text, "%d.%m.%Y")
            user_data = await state.get_data()
            user = fetch_data("users", {"telegram_id": message.from_user.id})
            group_goal_data = {
                "title": user_data['title'],
                "deadline": deadline.isoformat(),
                "participants": [user[0]['id']],
                "created_at": datetime.now().isoformat()
            }
            post_data("group_goals", group_goal_data)
            group_goal = fetch_data("group_goals", {"title": user_data['title']})[-1]
            await message.reply(
                get_message("group_goal_created", message.from_user.id, title=user_data['title'], goal_id=group_goal['id']),
                reply_markup=get_main_menu()
            )
            post_data("points", {"user_id": user[0]['id'], "points": 15, "earned_at": datetime.now().isoformat()})
            await state.finish()
        except ValueError:
            await message.reply("Неверный формат даты! Используйте дд.мм.гггг.", reply_markup=get_back_to_menu())

    # Приглашение в групповую цель
    @dp.message(Command("invite_to_goal"))
    async def invite_to_goal(message: types.Message):
        try:
            goal_id = int(message.text.split()[-1])
            user = fetch_data("users", {"telegram_id": message.from_user.id})
            group_goal = fetch_data("group_goals", {"id": goal_id})[0]
            participants = group_goal['participants']
            if user[0]['id'] in participants:
                await message.reply("Вы уже участвуете в этой цели.", reply_markup=get_main_menu())
                return
            participants.append(user[0]['id'])
            post_data("group_goals", {"id": goal_id, "participants": participants}, update=True)
            await message.reply(f"Вы присоединились к групповой цели '{group_goal['title']}'!", reply_markup=get_main_menu())
            post_data("points", {"user_id": user[0]['id'], "points": 10, "earned_at": datetime.now().isoformat()})
        except (ValueError, IndexError):
            await message.reply("Укажите корректный ID цели: /invite_to_goal <goal_id>", reply_markup=get_main_menu())

    # Социальные функции
    @dp.message(Command("motivation_feed"))
    async def show_motivation_feed(message: types.Message):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        friends = fetch_data("friends", {"user_id": user[0]['id']})
        activities = []
        for friend in friends:
            friend_goals = fetch_data("goals", {"user_id": friend['friend_id'], "progress": 100})
            friend_steps = fetch_data("steps", {"user_id": friend['friend_id'], "completed": True})
            friend_user = fetch_data("users", {"id": friend['friend_id']})
            for goal in friend_goals:
                activities.append(f"@{friend_user[0]['username']} достиг цели: {goal['title']} 🎉")
            for step in friend_steps:
                activities.append(f"@{friend_user[0]['username']} завершил шаг: {step['title']} 🚀")
        await message.reply("\n".join(activities) or "Пока нет активности.", reply_markup=get_main_menu())

    # Присоединение к челленджу
    @dp.message(Command("join_challenge"))
    async def join_challenge(message: types.Message):
        challenges = fetch_data("challenges", {})
        if not challenges:
            await message.reply("Пока нет активных челленджей.", reply_markup=get_main_menu())
            return
        challenge = challenges[0]
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        participants = challenge.get('participants', [])
        if user[0]['id'] in participants:
            await message.reply("Вы уже участвуете в этом челлендже.", reply_markup=get_main_menu())
            return
        participants.append(user[0]['id'])
        post_data("challenges", {"id": challenge['id'], "participants": participants}, update=True)
        await message.reply(get_message("challenge_joined", message.from_user.id, challenge=challenge['title']), reply_markup=get_main_menu())
        post_data("points", {"user_id": user[0]['id'], "points": 10, "earned_at": datetime.now().isoformat()})

    # Геймификация
    @dp.message(Command("view_achievements"))
    async def view_achievements(message: types.Message):
        user = fetch_data("users", {"telegram_id": message.from_user.id})
        achievements = fetch_data("achievements", {"user_id": user[0]['id']})
        if achievements:
            achievement_list = "\n".join([f"- {a['name']} (Получено: {a['awarded_at']})" for a in achievements])
            await message.reply(f"Ваши достижения:\n{achievement_list}", reply_markup=get_main_menu())
        else:
            await message.reply("Пока нет достижений. Продолжайте работать над целями!", reply_markup=get_main_menu())

    @dp.message(Command("leaderboard"))
    async def leaderboard(message: types.Message):
        points = fetch_data("points", {})
        user_points = {}
        for point in points:
            user_points[point['user_id']] = user_points.get(point['user_id'], 0) + point['points']
        sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
        leaderboard = []
        for user_id, total_points in sorted_users:
            user = fetch_data("users", {"id": user_id})[0]
            leaderboard.append(f"@{user['username']}: {total_points} баллов")
        await message.reply(get_message("leaderboard", message.from_user.id, leaderboard="\n".join(leaderboard)), reply_markup=get_main_menu())

    # Функция для главного меню (используется в других местах)
    def get_main_menu():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [
            KeyboardButton(text="/create_goal"),
            KeyboardButton(text="/add_study_capsule"),
            KeyboardButton(text="/get_motivation"),
            KeyboardButton(text="/view_achievements"),
            KeyboardButton(text="/join_challenge"),
            KeyboardButton(text="/connect_habitica"),
            KeyboardButton(text="/set_mentor_style"),
            KeyboardButton(text="/leaderboard")
        ]
        keyboard.add(*buttons)
        return keyboard
