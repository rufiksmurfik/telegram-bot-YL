import telebot
import sqlite3
from telebot import types
import random
import smtplib
from email.mime.text import MIMEText
import re
import datetime
import messages
import config
import time


def is_email(email):
    pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


SUBSCRIPE_PRICE = 100
API_TOKEN = config.BOT_TOKEN
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
services = ['Sber', 'Yandex', 'Eldorado']
bot.bot_pre_checkout_query = 60


def pay(message, price):
    print(price)
    price = types.LabeledPrice(label='Покупка подписки', amount=price * 100)
    bot.send_invoice(message.chat.id, title='премиум подписка',
                     description='покупка подписки на 30 дней',
                     provider_token=config.PAYMENTS_PROVIDER_TOKEN, currency='RUB',
                     photo_url='https://sun9-45.userapi.com/impg/-Z-7UPu8l2_BffCmk2AAOwO93RhctRV2o6P8fw/Db965YNvLKw.jpg?size=604x340&quality=96&sign=42d628d674878640cf4783e3778041d2&type=album',
                     prices=[price], start_parameter='start', need_email=True, invoice_payload='coupon')


@bot.message_handler(content_types=['successful_payment'])
def success(message):
    print(message.successful_payment.total_amount / 100)
    print("Payment successful!")
    user_id = message.chat.id
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    balnow = cur.execute(f"SELECT balance FROM users WHERE userid='{user_id}'").fetchone()[0]
    cur.execute(
        f"UPDATE users SET balance={round(balnow + message.successful_payment.total_amount / 100, 2)} WHERE userid='{user_id}'")
    db.commit()
    db.close()
    bot.send_message(message.chat.id,
                     f'Платеж на {message.successful_payment.total_amount / 100} {message.successful_payment.currency} проведен успешно!',
                     reply_markup=defaultmarkup)


@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


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
        print(f"Ошибка отправки email: {e}")

