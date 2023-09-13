import telebot
import json
import threading
import time
import schedule
import os
import random

from telebot import types
from datetime import datetime, timedelta


BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
bot = telebot.TeleBot(BOT_TOKEN)

# Время ожидания перед удалением пользователя из бара (в секундах)
WAIT_TIME_SECONDS = 30
WAIT_TIME_SCHEDULE_EVERY = 0.1
second_delete_gift = 600 # 5 минут

# Проверка наличия файла с данными о людях в баре
if not os.path.isfile('people_in_bar.json'):
    with open('people_in_bar.json', 'w') as file:
        json.dump([], file)

# Запланированная задача для удаления пользователей из бара
def remove_users_from_bar():
    current_time = time.time()
    users_to_remove = []
    
    with open('people_in_bar.json', 'r') as file:
        data = json.load(file)

    for user in data:
        user_id = user["id"]
        join_time = user["join_time"]
        if current_time - join_time >= WAIT_TIME_SECONDS:
            users_to_remove.append(user_id)

    for user_id in users_to_remove:
        #bot.send_message(user_id, "Вы покинули бар. Нажмите 'Я в баре', чтобы вернуться.")
        bot.send_message(user_id, "Вы всё ещё в баре?\nЕсли да, то нажмите 'Я в баре'\nИ прокрутите колесо фортуны!")
        data = [user for user in data if user["id"] != user_id]

    with open('people_in_bar.json', 'w') as file:
        json.dump(data, file, indent=4)

# Планирование задачи на выполнение каждую минуту
schedule.every(WAIT_TIME_SCHEDULE_EVERY).minutes.do(remove_users_from_bar)

# Запуск планировщика в отдельном потоке
def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=schedule_thread)
scheduler_thread.daemon = True
scheduler_thread.start()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # Отправляем приветственное сообщение и инструкцию
    bot.send_message(message.chat.id, "Я бот бара ...\nДля того, чтобы узнать, кто сейчас в баре, нажми 'Кто вы баре?'\nЧтобы попытать удачу и выиграть приз 🎁, нажми 'Я в баре', если ты в нём!\nПризм можно получить в течении 5 минту🕐, потом он проадёт!", reply_markup=send_keyboard())
    print(message.chat.id)

# Отправка клавиатуры с кнопками
def send_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    item1 = telebot.types.KeyboardButton("Я в баре")
    item2 = telebot.types.KeyboardButton("Кто в баре?")
    markup.add(item1, item2)
    #bot.send_message(chat_id, "", reply_markup=markup)
    return markup

# Функция для добавления человека в бар и сохранения информации в файл
def add_person_to_bar(user_id, username, full_name):
    current_time = time.time()
    with open('people_in_bar.json', 'r') as file:
        data = json.load(file)

    # Проверка наличия пользователя в баре
    user_exists = any(user["id"] == user_id for user in data)

    if not user_exists:
        # Добавление информации о человеке в бар
        new_person = {
            "id": user_id,
            "username": username,
            "full_name": full_name,
            "join_time": current_time
        }
        data.append(new_person)

        # Сохранение данных в файл
        with open('people_in_bar.json', 'w') as file:
            json.dump(data, file, indent=4)

        return True
    else:
        return False

