import telebot
from telebot import types
from pycbrf import ExchangeRates
from datetime import datetime
import os
import time
import random
from flask import Flask
from threading import Thread

# --- 0. ПРЕДОТВРАЩЕНИЕ ЗАСЫПАНИЯ (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "Status: Online"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()

# --- 1. НАСТРОЙКИ И ДАННЫЕ ---
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

convert_mode = 'usd'
current_action = None
quiz_score = 0
quiz_data = [
    {"question": "Какая планета самая большая?", "options": ["Марс", "Юпитер", "Сатурн"], "correct": "Юпитер"},
    {"question": "Сколько полосок на флаге США?", "options": ["10", "13", "15"], "correct": "13"},
    {"question": "На каком языке программирования обычно пишут простых ТГ ботов?", "options": ["Java", "Python", "C++"], "correct": "Python"},
    {"question": "2+2*2?", "options": ["8", "4", "6"], "correct": "6"}
]

# --- 2. ФУНКЦИИ-ПОМОЩНИКИ ---

def save_tasks(tasks_list):
    """Сохраняет список задач в текстовый файл."""
    try:
        with open("tasks.txt", "w", encoding="utf-8") as f:
            for task in tasks_list:
                f.write(task + "\n")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def load_tasks():
    """Загружает задачи из файла при старте."""
    if os.path.exists("tasks.txt"):
        with open("tasks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return []

tasks = load_tasks()

def get_rates():
    """Запрашивает свежие курсы валют у ЦБ РФ."""
    try:
        rates = ExchangeRates(datetime.now())
        return rates['USD'].value, rates['EUR'].value
    except Exception as e:
        print(f"Ошибка банка: {e}")
        return None, None

# --- 3. КОМАНДЫ (БЫСТРЫЙ ДОСТУП) ---

@bot.message_handler(commands=['tasks'])
def fast_tasks(message):
    """Быстрый переход к задачам через /tasks."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Список дел", "➕ Добавить", "❌ Удалить")
    markup.add("🗑 Очистить всё", "🏠 В меню")
    bot.send_message(message.chat.id, "📝 Меню задач открыто!", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Справка по командам."""
    help_text = (
        "❓ **Шпаргалка по боту:**\n\n"
        "✅ **Задачи:** Нажми «➕ Добавить» чтобы добавить задачу и «❌ Удалить» чтобы удалить, а также можешь увидеть свой список задач или полностью его отчистить одной кнопкой.\n"
        "📈 **Курсы:** В разделе Валюта можно увидеть курсы доллара и евро, а также конвертировать рубли в данные валюты.\n"
        f"🎮 **Игры:** Викторина на {len(quiz_data)} вопроса. Попробуй ответить на всё!\n"
        "Напиши /help для вызова этого сообщения.\n"
        "Для быстрого доступа к задачам /tasks.\n"
        "Чтобы перейти в главное меню /start или /menu.\n"
        "\nИспользуй кнопки меню для навигации!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# --- 3.1. ГЛАВНОЕ МЕНЮ ---

@bot.message_handler(commands=['start', 'menu'])
def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 Задачи", "💰 Валюта")
    markup.row("🎮 Викторина")
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я твой многофункциональный помощник.\n"
        "Выбери нужный раздел в меню ниже: 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# --- 4. ОСНОВНОЙ ОБРАБОТЧИК ---

@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    global convert_mode, tasks, quiz_score

    # Переход в разделы
    if message.text == "📝 Задачи":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📋 Список дел", "➕ Добавить", "❌ Удалить")
        markup.add("🗑 Очистить всё", "🏠 В меню")
        bot.send_message(message.chat.id, "📍 Раздел ЗАДАЧИ\nВыбери действие со списком задач в меню ниже.", reply_markup=markup)

    elif message.text == "💰 Валюта":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🇺🇸 Курс USD", "🇪🇺 Курс EUR", "🔄 Перевод в EUR", "🏠 В меню")
        bot.send_message(message.chat.id, "📍 Раздел ВАЛЮТА\nУзнай курс или введи число для конвертации.", reply_markup=markup)

    elif message.text == "🎮 Викторина":
        quiz_score = 0
        bot.send_message(message.chat.id, f"🕹 Начинаем викторину!Всего вопросов {len(quiz_data)}. Удачи!")
        show_quiz_question(message, 0)

    elif message.text == "🏠 В меню":
        convert_mode = 'usd'
        main_menu(message)
        
        
    # --- ЛОГИКА ВАЛЮТ ---
    elif message.text in ["🇺🇸 Курс USD", "🇪🇺 Курс EUR"]:
        usd, eur = get_rates()
        if usd:
            val = usd if "USD" in message.text else eur
            bot.send_message(message.chat.id, f"📈 Текущий курс ЦБ: {val} руб.")
        else:
            bot.send_message(message.chat.id, "⚠️ Банк временно недоступен.")

    elif message.text == "🔄 Перевод в EUR":
        convert_mode = 'eur'
        bot.send_message(message.chat.id, "🔄 Режим изменен. Теперь я перевожу рубли в ЕВРО. Введи сумму цифрами:")

    # --- ЛОГИКА ЗАДАЧ ---
    elif message.text == "📋 Список дел":
        if not tasks:
            bot.send_message(message.chat.id, "Твой список пока пуст. ✨")
        else:
            res = "🗒 Твои задачи:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
            bot.send_message(message.chat.id, f"{res}\n\n💡 Нажми «❌ Удалить», чтобы стереть задачу.")

    elif message.text == "🗑 Очистить всё":
        if not tasks:
            bot.send_message(message.chat.id, "Список и так пуст.")
        else:
            tasks.clear()
            save_tasks(tasks)
            bot.send_message(message.chat.id, "🧹 Список полностью очищен.")
        
    elif message.text == "❌ Удалить":
        if not tasks:
            bot.send_message(message.chat.id, "Удалять нечего!")
        else:
            global current_action
            current_action = "deleting"
            bot.send_message(message.chat.id, "🔢 Введи НОМЕР задачи, которую хочешь удалить:")
    
    elif message.text == "➕ Добавить":
        current_action = "adding"
        bot.send_message(message.chat.id, "🖊 Напиши, что добавить в список (до 50 симв.):")

    # --- ОБРАБОТКА ВВОДА (Действия в режимах) ---
    else:
        # Если юзер в режиме добавления
        if current_action == "adding":
            if len(message.text) < 50:
                tasks.append(message.text)
                save_tasks(tasks)
                bot.send_message(message.chat.id, f"✅ Добавлено: {message.text}")
                current_action = None # Сброс
            else:
                bot.send_message(message.chat.id, "❌ Слишком длинно!")

        # Если юзер в режиме удаления
        elif current_action == "deleting":
            if message.text.isdigit():
                num = int(message.text)
                if 0 < num <= len(tasks):
                    removed = tasks.pop(num - 1)
                    save_tasks(tasks)
                    bot.send_message(message.chat.id, f"🗑 Удалено: {removed}")
                    current_action = None # Сброс
                else:
                    bot.send_message(message.chat.id, "❌ Нет такого номера!")
            else:
                bot.send_message(message.chat.id, "🔢 Введи именно ЧИСЛО.")

        # Если просто введено число (конвертация)
        elif message.text.isdigit():
            num = int(message.text)
            usd, eur = get_rates()
            if usd:
                rate = eur if convert_mode == 'eur' else usd
                curr = "EUR 💶" if convert_mode == 'eur' else "USD 💵"
                res = num / rate
                bot.send_message(message.chat.id, f"💰 {num} руб. = {round(res, 2)} {curr}")

# --- 5. ЛОГИКА ВИКТОРИНЫ ---

def show_quiz_question(message, q_index):
    q = quiz_data[q_index]
    markup = types.InlineKeyboardMarkup()
    for option in q['options']:
        markup.add(types.InlineKeyboardButton(option, callback_data=f"quiz|{q_index}|{option}"))
    bot.send_message(message.chat.id, f"❓ {q['question']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz'))
def handle_quiz(call):
    global quiz_score
    bot.answer_callback_query(call.id, text="Ответ принят!")
    
    _, q_index, user_answer = call.data.split('|')
    q_index = int(q_index)
    
    correct = quiz_data[q_index]['correct']
    if user_answer == correct:
        quiz_score += 1
        res_text = f"✅ Верно! Это {user_answer}."
    else:
        res_text = f"❌ Ошибка. Правильный ответ: {correct}."
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=res_text)
    
    next_q = q_index + 1
    if next_q < len(quiz_data):
        time.sleep(1.5)
        show_quiz_question(call.message, next_q)
    else:
        bot.send_message(call.message.chat.id, f"🏁 Игра окончена!\nТвой результат: {quiz_score} из {len(quiz_data)}")

# --- ЗАПУСК ---
if __name__ == '__main__':
    # Обязательно добавь переменную current_action в начало кода (Часть 1)
    current_action = None 
    print("Супер-Бот Xaash запущен!")
    bot.infinity_polling(none_stop=True)
