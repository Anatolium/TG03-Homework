import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
# Конечный автомат FSM (Finite State Machine) служит для обработки последовательных шагов взаимодействия с пользователем
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN, WEATHER_API_KEY
import sqlite3
import aiohttp
import logging

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Класс Form используется для определения состояний конечного автомата, а не для создания объектов
# Состояния используются непосредственно в конечном автомате
class Form(StatesGroup):
    # Объекты класса State, представляющие собой различные состояния, через которые будет проходить бот
    # по мере взаимодействия с пользователем
    # Объект класса State – это единичное состояние, используемое в конечном автомате для обработки
    # различных шагов взаимодействия с пользователем
    name = State()
    age = State()
    city = State()


def init_db():
    conn = sqlite3.connect('user_data.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    city TEXT NOT NULL)
    ''')
    conn.commit()
    conn.close()


init_db()


# FSMContext – контекст состояния конечного автомата
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Как тебя зовут?")
    # Устанавливает текущее состояние конечного автомата в 'Form.name', что означает, что следующий обработчик будет
    # ожидать ответ на вопрос, связанный с этим состоянием
    await state.set_state(Form.name)

# Декоратор, указывающий, что функция будет вызвана при получении сообщения, когда бот находится в состоянии 'Form.name'
# Функция name() служит для обработки этого состояния
# Функция срабатывает, когда бот получает имя (пользователь заполнил поле формы)
@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    # Сохранение введенного пользователем имени в состоянии
    # В name сохраняем введённое пользователем имя (текст сообщения)
    await state.update_data(name=message.text)
    # Отправка следующего вопроса пользователю
    await message.answer("Сколько тебе лет?")
    # Установка следующего состояния 'Form.age'
    # Отправляем сообщение с ответом
    await state.set_state(Form.age)

# Декоратор для состояния 'Form.age'
@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    # Сохранение введенного возраста
    await state.update_data(age=message.text)
    await message.answer("Из какого ты города?")
    # Установка следующего состояния 'Form.city'
    await state.set_state(Form.city)

# Декоратор для состояния 'Form.city'
@dp.message(Form.city)
async def city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    user_data = await state.get_data()

    conn = sqlite3.connect('user_data.db')
    cur = conn.cursor()
    cur.execute('''
    INSERT INTO users (name, age, city) VALUES (?, ?, ?)''', (user_data['name'], user_data['age'], user_data['city']))
    conn.commit()
    conn.close()

    # Создаем асинхронную сессию
    # Этот контекстный менеджер создает асинхронную сессию HTTP, которая будет использоваться для отправки запросов
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={user_data['city']}&appid={WEATHER_API_KEY}&"
            f"units=metric") as response:
            if response.status == 200:
                weather_data = await response.json()
                main_data = weather_data['main']
                temperature = main_data['temp']
                humidity = main_data['humidity']
                weather = weather_data['weather'][0]
                description = weather['description']

                weather_report = (f"Город - {user_data['city']}\n"
                                  f"Температура - {temperature}°\n"
                                  f"Влажность воздуха - {humidity}\n"
                                  f"Описание погоды - {description}")
                await message.answer(weather_report)
            else:
                await message.answer("Не удалось получить данные о погоде")
    # Очищаем состояния для завершения текущего шага диалога
    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