# Обработчик кнопки "Я в баре"
@bot.message_handler(func=lambda message: message.text == "Я в баре")
def i_am_in_the_bar(message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.first_name + " " + message.from_user.last_name if message.from_user.last_name else message.from_user.first_name

    added = add_person_to_bar(user_id, username, full_name)

    if added:
        bot.send_message(message.chat.id, f"{full_name} (@{username}) добавлен(а) в бар!", reply_markup=send_keyboard())
        start_roulette(message)
    else:
        bot.send_message(message.chat.id, "Вы уже в баре!", reply_markup=send_keyboard())

    # Отправляем клавиатуру снова
    #send_keyboard(message.chat.id)

# Обработчик кнопки "Кто в баре?"
@bot.message_handler(func=lambda message: message.text == "Кто в баре?")
def who_is_in_the_bar(message):
    with open('people_in_bar.json', 'r') as file:
        data = json.load(file)

    response = "Люди в баре:\n"
    for user in data:
        response += f"{user['full_name']} (@{user['username']})\n"
    bot.send_message(message.chat.id, response)

# Создаем список элементов рулетки
gift_dict = {
    'Вода' : {
        'ratio' : 90
    },
    'Комплимент от бармена' : {
        'ratio' : 50
    },
    'Скидка 5%' : {
        'ratio' : 20
    },
    'Скидка на шампанское 10%' : {
        'ratio' : 1
    },
    'Коньяк' : {
        'ratio' : 0.01
    },  
    'Возможность выйти' : {
        'ratio' : 0.0005
    },
}


def get_gift_list(k_len=10):
    # Создаем список с элементами на основе вероятностей
    gift_list = []
    weights = [info['ratio'] for info in gift_dict.values()]
    gift_list = list(gift_dict.keys())

    # Выбираем 10 элементов из списка с учетом вероятностей
    selected_gifts = random.choices(gift_list, weights=weights, k=k_len)

    return selected_gifts


# Функция для запуска рулетки
def start_roulette(message, roulette_elements=get_gift_list()):
    chat_id = message.chat.id
    loading_messages = []
    time_sleep = 0.3
    for i, element in enumerate(roulette_elements):
        # Отправляем новое сообщение с элементом рулетки
        loading_message = bot.send_message(chat_id, f"Крутим рулетку... > {element}", disable_notification=True)
        loading_messages.append(loading_message)

        while len(loading_messages) > 3:
            bot.delete_message(chat_id, loading_messages[0].message_id)
            loading_messages.pop(0)
        
        # Задержка между сообщениями (можно изменить)
        time.sleep(time_sleep)
        time_sleep += 0.05

    # Отправляем сообщение с результатом
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Получить приз!", callback_data=f"1|{message.from_user.username}|{roulette_elements[-2]}")
    keyboard.add(button)
    result_message = bot.send_message(chat_id, f"Вы выйграли: {roulette_elements[-2]}  🎁 \nУ вас есть 5 минут на получения подарка!", reply_markup=keyboard)
    add_delete_message(result_message, second_delete_gift)

    time.sleep(2)
    # Удаляем сообщения из барабана
    for loading_message in loading_messages:     
        bot.delete_message(chat_id, loading_message.message_id)     
        time.sleep(0.5)                        

@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    data = call.data.split('|')
    if data[0] == '1':
        bot.send_message(ADMIN_ID, f"@{data[1]} выиграл '{data[2]}'")
        bot.send_message(call.message.chat.id, "Подойдите к бармену!")
        bot.delete_message(call.message.chat.id, call.message.message_id)    
        #add_delete_message(call.message, 1) 
        if messages_to_delete[(call.message.chat.id, call.message.message_id)]:
            del messages_to_delete[(call.message.chat.id, call.message.message_id)]


# Обработчик команды /roulette
@bot.message_handler(commands=['roulette'])
def handle_roulette(message):
    start_roulette(message)

messages_to_delete = {}
def add_delete_message(message, seconds=600):
    # Получаем chat_id и message_id сообщения
    chat_id = message.chat.id
    message_id = message.message_id

    # Добавляем информацию о сообщении в словарь
    now = datetime.now()
    delete_time = now + timedelta(seconds=seconds)  # Пример: удалять через 30 секунд
    messages_to_delete[(chat_id, message_id)] = delete_time

# Функция для удаления сообщений
def delete_messages():
    while True:
        now = datetime.now()
        keys_to_delete = []
        for (chat_id, message_id), delete_time in messages_to_delete.items():
            if now >= delete_time:
                try:
                    bot.delete_message(chat_id=chat_id, message_id=message_id)
                    keys_to_delete.append((chat_id, message_id))
                except telebot.apihelper.ApiException as e:
                    print(f"Ошибка при удалении сообщения: {e}")

        # Удаляем информацию о сообщениях, которые были удалены
        for key in keys_to_delete:
            del messages_to_delete[key]

        # Ждем 1 секунду перед следующей проверкой
        time.sleep(1)

# Запускаем поток для удаления сообщений
delete_thread = threading.Thread(target=delete_messages)
delete_thread.daemon = True
delete_thread.start()

# Запуск бота
while True:
    try:    
        bot.polling()
    except Exception as e:
        print(f'Ошибка: {e}')
