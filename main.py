import telebot
from telebot import types
from pycbrf import ExchangeRates
from datetime import datetime
import os
import time
import random

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Сразу вызываем функцию
keep_alive()


# Инициализация бота
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))


# --- 1. ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ И БАЗЫ ДАННЫХ ---
convert_mode = 'usd'
quiz_score = 0
quiz_data = [
    {"question": "Какая планета самая большая?", "options": ["Марс", "Юпитер", "Сатурн"], "correct": "Юпитер"},
    {"question": "Сколько полосок на флаге США?", "options": ["10", "13", "15"], "correct": "13"},
    {"question": "Какой язык программирования мы учим?", "options": ["Java", "Python", "C++"], "correct": "Python"}
    {"question": "2+2*2?", "options": ["8", "4", "6"], "correct": "6"}
]

# --- 2. ФУНКЦИИ-ПОМОЩНИКИ ---

# Работа с файлами (Задачи)
def save_tasks(tasks_list):
    with open("tasks.txt", "w", encoding="utf-8") as f:
        for task in tasks_list:
            f.write(task + "\n")

def load_tasks():
    if os.path.exists("tasks.txt"):
        with open("tasks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return []

tasks = load_tasks()

# Работа с банком (Валюта)
def get_rates():
    try:
        rates = ExchangeRates(datetime.now())
        return rates['USD'].value, rates['EUR'].value
    except:
        return None, None

# Показ вопроса (Викторина)
def show_quiz_question(message, q_index):
    q = quiz_data[q_index]
    markup = types.InlineKeyboardMarkup()
    for option in q['options']:
        markup.add(types.InlineKeyboardButton(option, callback_data=f"quiz|{q_index}|{option}"))
    bot.send_message(message.chat.id, f"Вопрос №{q_index + 1}: {q['question']}", reply_markup=markup)

# --- 3. ГЛАВНОЕ МЕНЮ ---

@bot.message_handler(commands=['start', 'menu'])
def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📝 Задачи")
    btn2 = types.KeyboardButton("💰 Валюта")
    btn3 = types.KeyboardButton("🎮 Викторина")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "🏠 Главное меню. Выбери раздел:", reply_markup=markup)

# --- 4. ОБРАБОТКА ТЕКСТА ---

@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    global convert_mode, tasks, quiz_score

    # ПЕРЕКЛЮЧЕНИЕ РАЗДЕЛОВ
    if message.text == "📝 Задачи":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📋 Список дел", "🗑 Очистить всё", "🏠 В меню")
        bot.send_message(message.chat.id, "Раздел ЗАДАЧИ. Напиши текст, чтобы добавить дело в список.", reply_markup=markup)

    elif message.text == "💰 Валюта":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🇺🇸 Курс USD", "🇪🇺 Курс EUR", "🔄 Перевод в EUR", "🏠 В меню")
        bot.send_message(message.chat.id, "Раздел ВАЛЮТА. Введи число для перевода или узнай курс.", reply_markup=markup)

    elif message.text == "🎮 Викторина":
        quiz_score = 0
        bot.send_message(message.chat.id, "Начинаем игру!")
        show_quiz_question(message, 0)

    elif message.text == "🏠 В меню":
        convert_mode = 'usd'
        main_menu(message)

    # ЛОГИКА ВАЛЮТ
    elif message.text == "🇺🇸 Курс USD" or message.text == "🇪🇺 Курс EUR":
        usd, eur = get_rates()
        if usd:
            res = usd if "USD" in message.text else eur
            bot.send_message(message.chat.id, f"Текущий курс: {res} руб.")
        else:
            bot.send_message(message.chat.id, "Ошибка связи с банком.")

    elif message.text == "🔄 Перевод в EUR":
        convert_mode = 'eur'
        bot.send_message(message.chat.id, "Режим изменен на ЕВРО 🇪🇺 Вводи сумму.")

    # ЛОГИКА ЗАДАЧ
    elif message.text == "📋 Список дел":
        if not tasks:
            bot.send_message(message.chat.id, "Список пуст!")
        else:
            res = "Твои задачи:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
            bot.send_message(message.chat.id, f"{res}\n\n(Введи номер, чтобы удалить)")

    elif message.text == "🗑 Очистить всё":
        tasks.clear()
        save_tasks(tasks)
        bot.send_message(message.chat.id, "Список очищен 🧹")

    # ОБРАБОТКА ЧИСЕЛ (Удаление задач ИЛИ Конвертация)
    elif message.text.isdigit():
        val = int(message.text)
        # Если это может быть номером задачи
        if tasks and 0 < val <= len(tasks):
            removed = tasks.pop(val - 1)
            save_tasks(tasks)
            bot.send_message(message.chat.id, f"Удалено: {removed} ✅")
        # Иначе считаем валюту
        else:
            usd, eur = get_rates()
            if usd:
                rate = eur if convert_mode == 'eur' else usd
                currency = "EUR" if convert_mode == 'eur' else "USD"
                res = val / rate
                bot.send_message(message.chat.id, f"{val} руб. = {round(res, 2)} {currency}")

    # ДОБАВЛЕНИЕ НОВОЙ ЗАДАЧИ (если текст не подошел под кнопки)
    else:
        if len(message.text) < 50:
            tasks.append(message.text)
            save_tasks(tasks)
            bot.send_message(message.chat.id, f"Добавлено в задачи: {message.text} ✅")
        else:
            bot.send_message(message.chat.id, "Слишком длинно!")

# --- 5. ОБРАБОТКА КНОПОК ВИКТОРИНЫ ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz'))
def handle_quiz(call):
    global quiz_score
    bot.answer_callback_query(call.id)
    
    # Разбираем данные: quiz|индекс|ответ
    _, q_index, user_answer = call.data.split('|')
    q_index = int(q_index)
    
    correct = quiz_data[q_index]['correct']
    if user_answer == correct:
        quiz_score += 1
        text = f"✅ Верно! {user_answer}"
    else:
        text = f"❌ Нет, правильно: {correct}"
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text)
    
    next_q = q_index + 1
    if next_q < len(quiz_data):
        time.sleep(1.5)
        show_quiz_question(call.message, next_q)
    else:
        bot.send_message(call.message.chat.id, f"🏁 Конец! Очки: {quiz_score} из {len(quiz_data)}")

# Запуск
print("Супер-Бот Xaash запущен и ждет команд!")
bot.infinity_polling(none_stop=True)
