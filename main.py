import telebot
import sqlite3
import time
from datetime import datetime, timedelta
TOKEN = '6030078538:AAHKvt2iH4-jl-Lw-dHEp2tJhJU7W0Z6TEk'
bot = telebot.TeleBot(TOKEN)

start_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
start_keyboard.add(telebot.types.KeyboardButton('Добавить объявление'))
start_keyboard.add(telebot.types.KeyboardButton('Просмотреть объявления'))

cancel_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
cancel_keyboard.add(telebot.types.KeyboardButton('Отмена'))

def is_start_step(message):
    return message.content_type == 'text' and message.text == '/start'

def is_cancel_step(message):
    return message.content_type == 'text' and message.text == 'Отмена'

def start(message):
    bot.reply_to(message, "Привет! Я бот размещения Ваших объвлений в Telegram. У нас ты очень быстро найдешь автомобиль который ищешь, ну или продашь свой", reply_markup=start_keyboard)
    bot.register_next_step_handler(message, process_start_step)

def process_start_step(message):
    if is_cancel_step(message):
        bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    elif not is_start_step(message) and message.chat.id in users:
        if message.text == 'Добавить объявление':
            add_ad(message)
        elif message.text == 'Просмотреть объявления':
            view_ads(message)
    else:
        users.add(message.chat.id)
        start(message)

@bot.message_handler(commands=['start'])
def handle_start(message):
    start(message)

@bot.message_handler(func=lambda message: message.text == 'Добавить объявление')
def add_ad(message):
    bot.reply_to(message, "Введите марку автомобиля:", reply_markup=cancel_keyboard)
    bot.register_next_step_handler(message, process_brand_step, {})

def process_brand_step(message, ad):
    if is_cancel_step(message):
        bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    else:
        ad['brand'] = message.text
        bot.reply_to(message, "Введите модель автомобиля:", reply_markup=cancel_keyboard)
        bot.register_next_step_handler(message, process_model_step, ad)

def process_model_step(message, ad):
    if is_cancel_step(message):
        bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    else:
        ad['model'] = message.text
        bot.reply_to(message, "Введите год выпуска:", reply_markup=cancel_keyboard)
        bot.register_next_step_handler(message, process_year_step, ad)

def process_year_step(message, ad):
    if is_cancel_step(message):
        bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    else:
        try:
            ad['year'] = int(message.text)
            bot.reply_to(message, "Введите цену:", reply_markup=cancel_keyboard)
            bot.register_next_step_handler(message, process_price_step, ad)
        except ValueError:
            bot.reply_to(message, "Некорректный год. Попробуйте еще раз.", reply_markup=cancel_keyboard)
            bot.register_next_step_handler(message, process_year_step, ad)

def process_price_step(message, ad):
    if is_cancel_step(message):
        bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    else:
        try:
            ad['price'] = int(message.text)
            bot.reply_to(message, "Введите ссылку на объявление:", reply_markup=cancel_keyboard)
            bot.register_next_step_handler(message, process_link_step, ad)
        except ValueError:
            bot.reply_to(message, "Некорректная цена. Попробуйте еще раз.", reply_markup=cancel_keyboard)
            bot.register_next_step_handler(message, process_price_step, ad)

def process_link_step(message, ad):
    if is_cancel_step(message):
        bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    else:
        if message.text.startswith('http'):
            ad['link'] = message.text
            ad['timestamp'] = int(time.mktime(datetime.now().timetuple()))
            conn = sqlite3.connect('ads.db')
            c = conn.cursor()
            c.execute("PRAGMA table_info(ads)")
            columns = c.fetchall()
            if not any(column[1] == 'timestamp' for column in columns):
                c.execute("ALTER TABLE ads ADD COLUMN timestamp INTEGER")
            c.execute("INSERT INTO ads (brand, model, year, price, link, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                      (ad['brand'], ad['model'], ad['year'], ad['price'], ad['link'], ad['timestamp']))
            conn.commit()
            conn.close()
            bot.reply_to(message, "Объявление успешно добавлено!", reply_markup=start_keyboard)
        else:
            bot.reply_to(message, "Некорректная ссылка. Попробуйте еще раз или нажмите 'Отмена'.", reply_markup=cancel_keyboard)
            bot.register_next_step_handler(message, process_link_step, ad)

@bot.message_handler(func=lambda message: message.text == 'Просмотреть объявления')
def view_ads(message):
    conn = sqlite3.connect('ads.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT brand FROM ads")
    brands = [row[0] for row in c.fetchall()]
    conn.close()
    if len(brands) == 0:
        bot.reply_to(message, "Нет объявлений.", reply_markup=start_keyboard)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for brand in brands:
            markup.add(telebot.types.KeyboardButton(brand))
        markup.add(telebot.types.KeyboardButton('Отмена'))
        bot.reply_to(message, "Выберите марку автомобиля:", reply_markup=markup)
        bot.register_next_step_handler(message, process_view_brand_step)

def process_view_brand_step(message):
    if is_cancel_step(message):
        bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    else:
        brand = message.text
        conn = sqlite3.connect('ads.db')
        c = conn.cursor()
        c.execute("SELECT DISTINCT model FROM ads WHERE brand = ?", (brand,))
        models = [row[0] for row in c.fetchall()]
        conn.close()
        if len(models) == 0:
            bot.reply_to(message, "Нет объявлений для этой марки.", reply_markup=start_keyboard)
        else:
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            for model in models:
                markup.add(telebot.types.KeyboardButton(model))
            markup.add(telebot.types.KeyboardButton('Отмена'))
            bot.reply_to(message, "Выберите модель автомобиля:", reply_markup=markup)
            bot.register_next_step_handler(message, process_view_model_step, brand)

def process_view_model_step(message, brand):
    if is_cancel_step(message):
        bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    else:
        model = message.text
        conn = sqlite3.connect('ads.db')
        c = conn.cursor()
        c.execute("SELECT * FROM ads WHERE brand = ? AND model = ?", (brand, model))
        ads = c.fetchall()
        if len(ads) == 0:
            bot.reply_to(message, "Нет объявлений для этой марки и модели.", reply_markup=start_keyboard)
        else:
            for ad in ads:
                bot.send_message(message.chat.id, f"{ad[1]} {ad[2]} ({ad[3]} год) - {ad[4]} руб. {ad[5]}")
        conn.close()
        bot.register_next_step_handler(message, process_start_step)

@bot.message_handler(func=is_cancel_step)
def cancel(message):
    bot.reply_to(message, "Действие отменено.", reply_markup=start_keyboard)
    bot.register_next_step_handler(message, process_start_step)

def add_timestamp_column_if_not_exists(cursor):
    cursor.execute("PRAGMA table_info(ads)")
    columns = cursor.fetchall()
    if not any(column[1] == 'timestamp' for column in columns):
        cursor.execute("ALTER TABLE ads ADD COLUMN timestamp INTEGER")

def delete_old_ads():
    while True:
        conn = sqlite3.connect('ads.db')
        c = conn.cursor()
        add_timestamp_column_if_not_exists(c)
        c.execute("DELETE FROM ads WHERE timestamp < ?", (int(time.mktime((datetime.now() - timedelta(days=7)).timetuple())),))
        conn.commit()
        conn.close()
        time.sleep(86400)  # Проверка каждый день

if __name__ == '__main__':
    conn = sqlite3.connect('ads.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS ads (id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, model TEXT, year INTEGER, price INTEGER, link TEXT, timestamp INTEGER)")
    conn.commit()
    conn.close()

    users = set()

    import threading
    t = threading.Thread(target=delete_old_ads)
    t.start()
    bot.polling(none_stop=True)
