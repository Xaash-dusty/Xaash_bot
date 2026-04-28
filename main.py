import telebot
from telebot import types
from pycbrf import ExchangeRates
from datetime import datetime
import os
import time
import random
from flask import Flask
from threading import Thread

# --- 0. KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Status: Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
keep_alive()

# --- 1. НАСТРОЙКИ И ДАННЫЕ ---
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))
ADMIN_ID = 7106093310 

quiz_data = [
    {"question": "Какая планета самая большая?", "options": ["Марс", "Юпитер", "Сатурн"], "correct": "Юпитер"},
    {"question": "Сколько полосок на флаге США?", "options": ["10", "13", "15"], "correct": "13"},
    {"question": "На каком языке программирования обычно пишут простых ТГ ботов?", "options": ["Java", "Python", "C++"], "correct": "Python"},
    {"question": "2+2*2?", "options": ["8", "4", "6"], "correct": "6"}
]

# ПЕРСОНАЛЬНЫЕ СЛОВАРИ
user_tasks = {}    
user_scores = {}   
user_modes = {}    
user_actions = {}  

# --- 2. ПОМОЩНИКИ ---
def get_rates():
    """Запрашивает свежие курсы валют у ЦБ РФ."""
    try:
        rates = ExchangeRates(datetime.now())
        return rates['USD'].value, rates['EUR'].value
    except Exception as e:
        print(f"Ошибка банка: {e}")
        return None, None

# --- 3. КОМАНДЫ ---
@bot.message_handler(commands=['tasks'])
def fast_tasks(message):
    """Быстрый переход к задачам через /tasks."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Список дел", "➕ Добавить", "❌ Удалить")
    markup.add("🗑 Очистить всё", "🏠 В меню")
    bot.send_message(message.chat.id, "📝 Меню задач открыто!", reply_markup=markup)

@bot.message_handler(commands=['quiz'])
def fast_quiz(message):
    """Быстрый переход к викторине через /quiz."""
    user_scores[message.from_user.id] = 0
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 Задачи", "💰 Валюта")
    markup.row("🎮 Викторина")
    bot.send_message(message.chat.id, f"🕹 Начинаем викторину!Всего вопросов {len(quiz_data)}. Удачи!")
    show_quiz_question(message, 0)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Справка по командам."""
    help_text = (
        "❓ **СПРАВКА ПО БОТУ**\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
        
        "📋 **ЗАДАЧИ**\n"
        "• «➕ Добавить» — создать новую запись.\n"
        "• «❌ Удалить» — убрать задачу.\n"
        "• «🗑️ Очистить» — полное удаление списка.\n"
        "• Быстрый доступ: `/tasks`\n\n"
        
        "📈 **ВАЛЮТА**\n"
        "• Актуальные курсы USD и EUR.\n"
        "• Удобный конвертер из рублей.\n\n"
        
        f"🎮 **ВИКТОРИНА**\n"
        f"• Тест на {len(quiz_data)} вопроса. Проверь себя!\n"
        "• Быстрый старт: `/quiz`\n\n"
        
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "📍 **БЫСТРЫЕ КОМАНДЫ:**\n"
        "• `/start` или `/menu` — главное меню.\n"
        "• `/help` — вызвать эту справку.\n\n"
        "✨ *Используй кнопки внизу для удобной навигации!*"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['start', 'menu'])
