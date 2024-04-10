import telebot
import sqlite3
from telebot import types
import random
import smtplib
from email.mime.text import MIMEText
import re
import datetime

def is_email(email):
    # Регулярное выражение для проверки email
    pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
SUBSCRIPE_PRICE = 100
API_TOKEN = '7162305379:AAEHpA2d1PBqHTrakBF1-YGs7ibq3HhSiFw'
ADMIN_USER_ID = '1369331889'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'ivanberat81@gmail.com'
EMAIL_HOST_PASSWORD = 'dhwk tuco xgof zosf'
defaultmarkup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
defaultmarkup.add(types.KeyboardButton('Добавить промокод'))
defaultmarkup.add(types.KeyboardButton('Показать промокоды'))
defaultmarkup.add(types.KeyboardButton('Мой профиль'))
defaultmarkup.add(types.KeyboardButton('Подписка'))
bot = telebot.TeleBot(API_TOKEN)
promo_codes = []
users_profiles = {}
verification_codes = {}
services = ['Sber',  'Yandex', 'Eldorado']


def isOutdated(dt):
    return datetime.datetime.now() > datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S.%f")


def send_verification_email(email, code):
    msg = MIMEText(f'Добрый день!'
                   f' Вы хотите зарегистрироваться в нашем телеграм-боте по выдаче промокодов.'
                   f' Ваш код подтверждения: {code}')
    msg['Subject'] = 'Код подтверждения для Telegram бота'
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = email
    try:
        server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, [email], msg.as_string())
        server.quit()
    except smtplib.SMTPException as e:
        print(f"An error occurred: {e}")



@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'buy_yes':
        db = sqlite3.connect("promocodes.db")
        cur = db.cursor()
        print(call.from_user.id)
        balance = round(cur.execute(f"SELECT balance FROM users WHERE userid={call.from_user.id}").fetchone()[0] - 100, 2)
        if balance < 0:
            bot.send_message(call.message.chat.id, "нахуй пошел, багоюзер")
            return
        print(balance)
        cur.execute(f"UPDATE users SET balance={balance}, usertype='sub', subscribedtill='{datetime.datetime.now() + datetime.timedelta(days=30)}' WHERE userid={call.from_user.id}")
        db.commit()
        db.close()
        bot.send_message(call.message.chat.id, "Вы приобрели подписку!")
    elif call.data == 'buy_no':
        bot.send_message(call.message.chat.id, "Вы отказались от подписки")


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    us = cur.execute(f"SELECT * FROM users WHERE userid='{str(message.from_user.id)}'").fetchone()
    if not us:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.InlineKeyboardButton('Верифицировать email', callback_data='set_email'))
        bot.send_message(message.chat.id, "Добро пожаловать! Установите email для пользования ботом.",
                         reply_markup=markup)
        bot.register_next_step_handler(message, lambda m: set_email(m))
        return ""
    us = list(us)
    print(us)
    if us[2] == "sub" and isOutdated(us[5]):
        us[2] = "user"
        cur.execute(f"UPDATE users SET usertype = 'user' WHERE userid = '{message.from_user.id}'")
        db.commit()
    db.close()
    print(message.text)
    if message.text == 'Добавить промокод':
        add_promo(message)
    elif message.text == 'Показать промокоды':
        ask_show_promos(message)
    elif message.text == 'Мой профиль':
        my_profile(message)
    elif message.text == 'Подписка':
        subscribe_settings(message)
    elif message.text == '/start':
        bot.send_message(message.chat.id, "Привет! Я бот для управления промокодами.", reply_markup=defaultmarkup)
    else:
        bot.send_message(message.chat.id, "Используйте кнопки для навигации", reply_markup=defaultmarkup)

def add_promo(message):
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    admins = [str(i[0]) for i in cur.execute("SELECT userid FROM users WHERE usertype='admin'").fetchall()]
    print(admins)
    db.close()
    if str(message.from_user.id) in admins:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('Sber'))
        markup.add(types.KeyboardButton('Yandex'))
        markup.add(types.KeyboardButton('Eldorado'))
        bot.send_message(message.chat.id, "Выберите сервис:", reply_markup=markup)
        bot.register_next_step_handler(message, process_service_choice)
    else:
        bot.reply_to(message, "Извините, только администратор может добавлять промокоды.")

def process_service_choice(message):
    if message.text in services:
        msg = bot.reply_to(message, f"Введите промокод для {message.text}:")
        bot.register_next_step_handler(msg, lambda m: process_promo_code(m, message.text))
    else:
        bot.reply_to(message, "Пожалуйста, выберите один из предложенных сервисов.")

def process_promo_code(message, service):
    promo_code = message.text
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    serviceprom = [int(i[0]) for i in cur.execute(f"SELECT servicenum FROM promos WHERE promo='{promo_code}'").fetchall()]
    if services.index(service) in serviceprom:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        bot.send_message(message.chat.id, "такой промокод уже есть", reply_markup=defaultmarkup)
    else:
        cur.execute(f"INSERT INTO promos (servicenum, promo, creatorId) VALUES({services.index(service)}, '{promo_code}', '{str(message.from_user.id)}')")
        db.commit()
        db.close()
        bot.send_message(message.chat.id, "Промокод добавлен!", reply_markup=defaultmarkup)


