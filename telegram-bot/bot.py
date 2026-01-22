import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")

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
    keyboard = [
        [InlineKeyboardButton("🧮 Тест по математике", callback_data="test_2")],
        [InlineKeyboardButton("💻 Тест по программированию", callback_data="test_1")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Выберите тест:", reply_markup=reply_markup)

async def math_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_test(update, context, test_id=2)

async def prog_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_test(update, context, test_id=1)

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE, test_id):
    test = TESTS.get(test_id)
    
    if not test:
        await update.message.reply_text("❌ Тест не найден")
        return
    
    user_id = update.effective_user.id
    
    user_sessions[user_id] = {
        "test_id": test_id,
        "test_title": test["title"],
        "questions": test["questions"],
        "current_question": 0,
        "answers": []
    }
    
    await show_question(update, user_id, 0)

async def show_question(update: Update, user_id, question_index):
    session = user_sessions.get(user_id)
    if not session or question_index >= len(session["questions"]):
        return
    
    question = session["questions"][question_index]
    
    keyboard = []
    answers = question["answers"]
    
    for i, answer in enumerate(answers):
        keyboard.append([InlineKeyboardButton(
            f"{i+1}. {answer}",
            callback_data=f"answer_{question_index}_{i}"
        )])
    
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

async def show_question_callback(query, user_id, question_index):
    session = user_sessions.get(user_id)
    if not session or question_index >= len(session["questions"]):
        return
    
    question = session["questions"][question_index]
    
    keyboard = []
    for i, answer in enumerate(question["answers"]):
        keyboard.append([InlineKeyboardButton(
            f"{i+1}. {answer}",
            callback_data=f"answer_{question_index}_{i}"
        )])
    
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
    
    await query.message.edit_text(
        f"📝 Тест: {session['test_title']}\n"
        f"Вопрос {question_index + 1}/{len(session['questions'])}\n\n"
        f"{question['text']}",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    session = user_sessions.get(user_id)
    
    if not session:
        await query.message.edit_text("❌ Сессия устарела")
        return
    
    data = query.data
    
    if data.startswith("test_"):
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
        parts = data.split("_")
        question_index = int(parts[1])
        answer_index = int(parts[2])
        
        if len(session["answers"]) <= question_index:
            session["answers"].extend([-1] * (question_index - len(session["answers"]) + 1))
        session["answers"][question_index] = answer_index
        
        question = session["questions"][question_index]
        correct = question["correct"]
        
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
            )])
        
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
        
        if answer_index == correct:
            result_text = "✅ Правильно!"
        else:
            result_text = f"❌ Неправильно. Правильный ответ: {question['answers'][correct]}"
        
        await query.message.edit_text(
            f"📝 Тест: {session['test_title']}\n"
            f"Вопрос {question_index + 1}/{len(session['questions'])}\n\n"
            f"{question['text']}\n\n{result_text}",
            reply_markup=reply_markup
        )
    
    elif data.startswith("next_"):
        next_index = int(data.split("_")[1])
        await show_question_callback(query, user_id, next_index)
    
    elif data.startswith("prev_"):
        prev_index = int(data.split("_")[1])
        await show_question_callback(query, user_id, prev_index)
    
    elif data == "finish":
        await finish_test(query, user_id)

async def finish_test(query, user_id):
    session = user_sessions.get(user_id)
    if not session:
        await query.message.edit_text("❌ Сессия устарела")
        return
    
    correct = 0
    total = len(session["questions"])
    
    for i, (question, answer) in enumerate(zip(session["questions"], session["answers"])):
        if answer == question["correct"]:
            correct += 1
    
    score = (correct * 100) // total if total > 0 else 0
    
    result_text = f"""
📊 Результаты теста:
{'-' * 30}
📝 Тест: {session['test_title']}
✅ Правильных: {correct}/{total}
📈 Процент: {score}%
🎯 Статус: {'Сдано' if score >= 70 else 'Не сдано'}
    """
    
    keyboard = [
        [InlineKeyboardButton("📋 Выбрать другой тест", callback_data="menu")],
        [InlineKeyboardButton("🔄 Пройти заново", callback_data=f"test_{session['test_id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(result_text, reply_markup=reply_markup)
    
    if user_id in user_sessions:
        del user_sessions[user_id]

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Помощь по боту:\n\n"
        "/start - Начать работу с ботом\n"
        "/tests - Показать список тестов\n"
        "/math - Тест по математике\n"
        "/prog - Тест по программированию\n"
        "/help - Эта справка"
    )

def main():
    if not TOKEN:
        logger.error("Токен бота не установлен!")
        logger.error("Установите переменную TELEGRAM_BOT_TOKEN")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tests", show_tests))
    application.add_handler(CommandHandler("math", math_test))
    application.add_handler(CommandHandler("prog", prog_test))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
