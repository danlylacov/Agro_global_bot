import telebot
from telebot import types
import psycopg2
from ymaps import StaticClient

conn = psycopg2.connect(dbname='profibot', user='postgres',
                        password='74244678', host='localhost')
cursor = conn.cursor()

token = '6042670909:AAFHea06klIh1KFLAMUuiavQqv69QOImcMQ'
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.id == 216720947:
        print('ewc')
        data = []
        while True:
            try:
                cursor.execute('SELECT * FROM publish')
                s = 0
                for row in cursor:
                    id = row[0]
                    if id not in data:
                        data.append(id)
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        btn1 = types.KeyboardButton("показать все фермы на карте")
                        markup.add(btn1)
                        try:
                            bot.send_location(message.chat.id, (str(row[3]).split()[0]), (str(row[3]).split()[1]))
                            bot.send_video(message.chat.id, row[2], caption=str(row[-1]) + '\n@' + str(row[1]))
                            bot.send_message(message.chat.id, '------------------------------------------',
                                             reply_markup=markup)
                        except:
                            pass
                        print(row[2])
                        # print(row)
            except:
                pass

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("зарегистрироваться как фермер")
    btn2 = types.KeyboardButton("отправить заявку на размещение фермы")
    markup.add(btn1, btn2)

    postgres_insert_query = """ INSERT INTO users (id, name, tel)
                                                       VALUES (%s,%s,%s)"""
    record_to_insert = (str(message.chat.id), str(message.chat.first_name), '0')
    cursor.execute(postgres_insert_query, record_to_insert)
    conn.commit()
    bot.send_message(message.chat.id,
                     "Привет, " + str(message.chat.first_name) + " ✌! Вы зарегистрировались в боте!",
                     reply_markup=markup)


@bot.message_handler(content_types="text")
def main(message):
    if message.text == 'зарегистрироваться как фермер':
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        reg_button = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
        keyboard.add(reg_button)
        nomer = bot.send_message(message.chat.id,
                                 'Оставьте ваш контактный номер чтобы наш менеджер смог связаться с вами.',
                                 reply_markup=keyboard)

        bot.register_next_step_handler(nomer, phone)

    if message.text == "отправить заявку на размещение фермы":
        postgres_insert_query = """ INSERT INTO publish (id, photos, video)
                                                               VALUES (%s,%s,%s)"""
        record_to_insert = (str(message.chat.id), str(message.chat.username), '0')

        cursor.execute(postgres_insert_query, record_to_insert)
        conn.commit()
        a = bot.send_message(message.chat.id, "Отправьте видео фермы")
        bot.register_next_step_handler(a, send_text)

    if message.text == "показать все фермы на карте":
        cursor.execute('SELECT geo FROM publish')
        geos = []
        for row in cursor:
            geos.append(row[0].split()[0] + ',' + row[0].split()[1] + ',1')

        print('fdf  ', geos)

        client = StaticClient()
        response = client.getimage([float(geos[0].split(',')[0]), float(geos[0].split(',')[1])], size=[450, 450],
                                   pt=geos)
        with open('file.png', "wb") as f:
            bot.send_photo(message.chat.id, photo=response)


@bot.message_handler(content_types=['contact'])
def phone(message):
    postgres_insert_query = """ UPDATE users SET tel = %s
                                               where id = %s"""

    record_to_insert = (str(message.contact.phone_number), str(message.chat.id))
    cursor.execute(postgres_insert_query, record_to_insert)
    conn.commit()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("зарегистрироваться как фермер")
    btn2 = types.KeyboardButton("отправить заявку на размещение фермы")
    markup.add(btn1, btn2)
    a = bot.send_message(message.chat.id, 'Вы зарегисторированы!', reply_markup=markup)
    bot.register_next_step_handler(a, main)


photo_list = []


@bot.message_handler(content_types=['video'])
def send_text(message):
    if message.text == '/done':
        bot.send_message(message.chat.id, 'Отправьте геолокацию фермы')
        bot.register_next_step_handler(message, get_geo)
        return
    else:
        postgres_insert_query = """UPDATE publish SET video = %s
                                               where id = %s"""
        record_to_insert = (str(message.video.file_id), str(message.chat.id))
        cursor.execute(postgres_insert_query, record_to_insert)
        conn.commit()
        # bot.send_video(message.chat.id, message.video.file_id)
        send = bot.send_message(message.from_user.id, "Отправьте ещё видео или нажмите /done")

        bot.register_next_step_handler(send, send_text)


@bot.message_handler(content_types=['location'])
def get_geo(message):
    if message.location is not None:
        postgres_insert_query = """UPDATE publish SET geo = %s
                                                       where id = %s"""
        record_to_insert = (
        str(message.location.longitude) + ' ' + str(message.location.latitude), str(message.chat.id))
        cursor.execute(postgres_insert_query, record_to_insert)
        conn.commit()
        print(message.location.longitude, message.location.latitude)
        bot.send_message(message.chat.id, 'Геолокация сохранена')
        bot.send_message(message.chat.id, 'Добавьте описание:')
        bot.register_next_step_handler(message, get_text)


@bot.message_handler(content_types=['text'])
def get_text(message):
    postgres_insert_query = """UPDATE publish SET deeeesc = %s
                                                           where id = %s"""
    record_to_insert = (str(message.text), str(message.chat.id))
    cursor.execute(postgres_insert_query, record_to_insert)
    conn.commit()
    print(message.text)
    bot.send_message(message.chat.id, 'Заявка отпралена на обработку!')


bot.polling()
