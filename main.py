import telebot
from telebot import types
from pycbrf import ExchangeRates
from datetime import datetime
import os
import time
import random
from flask import Flask
from threading import Thread

# --- 0. KEEP ALIVE (ДЛЯ РАБОТЫ 24/7) ---
app = Flask('')

@app.route('/')
def home():
    return "Status: Online"

def run():
    # Запуск микро-сервера для предотвращения сна хостинга
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Запуск сервера в отдельном потоке, чтобы не блокировать бота
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()

# --- 1. НАСТРОЙКИ И ДАННЫЕ ---
# Токен берем из переменных окружения (безопасность!)
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

# Глобальные переменные состояния
convert_mode = 'usd'  # Текущая валюта для конвертации
current_action = None # Состояние юзера (например, 'adding' или 'deleting')
quiz_score = 0        # Очки текущей викторины

# Данные викторины (можно расширять здесь)
quiz_data = [
    {"question": "Какая планета самая большая?", "options": ["Марс", "Юпитер", "Сатурн"], "correct": "Юпитер"},
    {"question": "Сколько полосок на флаге США?", "options": ["10", "13", "15"], "correct": "13"},
    {"question": "Какой язык программирования мы учим?", "options": ["Java", "Python", "C++"], "correct": "Python"},
    {"question": "2+2*2?", "options": ["8", "4", "6"], "correct": "6"}
]

# --- 2. ФУНКЦИИ-ПОМОЩНИКИ (РАБОТА С ДАННЫМИ) ---

def save_tasks(tasks_list):
    """Сохраняет список задач в текстовый файл."""
    try:
        with open("tasks.txt", "w", encoding="utf-8") as f:
            for task in tasks_list:
                f.write(task + "\n")
    except Exception as e:
        print(f"Ошибка сохранения в файл: {e}")

def load_tasks():
    """Загружает задачи из файла при старте."""
    if os.path.exists("tasks.txt"):
        with open("tasks.txt", "r", encoding="utf-8") as f:
            # strip() убирает переносы строк \n
            return [line.strip() for line in f.readlines()]
    return []

# Инициализируем список задач из файла
tasks = load_tasks()

def get_rates():
    """Запрашивает свежие курсы валют у ЦБ РФ."""
    try:
        rates = ExchangeRates(datetime.now())
        return rates['USD'].value, rates['EUR'].value
    except Exception as e:
        print(f"Ошибка получения курсов: {e}")
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
        "✅ **Задачи:** Нажми «➕ Добавить» или просто пиши текст.\n"
        "📈 **Курсы:** В разделе Валюта можно считать рубли.\n"
        "🎮 **Игры:** Викторина на 4 вопроса.\n"
        "\nИспользуй кнопки меню для навигации!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['start', 'menu'])
