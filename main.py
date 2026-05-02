import telebot
from telebot import types
from pycbrf import ExchangeRates
from datetime import datetime, timedelta, timezone
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
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0)) 

quiz_data = [
    {"question": "Какая планета самая большая?", "options": ["Марс", "Юпитер", "Сатурн"], "correct": "Юпитер"},
    {"question": "Сколько полосок на флаге США?", "options": ["10", "13", "15"], "correct": "13"},
    {"question": "На каком языке программирования обычно пишут простых ТГ ботов?", "options": ["Java", "Python", "C++"], "correct": "Python"},
    {"question": "2+2*2?", "options": ["8", "4", "6"], "correct": "6"},
    {"question": "Какой химический символ у золота?", "options": ["Ag", "Au", "Fe"], "correct": "Au"},
    {"question": "Кто написал 'Преступление и наказание'?", "options": ["Толстой", "Чехов", "Достоевский"], "correct": "Достоевский"},
    {"question": "В каком году человек впервые полетел в космос?", "options": ["1957", "1961", "1969"], "correct": "1961"},
    {"question": "Какой океан самый большой на Земле?", "options": ["Атлантический", "Индийский", "Тихий"], "correct": "Тихий"},
    {"question": "Сколько материков на планете Земля?", "options": ["5", "6", "7"], "correct": "6"},
    {"question": "Какая столица у Франции?", "options": ["Лондон", "Берлин", "Париж"], "correct": "Париж"},
    {"question": "Какое животное считается самым быстрым?", "options": ["Лев", "Гепард", "Сокол"], "correct": "Гепард"},
    {"question": "Из чего получают изюм?", "options": ["Слива", "Абрикос", "Виноград"], "correct": "Виноград"},
    {"question": "Как называется столица Японии?", "options": ["Пекин", "Сеул", "Токио"], "correct": "Токио"},
    {"question": "Сколько дней в високосном году?", "options": ["364", "365", "366"], "correct": "366"},
    {"question": "Какая самая высокая гора в мире?", "options": ["Эльбрус", "Эверест", "Килиманджаро"], "correct": "Эверест"},
    {"question": "Какое вещество самое твердое на Земле?", "options": ["Сталь", "Алмаз", "Гранит"], "correct": "Алмаз"},
    {"question": "Какой газ составляет большую часть атмосферы Земли?", "options": ["Кислород", "Азот", "Углекислый газ"], "correct": "Азот"},
    {"question": "В какой стране находится пирамида Хеопса?", "options": ["Мексика", "Египет", "Иран"], "correct": "Египет"},
    {"question": "Как зовут главного героя серии книг о Гарри Поттере?", "options": ["Рон", "Драко", "Гарри"], "correct": "Гарри"},
    {"question": "Какая единица измерения силы тока?", "options": ["Вольт", "Ватт", "Ампер"], "correct": "Ампер"},
    {"question": "Как называется самая длинная река в мире?", "options": ["Амазонка", "Нил", "Янцзы"], "correct": "Амазонка"},
    {"question": "Сколько цветов в радуге?", "options": ["6", "7", "8"], "correct": "7"},
    {"question": "В каком городе находится Эйфелева башня?", "options": ["Рим", "Париж", "Вена"], "correct": "Париж"},
    {"question": "Кто изобрел лампочку?", "options": ["Тесла", "Эдисон", "Белл"], "correct": "Эдисон"},
    {"question": "Какое море самое соленое?", "options": ["Красное", "Средиземное", "Мертвое"], "correct": "Мертвое"},
    {"question": "Сколько зубов у взрослого человека?", "options": ["28", "30", "32"], "correct": "32"},
    {"question": "Как называется орган дыхания у рыб?", "options": ["Легкие", "Жабры", "Кожа"], "correct": "Жабры"},
    {"question": "Какая валюта используется в Японии?", "options": ["Юань", "Вона", "Иена"], "correct": "Иена"},
    {"question": "Кто написал 'Ромео и Джульетту'?", "options": ["Данте", "Шекспир", "Гете"], "correct": "Шекспир"},
    {"question": "В какой стране изобрели бумагу?", "options": ["Греция", "Индия", "Китай"], "correct": "Китай"},
    {"question": "Какое число называют 'дюжиной'?", "options": ["10", "12", "13"], "correct": "12"},
    {"question": "Как называется крупный остров на юге Италии?", "options": ["Сицилия", "Корсика", "Крит"], "correct": "Сицилия"},
    {"question": "Какой орган человека качает кровь?", "options": ["Печень", "Мозг", "Сердце"], "correct": "Сердце"},
    {"question": "Какое дерево считается символом России?", "options": ["Дуб", "Береза", "Сосна"], "correct": "Береза"},
    {"question": "Как называется столица Германии?", "options": ["Мюнхен", "Берлин", "Гамбург"], "correct": "Берлин"},
    {"question": "Что изучает ботаника?", "options": ["Животных", "Растения", "Звезды"], "correct": "Растения"},
    {"question": "Как называется замерзшая вода?", "options": ["Пар", "Лед", "Роса"], "correct": "Лед"},
    {"question": "Сколько минут в одном часе?", "options": ["50", "60", "100"], "correct": "60"},
    {"question": "Какой инструмент используют для измерения температуры?", "options": ["Барометр", "Термометр", "Линейка"], "correct": "Термометр"},
    {"question": "В каком году закончилась Вторая мировая война?", "options": ["1941", "1945", "1953"], "correct": "1945"},
    {"question": "Какая птица не умеет летать?", "options": ["Орел", "Пингвин", "Воробей"], "correct": "Пингвин"},
    {"question": "Как называется наука о небесных телах?", "options": ["Биология", "Геология", "Астрономия"], "correct": "Астрономия"},
    {"question": "Сколько сторон у квадрата?", "options": ["3", "4", "5"], "correct": "4"},
    {"question": "Какой фрукт называют 'плодом раздора'?", "options": ["Груша", "Яблоко", "Персик"], "correct": "Яблоко"},
    {"question": "На каком континенте находится пустыня Сахара?", "options": ["Азия", "Австралия", "Африка"], "correct": "Африка"},
    {"question": "Кто был первым президентом США?", "options": ["Линкольн", "Вашингтон", "Джефферсон"], "correct": "Вашингтон"},
    {"question": "Какое вещество необходимо человеку для дыхания?", "options": ["Азот", "Кислород", "Водород"], "correct": "Кислород"},
    {"question": "Как называется маленькая точка на экране?", "options": ["Пиксель", "Бит", "Спрайт"], "correct": "Пиксель"},
    {"question": "Сколько секунд в минуте?", "options": ["30", "60", "100"], "correct": "60"},
    {"question": "Какая планета ближе всего к Солнцу?", "options": ["Венера", "Марс", "Меркурий"], "correct": "Меркурий"}
]