def ask_show_promos(message):
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    usertype = cur.execute(f"SELECT usertype FROM users WHERE userid={message.from_user.id}").fetchone()[0]
    db.close()
    if usertype != "user":
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        buttons = [types.KeyboardButton(service) for service in services]
        buttons.append(types.KeyboardButton("All"))
        markup.add(*buttons)
        bot.send_message(message.chat.id, "Выберите сервис:", reply_markup=markup)
        bot.register_next_step_handler(message, lambda m: show_promos(m, services.index(m.text) if m.text in services else m.text))
    else:
        bot.send_message(message.chat.id, "Чтобы просматривать промокоды, купите подписку!", reply_markup=defaultmarkup)


def show_promos(message, servicetype):
    print(servicetype)
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    ustype = cur.execute(f"SELECT usertype FROM users WHERE userid")
    if servicetype == 'All':
        promos = cur.execute("SELECT promo, servicenum, creatorId FROM promos").fetchall()
        promo_list = "СПИСОК ДОСТУПНЫХ ПРОМОКОДОВ:\n" + "\n".join([
                                   f"<b>{key}:</b>{services[value[1]]} <code>{value[0]}</code>, <a href='tg://user?id={value[2]}'>добавил промо</a>"
                                   for key, value in enumerate(promos, start=1)])

    else:
        promos = cur.execute(f"SELECT promo, servicenum, creatorId FROM promos where servicenum={servicetype}").fetchall()
        promo_list = f"ПРОМО ДЛЯ СЕРВИСА {services[servicetype]}:\n" + "\n".join([
                                   f"<b>{key}:</b> <code>{value[0]}</code>, <a href='tg://user?id={value[2]}'>добавил промо</a>"
                                   for key, value in enumerate(promos, start=1)])

    db.close()
    bot.send_message(message.chat.id, promo_list, parse_mode='HTML', reply_markup=defaultmarkup)


@bot.message_handler(commands=['my_profile'])
def my_profile(message):
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    usertype, email, balance = cur.execute(f"SELECT usertype, email, balance FROM users WHERE userid={message.from_user.id}").fetchone()
    print(email, balance, usertype)
    profile_info = f"<b>Профиль:</b>\n\n" \
                   f"<b>Имя:</b> {message.from_user.first_name}\n" \
                   f"<b>Email:</b> {email}\n" \
                   f"<b>Баланс:</b> {balance} руб.\n" \
                   f"<b>Ваша масть:</b> {usertype}"
    bot.send_message(message.chat.id, profile_info, parse_mode='HTML', reply_markup=defaultmarkup   )




def set_name(message):
    msg = bot.reply_to(message, "Введите ваше имя:")
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    user_id = message.from_user.id
    users_profiles[user_id]['name'] = message.text
    bot.reply_to(message, "Имя сохранено!")

def set_email(message):
    msg = bot.reply_to(message, "Введите ваш email:")
    bot.register_next_step_handler(msg, process_email_step)

def process_email_step(message):
    user_id = message.from_user.id
    email = message.text
    if is_email(email):
        code = random.randint(1000, 9999)
        verification_codes[user_id] = code
        send_verification_email(email, code)
        msg = bot.reply_to(message, "Мы отправили код на вашу почту. Пожалуйста, введите его здесь для подтверждения:")
        bot.register_next_step_handler(msg, lambda m: verify_email(m, email))
    else:
        msg = bot.reply_to(message, "не является email")
        bot.register_next_step_handler(msg, process_email_step)

def verify_email(message, email):
    user_id = message.from_user.id
    code = message.text
    if not code.isdigit():
        msg = bot.reply_to(message, "Пожалуйста, введите числовой код для подтверждения.")
        bot.register_next_step_handler(msg, lambda m: verify_email(m, email))
    elif verification_codes[user_id] == int(code):
        bot.send_message(message.chat.id, "Ваша почта подтверждена!", reply_markup=defaultmarkup)
        db = sqlite3.connect("promocodes.db")
        cur = db.cursor()
        cur.execute(f"INSERT INTO users (userid, email) VALUES('{str(message.from_user.id)}', '{email}')")
        db.commit()
        db.close()
    else:
        msg = bot.reply_to(message, "Неверный код, попробуйте еще раз.")
        bot.register_next_step_handler(msg, lambda m: verify_email(m, email))


def subscribe_settings(message):
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    usertype, balance, sub_till = cur.execute("SELECT usertype, balance, subscribedtill FROM users WHERE userid=" + str(message.from_user.id)).fetchone()
    print(usertype, balance)
    balance = float(balance)
    sub_till = datetime.datetime.strptime(sub_till, "%Y-%m-%d %H:%M:%S.%f")
    db.close()
    match usertype:
        case "user":
            if balance > SUBSCRIPE_PRICE:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Да', callback_data='buy_yes'))
                markup.add(types.InlineKeyboardButton('Нет', callback_data='buy_no'))
                bot.send_message(message.chat.id, f"Ваш баланс: {balance} руб\nПодписка стоит {SUBSCRIPE_PRICE} руб.\nУ вас нет активной подписки, но достаточно денег, чтобы ее приобрести. Желаете приобрести подписку?", reply_markup=markup)
            else:
                bot.send_message(message.chat.id,
                                 f"Ваш баланс: {balance} руб\nПодписка стоит {SUBSCRIPE_PRICE} руб.\nУ вас нет активной подписки и недостаточно денег, чтобы ее приобрести.", reply_markup=defaultmarkup)
        case "sub":
            bot.send_message(message.chat.id, f"У вас есть подписка, она активна до {sub_till.date()} (еще {(sub_till.date() - datetime.date.today()).days} дней)", reply_markup=defaultmarkup)
        case "admin":
            bot.send_message(message.chat.id, f"вы админ, зачем сюда заходить...", reply_markup=defaultmarkup)


bot.polling()