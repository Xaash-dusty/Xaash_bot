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
quiz_score = 0
quiz_data = [
    {"question": "Какая планета самая большая?", "options": ["Марс", "Юпитер", "Сатурн"], "correct": "Юпитер"},
    {"question": "Сколько полосок на флаге США?", "options": ["10", "13", "15"], "correct": "13"},
    {"question": "Какой язык программирования мы учим?", "options": ["Java", "Python", "C++"], "correct": "Python"},
    {"question": "2+2*2?", "options": ["8", "4", "6"], "correct": "6"}
]

# --- 2. ФУНКЦИИ-ПОМОЩНИКИ ---

def save_tasks(tasks_list):
    try:
        with open("tasks.txt", "w", encoding="utf-8") as f:
            for task in tasks_list:
                f.write(task + "\n")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def load_tasks():
    if os.path.exists("tasks.txt"):
        with open("tasks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return []

tasks = load_tasks()

def get_rates():
    try:
        rates = ExchangeRates(datetime.now())
        return rates['USD'].value, rates['EUR'].value
    except Exception as e:
        print(f"Ошибка банка: {e}")
        return None, None

# --- 3. ГЛАВНОЕ МЕНЮ ---

@bot.message_handler(commands=['start', 'menu', 'help'])
def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Задачи", "💰 Валюта", "🎮 Викторина")
    
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
        markup.add("📋 Список дел", "🗑 Очистить всё", "🏠 В меню")
        bot.send_message(message.chat.id, "📍 Раздел ЗАДАЧИ\nНапиши текст, чтобы добавить его в список дел.", reply_markup=markup)

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

    # Логика ВАЛЮТ
    elif message.text in ["🇺🇸 Курс USD", "🇪🇺 Курс EUR"]:
        usd, eur = get_rates()
        if usd:
            val = usd if "USD" in message.text else eur
            bot.send_message(message.chat.id, f"📈 Текущий курс ЦБ: {val} руб.")
        else:
            bot.send_message(message.chat.id, "⚠️ Банк временно недоступен.")

    elif message.text == "🔄 Перевод в EUR":
        convert_mode = 'eur'
        bot.send_message(message.chat.id, "🔄 Режим изменен. Теперь я перевожу рубли в ЕВРО.")

    # Логика ЗАДАЧ
    elif message.text == "📋 Список дел":
        if not tasks:
            bot.send_message(message.chat.id, "Твой список пока пуст. ✨")
        else:
            res = "🗒 Твои задачи:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
            bot.send_message(message.chat.id, f"{res}\n\n💡 Введи номер задачи, чтобы удалить её.")

    elif message.text == "🗑 Очистить всё":
        tasks.clear()
        save_tasks(tasks)
        bot.send_message(message.chat.id, "🧹 Список полностью очищен.")

    # Обработка ЧИСЕЛ (Удаление или Конвертация)
    elif message.text.isdigit():
        num = int(message.text)
        # Если это номер задачи
        if tasks and 0 < num <= len(tasks):
            removed = tasks.pop(num - 1)
            save_tasks(tasks)
            bot.send_message(message.chat.id, f"✅ Выполнено и удалено: {removed}")
        # Иначе это сумма для валюты
        else:
            usd, eur = get_rates()
            if usd:
                rate = eur if convert_mode == 'eur' else usd
                curr = "EUR 💶" if convert_mode == 'eur' else "USD 💵"
                res = num / rate
                bot.send_message(message.chat.id, f"💰 {num} руб. = {round(res, 2)} {curr}")

    # Просто ввод текста (Новая задача)
    else:
        if len(message.text) < 60:
            tasks.append(message.text)
            save_tasks(tasks)
            bot.send_message(message.chat.id, f"📝 Добавлено в список: {message.text}")
        else:
            bot.send_message(message.chat.id, "❌ Текст слишком длинный (макс. 60 симв.)")

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
    # Убираем часики и показываем уведомление сверху
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
    print("Супер-Бот Xaash запущен 24/7!")
    bot.infinity_polling(none_stop=True)