# ПЕРСОНАЛЬНЫЕ СЛОВАРИ
user_tasks = {}    #Задачи
user_scores = {}   #Счет в викторине
user_modes = {}    #Конвертер
user_actions = {}  #Режим
user_quiz_order = {}    #Перемешанные вопросы

# --- 2. ПОМОЩНИКИ ---
import json

DB_FILE = "user_data.json"

def save_data():
    """Сохраняет словарь user_tasks в файл."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(user_tasks, f, ensure_ascii=False, indent=4)

def load_data():
    """Загружает данные из файла при старте."""
    global user_tasks
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            # JSON хранит ключи как строки, превращаем их обратно в числа (ID)
            data = json.load(f)
            user_tasks = {int(k): v for k, v in data.items()}
    else:
        user_tasks = {}

# Сразу вызываем загрузку при старте скрипта
load_data()

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
    uid = message.from_user.id
    user_actions[uid] = None
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Список дел", "➕ Добавить", "❌ Удалить")
    markup.add("🗑 Очистить всё", "🏠 В меню")
    bot.send_message(message.chat.id, "📝 Меню задач открыто!\n\n/help — вызвать справку.", reply_markup=markup)

@bot.message_handler(commands=['quiz'])
def fast_quiz(message):
    """Быстрый переход к викторине через /quiz."""
    uid = message.from_user.id
    user_actions[uid] = None
    user_scores[message.from_user.id] = 0
    # Создаем список индексов [0, 1, 2, 3] и перемешиваем его
    indices = list(range(len(quiz_data)))
    random.shuffle(indices)
    # Сохраняем этот порядок для конкретного пользователя
    user_quiz_order[uid] = indices 
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 Задачи", "💰 Валюта")
    markup.row("🎮 Викторина")
    bot.send_message(message.chat.id, f"🕹 Начинаем викторину!Всего {len(quiz_data)} вопросов. Удачи!\n\n/help — вызвать справку.")
    show_quiz_question(message, 0)
    
@bot.message_handler(commands=['rates'])
def fast_rates(message):
    """Быстрый переход к валютам через /rates."""
    uid = message.from_user.id
    user_actions[uid] = None
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇺🇸 Курс USD", "🇪🇺 Курс EUR", "🔄 Конвертер", "🏠 В меню")
    bot.send_message(
        message.chat.id, 
        "📍 Раздел ВАЛЮТА\nВыбери курс или нажми «Конвертер»\n\n/help — вызвать справку.", 
        reply_markup=markup
    )


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
        "• Быстрый доступ: /tasks\n\n"
        
        "📈 **ВАЛЮТА**\n"
        "• Актуальные курсы USD и EUR.\n"
        "• Удобный конвертер из рублей.\n"
        "• Быстрый доступ: /rates\n\n"
        
        f"🎮 **ВИКТОРИНА**\n"
        f"• Тест на {len(quiz_data)} вопросов. Проверь себя!\n"
        "• Быстрый старт: /quiz\n\n"
        
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "📍 **БЫСТРЫЕ КОМАНДЫ:**\n"
        "• /start или /menu — главное меню.\n"
        "• /help — вызвать эту справку.\n\n"
        "✨ *Используй кнопки внизу для удобной навигации!*"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['start', 'menu'])
def main_menu(message):
    '''ГЛАВНОЕ МЕНЮ'''
    uid = message.from_user.id
    user_actions[uid] = None
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 Задачи", "💰 Валюта")
    markup.row("🎮 Викторина")
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я твой многофункциональный помощник.\n"
        "Выбери нужный раздел в меню ниже: 👇\n\n/help — вызвать справку."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# --- 4. ОБРАБОТЧИК ТЕКСТА ---
@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    '''ОБРАБОТЧИК ТЕКСТА'''
    uid = message.from_user.id
    text = message.text.lower()
    
    # Инициализация данных пользователя, если их нет
    if uid not in user_tasks: user_tasks[uid] = []
    if uid not in user_modes: user_modes[uid] = 'usd'
    if uid not in user_actions: user_actions[uid] = None
    
    # ЛОГИРОВАНИЕ АДМИНУ
    if uid != ADMIN_ID:
        first_name = message.from_user.first_name if message.from_user.first_name else "нет имени"
        username = message.from_user.username if message.from_user.username else "нет ника"
        # 1. Сначала уведомляем админа (вас)
        report = f"👤 От: {first_name} (@{username})\n" \
                 f"🆔 ID: {uid}\n" \
                 f"💬 Текст: {message.text}"
        bot.send_message(ADMIN_ID, report)
        if text == "я":
            bot.send_message(message.chat.id, "Вы — мой дорогой пользователь, а я — ваш верный помощник! 😊")
    else:
        if text == "я":
            bot.send_message(message.chat.id, 'Вы мой Хозяин👑')

    # НАВИГАЦИЯ
    if message.text == "📝 Задачи":
        fast_tasks(message)
    elif message.text == "💰 Валюта":
        fast_rates(message)
    elif message.text == "🎮 Викторина":
        fast_quiz(message)
    elif message.text == "🏠 В меню":
        user_actions[uid] = None
        main_menu(message)

    # ЛОГИКА ВАЛЮТ
    elif message.text in ["🇺🇸 Курс USD", "🇪🇺 Курс EUR"]:
        usd, eur = get_rates()
        val = usd if "USD" in message.text else eur
        t = 'USD' if "USD" in message.text else 'EUR'
        bot.send_message(message.chat.id, f"📈 Курс {t}: {val} руб." if val else "⚠️ Ошибка банка")

    elif message.text == "🔄 Конвертер":
        user_actions[uid] = "converting"
        markup = types.InlineKeyboardMarkup()
        mode = user_modes[uid]
        label = "➡️ На EUR" if mode == 'usd' else "➡️ На USD"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"mode_{'eur' if mode=='usd' else 'usd'}"))
        bot.send_message(message.chat.id, f"💵 Сейчас режим: {mode.upper()}\nВведите сумму в рублях цифрами:", reply_markup=markup)

    # ЛОГИКА ЗАДАЧ
    elif message.text == "📋 Список дел":
        tasks = user_tasks[uid]
        res = "🗒 Твои задачи:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)]) if tasks else "Список пуст."
        if tasks:
            bot.send_message(message.chat.id, f"{res}\n\n💡 Нажми «❌ Удалить», чтобы стереть задачу.")
        else:
            bot.send_message(message.chat.id, f"{res}")
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

    # ОБРАБОТКА ВВОДА (Действия в режимах)
    else:       #другой текст или число
        action = user_actions.get(uid) # Безопасно получаем действие
        
        if action == "adding":
            if len(message.text) < 50:
                offset = timezone(timedelta(hours=3))
                time_now = datetime.now(offset).strftime("%H:%M")
                user_tasks[uid].append(f"[{time_now}] {message.text}")
                save_data()
                bot.send_message(message.chat.id, f"✅ Добавлено: [{time_now}] {message.text}")
                user_actions[uid] = None
            else:
                bot.send_message(message.chat.id, "❌ Слишком длинное название!")

        elif action == "deleting":
            if message.text.isdigit():
                idx = int(message.text) - 1
                if 0 <= idx < len(user_tasks[uid]):
                    removed = user_tasks[uid].pop(idx)
                    save_data()
                    bot.send_message(message.chat.id, f"🗑 Удалено: {removed}")
                    user_actions[uid] = None
                else:
                    bot.send_message(message.chat.id, "❌ Нет задачи с таким номером!")
            else:
                bot.send_message(message.chat.id, "🔢 Введи номер числом.")

        elif action == "converting":        #выбрано "🔄 Конвертер" текст или число
            try:
                num = float(message.text.replace(',', '.'))
                usd, eur = get_rates()
                if usd is not None:
                    # Превращаем Decimal из банка в обычное число для расчетов
                    rate = float(eur if user_modes[uid] == 'eur' else usd)
                    res = num / rate
                    bot.send_message(message.chat.id, f"💰 {num} руб. = {res:.2f} {user_modes[uid].upper()}")
                    # Здесь режим НЕ сбрасываем, чтобы юзер мог вводить числа дальше
                else:
                    bot.send_message(message.chat.id, "⚠️ Ошибка банка. Попробуй позже.")
            except ValueError:
                bot.send_message(message.chat.id, "🔢 Введи сумму цифрами (например: 100 или 50.5)")
            except Exception as e:
                bot.send_message(message.chat.id, f"Ошибка: {e}")
        else:
            if text != "я":
            # Если никакого режима нет и это не команда — тогда уже пишем "Не понимаю" или просто текст
                bot.send_message(message.chat.id, "❓ Я тебя не понимаю. Используй кнопки меню.")
            


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
            save_data()
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="🧹 Список полностью очищен.")
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="♻️ Действие отменено.")
    
    elif call.data.startswith("quiz_stop"):
        # Достаем индекс вопроса из callback_data
        _, q_idx = call.data.split('|')
        q_idx = int(q_idx)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        # Теперь q_idx доступен, и мы показываем, сколько пройдено
        bot.send_message(uid, f"🚫 Викторина остановлена.\n📊 Ваш результат: {user_scores.get(uid, 0)} из {q_idx}")
        main_menu(call)


    elif call.data.startswith('quiz'):
        if uid not in user_scores: user_scores[uid] = 0
        _, q_idx, ans = call.data.split('|')
        q_idx = int(q_idx)
        
        # 1. Удаляем сообщение с вопросом и кнопками
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
            
        # 2. Проверяем ответ
        real_idx = user_quiz_order[uid][q_idx]
        if ans == quiz_data[real_idx]['correct']:
            user_scores[uid] += 1
            res_text = "✅ Верно!"
        else: 
            res_text = f"❌ Нет. Ответ: {quiz_data[real_idx]['correct']}"
        res_text = f"Вопрос {q_idx + 1}: {res_text}"
        
        # 3. Отправляем временный результат
        #temp_res = bot.send_message(uid, res_text)
        bot.send_message(uid, res_text)
        
        # 4. Пауза, чтобы юзер успел прочитать
        #time.sleep(1.5) 
        
        # 5. Удаляем временный результат
        # try:
            # bot.delete_message(uid, temp_res.message_id)
        # except Exception:
            # pass

        # 6. Либо следующий вопрос, либо финал
        if q_idx + 1 < len(quiz_data):
            show_quiz_question(call.message, q_idx + 1)
        else:
            bot.send_message(uid, f"🏁 Конец! Счет: {user_scores[uid]} из {len(quiz_data)}")

def show_quiz_question(message, q_idx):
    uid = message.chat.id
    # Берем реальный номер вопроса из нашего перемешанного списка
    real_idx = user_quiz_order[uid][q_idx] 
    q = quiz_data[real_idx]
    
    # Перемешиваем варианты (как делали раньше)
    options = list(q['options'])
    random.shuffle(options)
    
    markup = types.InlineKeyboardMarkup()
    for opt in options:
        # В callback_data передаем q_idx (номер шага), а не реальный индекс
        markup.add(types.InlineKeyboardButton(opt, callback_data=f"quiz|{q_idx}|{opt}"))
    
    markup.add(types.InlineKeyboardButton("🚪 Прервать", callback_data=f"quiz_stop|{q_idx}"))
    bot.send_message(uid, f"❓ {q['question']}", reply_markup=markup)


if __name__ == '__main__':
    #print("Супер-Бот Xaash запущен!")
    bot.infinity_polling()
