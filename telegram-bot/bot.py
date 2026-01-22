cat > bot.py << 'EOF'
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")

# Простые тестовые данные
TESTS = {
    1: {
        "id": 1,
        "title": "Тест по программированию",
        "questions": [
            {
                "id": 1,
                "text": "Что такое переменная?",
                "answers": ["Ячейка памяти", "Функция", "Класс", "Метод"],
                "correct": 0
            },
            {
                "id": 2,
                "text": "Что такое функция?",
                "answers": ["Переменная", "Блок кода", "Класс", "Объект"],
                "correct": 1
            }
        ]
    },
    2: {
        "id": 2,
        "title": "Тест по математике",
        "questions": [
            {
                "id": 1,
                "text": "Сколько будет 2+2?",
                "answers": ["3", "4", "5", "6"],
                "correct": 1
            },
            {
                "id": 2,
                "text": "Сколько будет 3*3?",
                "answers": ["6", "9", "12", "15"],
                "correct": 1
            }
        ]
    }
}

# Хранение сессий
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для прохождения тестов.\n\n"
        "📋 Команды:\n"
        "/tests - Показать тесты\n"
        "/math - Тест по математике\n"
        "/prog - Тест по программированию\n"
        "/help - Помощь"
    )

async def show_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список тестов с кнопками"""
    keyboard = [
        [InlineKeyboardButton("🧮 Тест по математике", callback_data="test_2")],
        [InlineKeyboardButton("💻 Тест по программированию", callback_data="test_1")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Выберите тест:", reply_markup=reply_markup)

async def math_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сразу начать тест по математике"""
    await start_test(update, context, test_id=2)

async def prog_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сразу начать тест по программированию"""
    await start_test(update, context, test_id=1)

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE, test_id):
    """Начать тест"""
    test = TESTS.get(test_id)
    
    if not test:
        await update.message.reply_text("❌ Тест не найден")
        return
    
    user_id = update.effective_user.id
    
    # Сохраняем сессию
    user_sessions[user_id] = {
        "test_id": test_id,
        "test_title": test["title"],
        "questions": test["questions"],
        "current_question": 0,
        "answers": []
    }
    
    await show_question(update, user_id, 0)

async def show_question(update: Update, user_id, question_index):
    """Показать вопрос с кнопками"""
    session = user_sessions.get(user_id)
    if not session or question_index >= len(session["questions"]):
        return
    
    question = session["questions"][question_index]
    
    # СОЗДАЕМ КНОПКИ С ВАРИАНТАМИ ОТВЕТОВ
    keyboard = []
    answers = question["answers"]
    
    for i, answer in enumerate(answers):
        keyboard.append([InlineKeyboardButton(
            f"{i+1}. {answer}",
            callback_data=f"answer_{question_index}_{i}"
        )])
    
    # Кнопки навигации
    nav_buttons = []
    if question_index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{question_index-1}"))
    
    if question_index < len(session["questions"]) - 1:
        nav_buttons.append(InlineKeyboardButton("Далее ➡️", callback_data=f"next_{question_index+1}"))
    else:
        nav_buttons.append(InlineKeyboardButton("✅ Завершить тест", callback_data="finish"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📝 Тест: {session['test_title']}\n"
        f"Вопрос {question_index + 1}/{len(session['questions'])}\n\n"
        f"{question['text']}",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех callback'ов"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    session = user_sessions.get(user_id)
    
    if not session:
        await query.message.edit_text("❌ Сессия устарела")
        return
    
    data = query.data
    
    if data.startswith("test_"):
        # Выбор теста из меню
        test_id = int(data.split("_")[1])
        test = TESTS.get(test_id)
        
        if not test:
            await query.message.edit_text("❌ Тест не найден")
            return
        
        user_sessions[user_id] = {
            "test_id": test_id,
            "test_title": test["title"],
            "questions": test["questions"],
            "current_question": 0,
            "answers": []
        }
        
        await show_question_callback(query, user_id, 0)
    
    elif data.startswith("answer_"):
        # Ответ на вопрос
        parts = data.split("_")
        question_index = int(parts[1])
        answer_index = int(parts[2])
        
        # Сохраняем ответ
        if len(session["answers"]) <= question_index:
            session["answers"].extend([-1] * (question_index - len(session["answers"]) + 1))
        session["answers"][question_index] = answer_index
        
        # Показываем результат
        question = session["questions"][question_index]
        correct = question["correct"]
        
        if answer_index == correct:
            result = "✅ Правильно!"
        else:
            result = f"❌ Неправильно. Правильный ответ: {question['answers'][correct]}"
        
        # Обновляем кнопки
        keyboard = []
        for i, answer in enumerate(question["answers"]):
            prefix = ""
            if i == answer_index:
                prefix = "🔹 "
            elif i == correct:
                prefix = "✅ "
            
            keyboard.append([InlineKeyboardButton(
                f"{prefix}{i+1}. {answer}",
                callback_data=f"answer_{question_index}_{i}"
           
