import asyncio
import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler
)
import aiohttp

# Загрузка переменных окружения
load_dotenv()

# Получение конфигурации
TOKEN = os.getenv("BOT_TOKEN")
CORE_API = os.getenv("API_URL", "http://core:8080")

# Проверка обязательных переменных
if not TOKEN:
    print("Ошибка: BOT_TOKEN не найден!")
    exit(1)

# Состояния для ConversationHandler
SELECTING_TEST, ANSWERING_QUESTION, SHOWING_RESULTS = range(3)


# Хранение состояния пользователя
@dataclass
class UserSession:
    current_test_id: Optional[int] = None
    current_questions: List[Dict] = field(default_factory=list)
    current_question_index: int = 0
    user_answers: List[int] = field(default_factory=list)
    test_title: str = ""
    correct_answers: List[Optional[int]] = field(default_factory=list)


# Хранилище сессий пользователей
user_sessions: Dict[int, UserSession] = {}


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С CORE API
# ============================================
async def fetch_tests() -> List[Dict]:
    """Получить список тестов из Core API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{CORE_API}/api/tests", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                print(f"Core API вернул статус {response.status}")
                return []
    except Exception as e:
        print(f"Ошибка при запросе тестов: {e}")
        return []


async def fetch_test(test_id: int) -> Optional[Dict]:
    """Получить конкретный тест по ID"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{CORE_API}/api/tests/{test_id}", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                print(f"Core API вернул статус {response.status} для теста {test_id}")
                return None
    except Exception as e:
        print(f"Ошибка при запросе теста {test_id}: {e}")
        return None


async def submit_answers(user_id: int, test_id: int, answers: List[int]) -> Optional[Dict]:
    """Отправить ответы в Core API и получить результаты"""
    try:
        payload = {
            "user_id": user_id,
            "answers": answers
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{CORE_API}/api/tests/{test_id}/submit",
                    json=payload,
                    timeout=10
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Core API вернул статус {response.status} при отправке ответов")
                    return None
    except Exception as e:
        print(f"Ошибка при отправке ответов: {e}")
        return None


# ============================================
# ОСНОВНЫЕ ОБРАБОТЧИКИ КОМАНД
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для прохождения тестов и опросов.\n\n"
        "📋 Доступные команды:\n"
        "/tests - Посмотреть все тесты\n"
        "/help - Помощь и инструкции\n\n"
        "После прохождения теста вы увидите:\n"
        "✅ - правильный ответ\n"
        "❌ - неправильный ответ\n"
        "📊 - итоговый результат\n\n"
        "Используйте меню внизу для быстрого доступа к командам."
    )

    keyboard = [
        [InlineKeyboardButton("📚 Все тесты", callback_data="show_tests")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return ConversationHandler.END


async def show_tests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команда /tests"""
    await show_tests(update, context)
    return SELECTING_TEST


async def show_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список тестов с инлайн-кнопками"""
    user_id = update.effective_user.id

    if update.callback_query:
        await update.callback_query.answer()
        message = await update.callback_query.message.reply_text("🔄 Загружаю тесты...")
    else:
        message = await update.message.reply_text("🔄 Загружаю тесты...")

    tests = await fetch_tests()

    if not tests:
        await message.edit_text("❌ Не удалось загрузить тесты. Сервер Core не доступен.")
        return ConversationHandler.END

    keyboard = []
    for test in tests:
        test_id = test.get('id', 0)
        title = test.get('title', 'Без названия')
        questions_count = test.get('questions_count', 0)

        button_text = f"📝 {title} ({questions_count} вопросов)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_test_{test_id}")])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.edit_text(
        "📚 Выберите тест для прохождения:",
        reply_markup=reply_markup
    )

    return SELECTING_TEST