def main_menu(message):
    """Главное меню бота."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Группируем кнопки: две сверху, одна снизу
    markup.row("📝 Задачи", "💰 Валюта")
    markup.row("🎮 Викторина")
    
    welcome = f"👋 Привет, {message.from_user.first_name}! Чем займемся?"
    bot.send_message(message.chat.id, welcome, reply_markup=markup)

# --- 4. ОСНОВНОЙ ОБРАБОТЧИК (НАВИГАЦИЯ) ---

@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    global convert_mode, tasks, current_action

    # Кнопка возврата (срабатывает всегда)
    if message.text == "🏠 В меню":
        current_action = None
        main_menu(message)
        return

    # Логика переключения разделов
    if message.text == "📝 Задачи":
        current_action = None # Сброс старого действия
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📋 Список дел", "➕ Добавить", "❌ Удалить")
        markup.add("🗑 Очистить всё", "🏠 В меню")
        bot.send_message(message.chat.id, "📍 Раздел: ЗАДАЧИ", reply_markup=markup)
        return

    # --- РАЗДЕЛ ВАЛЮТА ---
    elif message.text == "💰 Валюта":
        current_action = "converting" # Включаем режим ожидания цифр для расчета
        show_currency_menu(message)

    elif "Перевод в" in message.text:
        # Умное переключение: если было usd -> станет eur, и наоборот
        convert_mode = 'eur' if convert_mode == 'usd' else 'usd'
        # Сразу обновляем меню, чтобы кнопка изменилась визуально
        show_currency_menu(message)

    # --- ОБРАБОТКА ВВОДА (Действия в зависимости от current_action) ---
    else:
        # 1. Режим добавления задачи
        if current_action == "adding":
            if len(message.text) < 60:
                tasks.append(message.text)
                save_tasks(tasks)
                bot.send_message(message.chat.id, f"✅ Добавлено: {message.text}")
                current_action = None  # Выходим из режима после успеха
            else:
                bot.send_message(message.chat.id, "⚠️ Слишком длинно! Попробуй короче.")

        # 2. Режим удаления задачи
        elif current_action == "deleting":
            if message.text.isdigit():
                num = int(message.text)
                if 0 < num <= len(tasks):
                    removed = tasks.pop(num - 1)
                    save_tasks(tasks)
                    bot.send_message(message.chat.id, f"🗑 Удалено: {removed}")
                    current_action = None # Сброс состояния
                else:
                    bot.send_message(message.chat.id, "❌ Задачи с таким номером нет!")
            else:
                bot.send_message(message.chat.id, "🔢 Введи именно число (номер задачи).")

        # 3. Режим конвертации валют
        elif current_action == "converting":
            if message.text.replace('.', '', 1).isdigit(): # Проверка на число (включая дробные)
                usd, eur = get_rates()
                if usd:
                    rate = eur if convert_mode == 'eur' else usd
                    curr = "EUR 💶" if convert_mode == 'eur' else "USD 💵"
                    res = float(message.text) / rate
                    bot.send_message(message.chat.id, f"💰 {message.text} руб. = {round(res, 2)} {curr}")
                else:
                    bot.send_message(message.chat.id, "🏦 Проблемы со связью с ЦБ.")
            else:
                bot.send_message(message.chat.id, "📍 Введи сумму цифрами для перевода.")

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def show_currency_menu(message):
    """Динамическое создание меню валют."""
    global convert_mode
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Меняем текст на кнопке в реальном времени
    change_btn = "🔄 Перевод в EUR" if convert_mode == 'usd' else "🔄 Перевод в USD"
    
    markup.row("🇺🇸 Курс USD", "🇪🇺 Курс EUR")
    markup.row(change_btn)
    markup.row("🏠 В меню")
    
    msg = f"📈 Режим: {convert_mode.upper()}\nВведи сумму в рублях, чтобы перевести:"
    bot.send_message(message.chat.id, msg, reply_markup=markup)

# --- 5. ЛОГИКА ВИКТОРИНЫ (INLINE КНОПКИ) ---

def show_quiz_question(message, q_index):
    """Формирует вопрос с Inline-кнопками."""
    q = quiz_data[q_index]
    markup = types.InlineKeyboardMarkup()
    # Создаем кнопки для каждого варианта ответа
    for option in q['options']:
        # В callback_data передаем тип события, индекс вопроса и выбранный ответ
        markup.add(types.InlineKeyboardButton(option, callback_data=f"quiz|{q_index}|{option}"))
    bot.send_message(message.chat.id, f"❓ {q['question']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz'))
def handle_quiz(call):
    """Обработка нажатий на ответы викторины."""
    global quiz_score
    bot.answer_callback_query(call.id) # Убираем индикатор нажатия
    
    # Парсим данные из callback_data
    _, q_index, user_answer = call.data.split('|')
    q_index = int(q_index)
    
    correct = quiz_data[q_index]['correct']
    
    # Сверяем ответ
    if user_answer == correct:
        quiz_score += 1
        res_text = f"✅ Верно! {user_answer}"
    else:
        res_text = f"❌ Нет, это {correct}"
    
    # Редактируем текущее сообщение (эффект «замены» текста на результат)
    bot.edit_message_text(chat_id=call.message.chat.id, 
                          message_id=call.message.message_id, 
                          text=res_text)
    
    # Проверка на завершение
    next_q = q_index + 1
    if next_q < len(quiz_data):
        time.sleep(1) # Короткая пауза для чтения результата
        show_quiz_question(call.message, next_q)
    else:
        bot.send_message(call.message.chat.id, 
                         f"🏁 Конец! Результат: {quiz_score}/{len(quiz_data)}")

# --- ЗАПУСК ---
if __name__ == '__main__':
    # Сообщение в консоль для нас
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот Xaash запущен!")
    bot.infinity_polling(none_stop=True)