@bot.message_handler(commands=['admin_panel'])
def admin_panel(message):
    if str(message.from_user.id) == ADMIN_USER_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Управление пользователями'))
        markup.add(types.KeyboardButton('Статистика бота'))
        markup.add(types.KeyboardButton('Добавить админа'))
        markup.add(types.KeyboardButton('Удалить админа'))
        bot.send_message(message.chat.id, "Административная панель:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
# Обработчик для управления пользователями
@bot.message_handler(func=lambda message: message.text == 'Управление пользователями')
def manage_users(message):
    if str(message.from_user.id) == ADMIN_USER_ID:
        # Здесь код для управления пользователями
        bot.send_message(message.chat.id, "Функция управления пользователями еще не реализована.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")


@bot.message_handler(func=lambda message: message.text == 'Статистика бота')
def bot_statistics(message):
    if str(message.from_user.id) == ADMIN_USER_ID:
        bot.send_message(message.chat.id, "Функция просмотра статистики бота еще не реализована.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")


@bot.message_handler(func=lambda message: message.text == 'Добавить админа')
def add_admin(message):
    if str(message.from_user.id) == ADMIN_USER_ID:
        bot.send_message(message.chat.id, "Функция добавления админа еще не реализована.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

@bot.message_handler(func=lambda message: message.text == 'Удалить админа')
def remove_admin(message):
    if str(message.from_user.id) == ADMIN_USER_ID:
        bot.send_message(message.chat.id, "Функция удаления админа еще не реализована.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'buy_yes':
        db = sqlite3.connect("promocodes.db")
        cur = db.cursor()
        print(call.from_user.id)
        balance = round(cur.execute(f"SELECT balance FROM users WHERE userid={call.from_user.id}").fetchone()[0] - 100,
                        2)
        if balance < 0:
            bot.send_message(call.message.chat.id, "багоюзер")
            return
        print(balance)
        cur.execute(
            f"UPDATE users SET balance={balance}, usertype='sub', subscribedtill='{datetime.datetime.now() + datetime.timedelta(days=30)}' WHERE userid={call.from_user.id}")
        db.commit()
        db.close()
        bot.send_message(call.message.chat.id, "Вы приобрели подписку!") #ыф
    elif call.data == 'buy_no':
        bot.send_message(call.message.chat.id, "Вы отказались от подписки")
    elif "admin_down_" in call.data:
        print(call.data)
        db = sqlite3.connect("promocodes.db")
        cur = db.cursor()
        cur.execute(f"UPDATE users SET usertype='user' WHERE userid='{call.data.split('_')[-1]}'")
        db.commit()
        db.close()
        bot.send_message(call.message.chat.id, "админ успешно унижен", reply_markup=defaultmarkup)
    elif call.data == "pop_up":
        msg = bot.send_message(call.message.chat.id, "введите сумму пополнения")
        bot.register_next_step_handler(msg, lambda m: pay(msg, int(m.text)))
    elif "admin_" in call.data:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("УНИЗИТЬ", callback_data="admin_down_" + call.data.split("_")[-1]))
        bot.send_message(call.message.chat.id, "выберите действие для админа " + str(
            bot.get_chat_member(call.data.split("_")[-1], call.data.split("_")[-1]).user.username), reply_markup=markup)


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
    admins = [str(i[0]) for i in
              cur.execute("SELECT userid FROM users WHERE usertype='admin' or usertype='gladmin'").fetchall()]
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
        bot.send_message(message.chat.id, "Извините, только администратор может добавлять промокоды.",
                         reply_markup=defaultmarkup)


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
    serviceprom = [int(i[0]) for i in
                   cur.execute(f"SELECT servicenum FROM promos WHERE promo='{promo_code}'").fetchall()]
    if services.index(service) in serviceprom:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        bot.send_message(message.chat.id, "такой промокод уже есть", reply_markup=defaultmarkup)
    else:
        cur.execute(
            f"INSERT INTO promos (servicenum, promo, creatorId) VALUES({services.index(service)}, '{promo_code}', '{str(message.from_user.id)}')")
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
        bot.register_next_step_handler(message, lambda m: show_promos(m, services.index(
            m.text) if m.text in services else m.text))
    else:
        bot.send_message(message.chat.id, "Чтобы просматривать промокоды, купите подписку!", reply_markup=defaultmarkup)


def show_promos(message, servicetype):
    print(servicetype)
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    ustype = cur.execute(f"SELECT usertype FROM users WHERE userid={message.from_user.id}").fetchone()[0]
    if servicetype == 'All':
        promos = cur.execute("SELECT promo, servicenum, creatorId FROM promos").fetchall()
        promo_list = "ДОСТУПНЫЕ ПРОМОКОДЫ:\n" + "\n".join([
            f"<b>{key}:</b>{services[value[1]]} <code>{value[0]}</code>, " + (
                f"<a href='tg://user?id={value[2]}'>добавил промокод:</a>" if "dmin" in ustype else "")
            for key, value in enumerate(promos, start=1)])

    else:
        promos = cur.execute(
            f"SELECT promo, servicenum, creatorId FROM promos where servicenum={servicetype}").fetchall()
        promo_list = f"ПРОМО ДЛЯ СЕРВИСА {services[servicetype]}:\n" + "\n".join([
            f"<b>{key}:</b> <code>{value[0]}</code>, " + (
                f"<a href='tg://user?id={value[2]}'>добавил промокод:</a>" if "dmin" in ustype else "")
            for key, value in enumerate(promos, start=1)])

    db.close()
    bot.send_message(message.chat.id, promo_list, parse_mode='HTML', reply_markup=defaultmarkup)


@bot.message_handler(commands=['my_profile'])
def my_profile(message):
    db = sqlite3.connect("promocodes.db")
    cur = db.cursor()
    usertype, email, balance = cur.execute(
        f"SELECT usertype, email, balance FROM users WHERE userid={message.from_user.id}").fetchone()
    print(email, balance, usertype)
    profile_info = f"<b>Профиль:</b>\n\n" \
                   f"<b>Имя:</b> {message.from_user.first_name}\n" \
                   f"<b>Email:</b> {email}\n" \
                   f"<b>Баланс:</b> {balance} руб.\n" \
                   f"<b>Ваша масть:</b> {usertype}"
    bot.send_message(message.chat.id, profile_info, parse_mode='HTML', reply_markup=defaultmarkup)


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
        msg = bot.reply_to(message, "Это не является почтой, введите вашу реальную почту")
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
    usertype, balance, sub_till = cur.execute(
        "SELECT usertype, balance, subscribedtill FROM users WHERE userid=" + str(message.from_user.id)).fetchone()
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
                bot.send_message(message.chat.id,
                                 f"Ваш баланс: {balance} руб\nПодписка стоит {SUBSCRIPE_PRICE} руб.\nУ вас нет активной подписки, но достаточно денег, чтобы ее приобрести. Желаете приобрести подписку?",
                                 reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Пополнить баланс', callback_data='pop_up'))
                bot.send_message(message.chat.id,
                                 f"Ваш баланс: {balance} руб\nПодписка стоит {SUBSCRIPE_PRICE} руб.\nУ вас нет активной подписки и недостаточно денег, чтобы ее приобрести.",
                                 reply_markup=markup)
        case "sub":
            bot.send_message(message.chat.id,
                             f"У вас есть подписка, она активна до {sub_till.date()} (еще {(sub_till.date() - datetime.date.today()).days} дней)",
                             reply_markup=defaultmarkup)
        case "admin":
            bot.send_message(message.chat.id, f"вы админ, зачем сюда заходить...", reply_markup=defaultmarkup)
        case "gladmin":
            db = sqlite3.connect("promocodes.db")
            cur = db.cursor()
            admins = [bot.get_chat_member(i[0], i[0]).user.username for i in
                      cur.execute("SELECT userid FROM users WHERE usertype='admin'").fetchall()]
            adminsids = [i[0] for i in cur.execute("SELECT userid FROM users WHERE usertype='admin'").fetchall()]
            db.close()
            markup = types.InlineKeyboardMarkup(row_width=len(admins))
            for admin in range(len(admins)):
                markup.add(types.InlineKeyboardButton(admins[admin], callback_data="admin_" + str(adminsids[admin])))
            bot.send_message(message.chat.id, "Список администрации", reply_markup=markup)


bot.polling()