async def select_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора теста"""
    query = update.callback_query
    await query.answer()

    test_id = int(query.data.split("_")[2])
    user_id = query.from_user.id

    test_data = await fetch_test(test_id)

    if not test_data:
        await query.message.edit_text("❌ Не удалось загрузить тест. Попробуйте позже.")
        return ConversationHandler.END

    questions = test_data.get('questions', [])
    
    # Извлекаем правильные ответы из вопросов
    correct_answers = []
    for q in questions:
        # Предполагаем, что у вопроса есть поле 'correct_answer' или 'correct_option'
        correct_answer = q.get('correct_answer') or q.get('correct_option')
        if correct_answer is not None:
            correct_answers.append(correct_answer)
        else:
            correct_answers.append(None)
    
    user_sessions[user_id] = UserSession(
        current_test_id=test_id,
        current_questions=questions,
        test_title=test_data.get('title', 'Тест'),
        correct_answers=correct_answers
    )

    if not questions:
        await query.message.edit_text("⚠️ В этом тесте пока нет вопросов.")
        return ConversationHandler.END

    await show_question(query.message, user_id, 0)
    return ANSWERING_QUESTION


async def show_question(message, user_id: int, question_index: int):
    """Показать вопрос с вариантами ответов"""
    session = user_sessions.get(user_id)
    if not session or question_index >= len(session.current_questions):
        return

    question = session.current_questions[question_index]
    question_text = question.get('text', '')
    options = question.get('options', [])

    # Показываем предыдущий результат, если он есть
    result_text = ""
    if question_index < len(session.user_answers):
        user_answer = session.user_answers[question_index]
        if user_answer != -1:
            is_correct = (session.correct_answers[question_index] == user_answer 
                          if session.correct_answers[question_index] is not None else None)
            if is_correct is not None:
                result_text = "\n\n"
                if is_correct:
                    result_text += "✅ Вы ответили правильно!"
                else:
                    correct_idx = session.correct_answers[question_index]
                    if 0 <= correct_idx < len(options):
                        result_text += f"❌ Правильный ответ: {options[correct_idx]}"
                    else:
                        result_text += "❌ Вы ответили неправильно"

    # Создаем кнопки с вариантами ответов
    keyboard = []
    for i, option in enumerate(options):
        # Подсвечиваем уже выбранный ответ
        prefix = ""
        if question_index < len(session.user_answers):
            if session.user_answers[question_index] == i:
                prefix = "🔹 "
            elif (session.correct_answers[question_index] == i and 
                  session.correct_answers[question_index] is not None):
                prefix = "✅ "
        
        callback_data = f"answer_{question_index}_{i}"
        keyboard.append([InlineKeyboardButton(
            f"{prefix}{i + 1}. {option}",
            callback_data=callback_data
        )])

    # Кнопки навигации
    nav_buttons = []
    if question_index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{question_index - 1}"))

    if question_index < len(session.current_questions) - 1:
        nav_buttons.append(InlineKeyboardButton("Далее ➡️", callback_data=f"next_{question_index + 1}"))
    else:
        nav_buttons.append(InlineKeyboardButton("✅ Завершить тест", callback_data="finish_test"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("❌ Отменить тест", callback_data="cancel_test")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.edit_text(
        f"📝 Тест: {session.test_title}\n"
        f"Вопрос {question_index + 1}/{len(session.current_questions)}\n\n"
        f"{question_text}"
        f"{result_text}",
        reply_markup=reply_markup
    )


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора ответа"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = user_sessions.get(user_id)

    if not session:
        await query.message.edit_text("❌ Сессия устарела. Начните заново.")
        return ConversationHandler.END

    parts = query.data.split("_")
    question_index = int(parts[1])
    answer_index = int(parts[2])

    # Сохраняем ответ
    if len(session.user_answers) <= question_index:
        session.user_answers.extend([-1] * (question_index - len(session.user_answers) + 1))
    session.user_answers[question_index] = answer_index

    # Перерисовываем текущий вопрос с результатом
    await show_question(query.message, user_id, question_index)
    return ANSWERING_QUESTION


async def navigate_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Навигация между вопросами"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = user_sessions.get(user_id)

    if not session:
        await query.message.edit_text("❌ Сессия устарела. Начните заново.")
        return ConversationHandler.END

    if query.data.startswith("next_"):
        next_index = int(query.data.split("_")[1])
        await show_question(query.message, user_id, next_index)
    elif query.data.startswith("prev_"):
        prev_index = int(query.data.split("_")[1])
        await show_question(query.message, user_id, prev_index)

    return ANSWERING_QUESTION


async def finish_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение теста и отправка результатов"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = user_sessions.get(user_id)

    if not session:
        await query.message.edit_text("❌ Сессия устарела.")
        return ConversationHandler.END

    # Проверяем, все ли вопросы отвечены
    unanswered = [i + 1 for i, ans in enumerate(session.user_answers)
                  if ans == -1 or i >= len(session.user_answers)]

    if unanswered and query.data != "force_finish":
        keyboard = [
            [InlineKeyboardButton("✅ Да, отправить как есть", callback_data="force_finish")],
            [InlineKeyboardButton("⬅️ Вернуться к вопросам", callback_data=f"back_to_{unanswered[0] - 1}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(
            f"⚠️ Вы не ответили на вопросы: {', '.join(map(str, unanswered))}\n"
            "Хотите отправить тест как есть?",
            reply_markup=reply_markup
        )
        return ANSWERING_QUESTION

    # Все ответы есть - отправляем
    await submit_and_show_results(query.message, user_id, session)
    return SHOWING_RESULTS


async def calculate_local_results(session: UserSession) -> Dict:
    """Локальный расчет результатов на основе правильных ответов"""
    total = len(session.current_questions)
    answered = sum(1 for ans in session.user_answers if ans != -1 and ans is not None)
    correct = 0
    
    # Считаем правильные ответы
    for i in range(total):
        if i < len(session.user_answers) and session.user_answers[i] != -1:
            if (session.correct_answers[i] is not None and 
                session.user_answers[i] == session.correct_answers[i]):
                correct += 1
    
    if total > 0:
        score_percent = (correct / total) * 100
    else:
        score_percent = 0
    
    return {
        "total_questions": total,
        "answered": answered,
        "correct": correct,
        "incorrect": answered - correct,
        "skipped": total - answered,
        "score_percent": score_percent,
        "passed": score_percent >= 70  # Порог сдачи 70%
    }


async def show_detailed_results(message, user_id: int, session: UserSession, results: Dict):
    """Показать детальные результаты по каждому вопросу"""
    text = f"📊 РЕЗУЛЬТАТЫ ТЕСТА: {session.test_title}\n\n"
    
    # Общая статистика
    text += f"📈 Общая статистика:\n"
    text += f"• Всего вопросов: {results['total_questions']}\n"
    text += f"• Отвечено: {results['answered']}\n"
    text += f"• Правильных ответов: {results['correct']} ✅\n"
    text += f"• Неправильных ответов: {results['incorrect']} ❌\n"
    text += f"• Пропущено: {results['skipped']}\n"
    text += f"• Результат: {results['score_percent']:.1f}%\n\n"
    
    # Определяем, сдан ли тест
    if results['passed']:
        text += "🎉 ПОЗДРАВЛЯЕМ! ТЕСТ СДАН! 🎉\n\n"
    else:
        text += "😔 ТЕСТ НЕ СДАН. Попробуйте еще раз!\n\n"
    
    # Детали по каждому вопросу
    text += "📋 Ответы по вопросам:\n"
    for i, question in enumerate(session.current_questions):
        text += f"\n{i + 1}. {question.get('text', '')[:50]}..."
        
        if i >= len(session.user_answers) or session.user_answers[i] == -1:
            text += "\n   ❓ Вы не ответили на этот вопрос"
        else:
            user_answer_idx = session.user_answers[i]
            correct_answer_idx = session.correct_answers[i]
            
            if user_answer_idx is not None and correct_answer_idx is not None:
                if user_answer_idx == correct_answer_idx:
                    text += "\n   ✅ Правильно"
                else:
                    text += "\n   ❌ Неправильно"
                    
                    # Показываем правильный ответ
                    options = question.get('options', [])
                    if 0 <= correct_answer_idx < len(options):
                        text += f" (правильный ответ: {options[correct_answer_idx]})"
    
    # Кнопки для навигации
    keyboard = [
        [InlineKeyboardButton("🔍 Посмотреть вопросы", callback_data="review_questions")],
        [InlineKeyboardButton("📚 Выбрать другой тест", callback_data="show_tests")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="back_to_start")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Разбиваем длинное сообщение на части, если оно слишком длинное
    if len(text) > 4000:
        parts = []
        while len(text) > 4000:
            part = text[:4000]
            last_newline = part.rfind('\n')
            if last_newline > 0:
                parts.append(text[:last_newline])
                text = text[last_newline+1:]
            else:
                parts.append(text[:4000])
                text = text[4000:]
        parts.append(text)
        
        for i, part in enumerate(parts):
            if i == 0:
                await message.edit_text(part, reply_markup=reply_markup)
            else:
                await message.reply_text(part)
    else:
        await message.edit_text(text, reply_markup=reply_markup)


async def submit_and_show_results(message, user_id: int, session: UserSession):
    """Отправить результаты и показать итог"""
    # Отправляем в Core
    api_results = await submit_answers(user_id, session.current_test_id, session.user_answers)
    
    if api_results:
        # Используем результаты от API
        results = {
            "total_questions": api_results.get("total_questions", len(session.current_questions)),
            "answered": len([a for a in session.user_answers if a != -1]),
            "correct": api_results.get("correct_answers", 0),
            "incorrect": api_results.get("incorrect_answers", 0),
            "skipped": api_results.get("total_questions", len(session.current_questions)) - 
                       len([a for a in session.user_answers if a != -1]),
            "score_percent": api_results.get("score", 0),
            "passed": api_results.get("passed", False)
        }
    else:
        # Локальный расчет, если API не вернул результаты
        results = await calculate_local_results(session)
    
    # Показываем детальные результаты
    await show_detailed_results(message, user_id, session, results)


async def review_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр вопросов после завершения теста"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    session = user_sessions.get(user_id)
    
    if not session:
        await query.message.edit_text("❌ Сессия устарела. Начните заново.")
        return ConversationHandler.END
    
    # Возвращаемся к первому вопросу
    await show_question(query.message, user_id, 0)
    return ANSWERING_QUESTION


async def cancel_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]

    await query.message.edit_text(
        "❌ Тест отменен.\n\n"
        "Чтобы начать заново, используйте /tests"
    )

    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📖 Помощь по использованию бота:\n\n"
        "Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/tests - Показать все доступные тесты\n"
        "/help - Эта справка\n\n"
        "Как пройти тест:\n"
        "1. Нажмите /tests\n"
        "2. Выберите тест из списка\n"
        "3. Отвечайте на вопросы, выбирая варианты ответов\n"
        "4. Сразу видите, правильно ли ответили\n"
        "5. Завершите тест, когда ответите на все вопросы\n\n"
        "Обозначения:\n"
        "✅ - правильный ответ\n"
        "❌ - неправильный ответ\n"
        "🔹 - ваш выбранный ответ\n\n"
        "После теста вы увидите:\n"
        "• Подробные результаты по каждому вопросу\n"
        "• Общий процент правильных ответов\n"
        "• Информацию, сдан ли тест\n\n"
        "Если бот не отвечает:\n"
        "• Проверьте подключение к интернету\n"
        "• Убедитесь, что сервер Core работает\n"
        "• Попробуйте перезапустить бота командой /start"
    )

    if update.message:
        await update.message.reply_text(help_text)
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text)
        await update.callback_query.answer()

    return ConversationHandler.END


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к началу"""
    query = update.callback_query
    await query.answer()

    welcome_text = (
        "Главное меню:\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("📚 Все тесты", callback_data="show_tests")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(welcome_text, reply_markup=reply_markup)
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных команд"""
    await update.message.reply_text(
        "🤖 Я не понимаю эту команду.\n"
        "Используйте /help для списка команд."
    )


# ============================================
# НАСТРОЙКА И ЗАПУСК БОТА
# ============================================
def main():
    """Основная функция запуска бота"""
    try:
        # Создаем приложение
        app = ApplicationBuilder().token(TOKEN).build()

        # Настройка ConversationHandler для прохождения теста
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("tests", show_tests_command),
                CallbackQueryHandler(show_tests, pattern="^show_tests$")
            ],
            states={
                SELECTING_TEST: [
                    CallbackQueryHandler(select_test, pattern="^select_test_"),
                    CallbackQueryHandler(back_to_start, pattern="^back_to_start$"),
                    CallbackQueryHandler(help_command, pattern="^help$")
                ],
                ANSWERING_QUESTION: [
                    CallbackQueryHandler(handle_answer, pattern="^answer_"),
                    CallbackQueryHandler(navigate_question, pattern="^(next_|prev_)"),
                    CallbackQueryHandler(finish_test, pattern="^finish_test$"),
                    CallbackQueryHandler(finish_test, pattern="^force_finish$"),
                    CallbackQueryHandler(cancel_test, pattern="^cancel_test$"),
                    CallbackQueryHandler(lambda u, c: show_question(u.callback_query.message, u.effective_user.id,
                                                                    int(u.callback_query.data.split("_")[2])),
                                         pattern="^back_to_")
                ],
                SHOWING_RESULTS: [
                    CallbackQueryHandler(review_questions, pattern="^review_questions$"),
                    CallbackQueryHandler(show_tests, pattern="^show_tests$"),
                    CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
                ]
            },
            fallbacks=[
                CommandHandler("start", start),
                CommandHandler("help", help_command),
                CallbackQueryHandler(back_to_start, pattern="^back_to_start$")
            ]
        )

        # Регистрируем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(conv_handler)

        # Обработчик неизвестных команд
        app.add_handler(MessageHandler(filters.COMMAND, unknown))

        # Запускаем бота
        print("=" * 50)
        print("🤖 MassPoll Telegram Bot")
        print(f"📡 Core API: {CORE_API}")
        print("✅ Бот запущен и готов к работе...")
        print("=" * 50)

        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        exit(1)


if __name__ == '__main__':
    main()