def main_menu(message):
    '''ГЛАВНОЕ МЕНЮ'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 Задачи", "💰 Валюта")
    markup.row("🎮 Викторина")
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я твой многофункциональный помощник.\n"
        "Выбери нужный раздел в меню ниже: 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# --- 4. ОБРАБОТЧИК ТЕКСТА ---
@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    '''ОБРАБОТЧИК ТЕКСТА'''
    uid = message.from_user.id
    
    # ЛОГИРОВАНИЕ АДМИНУ
    if uid != ADMIN_ID:
        first_name = message.from_user.first_name if message.from_user.first_name else "нет имени"
        username = message.from_user.username if message.from_user.username else "нет ника"
        userID = message.from_user.id if message.from_user.id else "нет ID"
        # 1. Сначала уведомляем админа (вас)
        report = f"👤 От: {first_name} (@{username})\n" \
                 f"🆔 ID: {userID}\n" \
                 f"💬 Текст: {message.text}"
        bot.send_message(ADMIN_ID, report)

    # Инициализация данных пользователя, если их нет
    if uid not in user_tasks: user_tasks[uid] = []
    if uid not in user_modes: user_modes[uid] = 'usd'
    if uid not in user_actions: user_actions[uid] = None

    # НАВИГАЦИЯ
    if message.text == "📝 Задачи":
        fast_tasks(message)
    elif message.text == "💰 Валюта":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🇺🇸 Курс USD", "🇪🇺 Курс EUR", "🔄 Конвертер", "🏠 В меню")
        bot.send_message(message.chat.id, "📍 Раздел ВАЛЮТА\nВыбери курс или нажми «Конвертер»", reply_markup=markup)
    elif message.text == "🎮 Викторина":
        fast_quiz(message)
    elif message.text == "🏠 В меню":
        user_actions[uid] = None
        main_menu(message)

    # ЛОГИКА ВАЛЮТ
    elif message.text in ["🇺🇸 Курс USD", "🇪🇺 Курс EUR"]:
        usd, eur = get_rates()
        val = usd if "USD" in message.text else eur
        bot.send_message(message.chat.id, f"📈 Курс: {val} руб." if val else "⚠️ Ошибка банка")

    elif message.text == "🔄 Конвертер":
        markup = types.InlineKeyboardMarkup()
        mode = user_modes[uid]
        label = "➡️ На EUR" if mode == 'usd' else "➡️ На USD"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"mode_{'eur' if mode=='usd' else 'usd'}"))
        bot.send_message(message.chat.id, f"💵 Сейчас режим: {mode.upper()}\nВведите сумму в рублях цифрами:", reply_markup=markup)

    # ЛОГИКА ЗАДАЧ
    elif message.text == "📋 Список дел":
        tasks = user_tasks[uid]
        res = "🗒 Твои задачи:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]) if tasks else "Список пуст."
        bot.send_message(message.chat.id, f"{res}\n\n💡 Нажми «❌ Удалить», чтобы стереть задачу.")
    elif message.text == "➕ Добавить":
        user_actions[uid] = "adding"
        bot.send_message(message.chat.id, "🖊 Напиши, что добавить в список (до 50 симв.):")
    elif message.text == "❌ Удалить":
        if not user_tasks[uid]: bot.send_message(message.chat.id, "Удалять нечего!")
        else:
            user_actions[uid] = "deleting"
            bot.send_message(message.chat.id, "🔢 Введи НОМЕР задачи, которую хочешь удалить:")
    elif message.text == "🗑 Очистить всё":
        if user_tasks[uid]:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Да", callback_data="confirm_clear"), types.InlineKeyboardButton("❌ Нет", callback_data="cancel_clear"))
            bot.send_message(message.chat.id, "❓ Вы уверены, что хотите удалить ВСЕ задачи?", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Список и так пуст.")

    # ОБРАБОТКА ВВОДА (Действия)
    else:
        action = user_actions[uid]
        if action == "adding":
            if len(message.text) < 50:
                time_now = datetime.now().strftime("%H:%M")
                user_tasks[uid].append(f"[{time_now}] {message.text}")
                bot.send_message(message.chat.id, "✅ Добавлено")
                user_actions[uid] = None
            else:
                bot.send_message(message.chat.id, "❌ Слишком длинно!")
        elif action == "deleting":
            if message.text.isdigit():
                idx = int(message.text) - 1
                if 0 <= idx < len(user_tasks[uid]):
                    user_tasks[uid].pop(idx)
                    bot.send_message(message.chat.id, "🗑 Удалено")
                    user_actions[uid] = None
                else:
                    bot.send_message(message.chat.id, "❌ Нет такого номера!")
            else:
                bot.send_message(message.chat.id, "🔢 Введи именно ЧИСЛО.")
        else:
            try:
                num = float(message.text.replace(',', '.'))
                usd, eur = get_rates()
                if usd:
                    rate = eur if user_modes[uid] == 'eur' else usd
                    res = num / rate
                    bot.send_message(message.chat.id, f"💰 {num} руб. = {res:.2f} {user_modes[uid].upper()}")
                else:
                    bot.send_message(message.chat.id, "⚠️ Банк временно недоступен.")
            except:
                bot.send_message(message.chat.id, "Я тебя не понимаю. Используй меню или введи число.")

# --- 5. CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    '''Обработка команда'''
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    if call.data.startswith('mode_'):
        user_modes[uid] = call.data.split('_')[1]
        label = "➡️ На EUR" if user_modes[uid] == 'usd' else "➡️ На USD"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(label, callback_data=f"mode_{'eur' if user_modes[uid]=='usd' else 'usd'}"))
        bot.edit_message_text(chat_id=uid, message_id=call.message.message_id, text=f"💵 Режим: {user_modes[uid].upper()}\nВведите сумму:", reply_markup=markup)
    
    elif call.data in ["confirm_clear", "cancel_clear"]:
        if call.data == "confirm_clear":
            user_tasks[uid] = []
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🧹 Список полностью очищен.")
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="♻️ Действие отменено.")
    
    elif call.data.startswith('quiz'):
        if uid not in user_scores: user_scores[uid] = 0
        _, q_idx, ans = call.data.split('|')
        q_idx = int(q_idx)
        if ans == quiz_data[q_idx]['correct']:
            user_scores[uid] = user_scores.get(uid, 0) + 1
            res = "✅ Верно!"
        else: res = f"❌ Нет. Ответ: {quiz_data[q_idx]['correct']}"
        bot.edit_message_text(chat_id=uid, message_id=call.message.message_id, text=res)
        if q_idx + 1 < len(quiz_data):
            time.sleep(1)
            show_quiz_question(call.message, q_idx + 1)
        else:
            bot.send_message(uid, f"🏁 Конец! Счет: {user_scores[uid]} из {len(quiz_data)}")

def show_quiz_question(message, q_idx):
    '''Достаем данные вопроса (текст, варианты) из списка по индексу'''
    q = quiz_data[q_idx]
    markup = types.InlineKeyboardMarkup()
    for opt in q['options']:
        markup.add(types.InlineKeyboardButton(opt, callback_data=f"quiz|{q_idx}|{opt}"))
    bot.send_message(message.chat.id, f"❓ {q['question']}", reply_markup=markup)

if __name__ == '__main__':
    #print("Супер-Бот Xaash запущен!")
    bot.infinity_polling()
