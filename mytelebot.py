from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from config_for_bot import tg_token
from config_for_db import db_name, user, password, host
from datetime import datetime
import emoji
import pymysql


bot = Bot(token=tg_token)
dp = Dispatcher(bot)


def welcome_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(name) for name in ['!Расписание']])
    return keyboard

# метод ANSWER принимает строку и возвращает готовый ответ с расписанием
def answer(string, a):
    time=datetime.now().time().strftime("%H:%M:%S")
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print(f"{time}: connection successful, search for the desired date...")
    except Exception as ex:
        print(f"{time}: connection failed")
        print(ex)
    with connection.cursor() as cursor:
        try:
            txt=""
            times=['8:00-9:20','9:30-10:50','11:00-12:20','12:40-14:00','14:10-15:30','15:40-17:00','17:05-18:25','18:30-19:50','19:55-21:15','21:20-22:40']
            # ЗАБРАТЬ ДАННЫЕ ПО ДАТЕ
            cursor.execute(f"SELECT * FROM `lessons` WHERE date = '{string}';")
            rows=cursor.fetchall()[0]
            for x in range(len(rows)-2):
                if rows[f'les{x+1}'] != '-':
                    txt=txt+(f"{emoji.emojize(':Ukraine:')} {x+1} пара (<u>{times[x]}</u>):\n <b>{rows[f'les{x+1}']}</b>\n\n")
            txt=txt+"\nОчистить клавиатуру /clear"
        except Exception as e:
            txt=f"{emoji.emojize(':cross_mark:')}Расписания по дате '{string}' - не найдено\nВозможно дата указана неверно\nили расписания еще нет\n\n /help\n\n /clear"
            print(f"\tError: {e}") 
            print(f"\t{a} написал: '{string}'")
        connection.close()
        
        print(f"{time}: disconnect.")
    return txt
    
# ответ на команду "старт"
@dp.message_handler(commands=["start"])
async def start_message(message: types.Message):
    await message.reply("Бот для расписания пар группы КН б-11\nвведите /help для подробной информации.", reply_markup=welcome_keyboard())


# ответ на команду "хелп"
@dp.message_handler(commands=['help'])
async def answer_message(message: types.Message):
    await message.answer("Для просмотра расписания пар Нажмите кнопку \"Расписание\" и выберите дату", reply_markup=welcome_keyboard())


# ответ на команду "клир"
@dp.message_handler(commands=['clear'])
async def answer_message(message: types.Message):
    await message.reply(f"{emoji.emojize(':broom:')} Чисто!", reply_markup=welcome_keyboard())


# ответ на команду "Расписание"
@dp.message_handler(commands=['Расписание'],commands_prefix='!/')
async def answer_message(message: types.Message):
    time=datetime.now().time().strftime("%H:%M:%S")
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    buttons=[]
    try: # подкл к бд
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print(f"{time}: connection successful")
    except Exception as ex:
        print(f"{time}: connection failed")
        print(ex)
    # достаем все ключи из словаря в список buttons
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM `lessons`")
        rows=cursor.fetchall()
        for row in rows:
            buttons.append(row['date'])
        # создаем сразу все кнопки с датой
    keyboard.add(*buttons)
    connection.close() # отключаемся от бд
    print(f"{time}: disconnect")
    await message.answer("Выберите дату.", reply_markup=keyboard)


# ответ на любое входящее ТЕКСТОВОЕ сообщение 
@dp.message_handler()
async def reply_message(message: types.Message):
    try:
        txt=answer(message.text,message.from_user.first_name)
        await message.reply(txt, types.ParseMode.HTML)
    except Exception as e:
        await message.reply("Что-то пошло не так(")
        print(e)


@dp.message_handler(content_types=['sticker'])
async def sticker_answer(message: types.Message):
    await message.answer_sticker('CAACAgIAAxkBAAEELTBiMc_vxpSRoFQE1fefuxqPQ7O26gACDRUAAoj0kUloCF-tcpbaKCME')


# это до конца хз зачем но по приколу пусть будет
if __name__ == "__main__": 
    executor.start_polling(dp, skip_updates=True)