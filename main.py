import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import TOKEN1
import sqlite3
import logging

# homework_TG03_bot
bot = Bot(token=TOKEN1)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()


def init_db():
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    grade TEXT NOT NULL)
    ''')
    conn.commit()
    conn.close()


init_db()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Введи /add для добавления ученика или /list для просмотра списка")


@dp.message(Command('help'))
async def f_help(message: Message):
    await message.answer(
        "Бот умеет выполнять команды:\n/start\n/help\n/add\n/list")


@dp.message(Command('add'))
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Как тебя зовут?")
    await state.set_state(Form.name)


# Функция срабатывает, когда бот получает имя (пользователь заполнил поле формы)
@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    # В name сохраняем введённое пользователем имя (текст сообщения)
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    # Отправляем сообщение с ответом
    await state.set_state(Form.age)


@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("В каком ты классе?")
    await state.set_state(Form.grade)


@dp.message(Form.grade)
async def grade(message: Message, state: FSMContext):
    await state.update_data(grade=message.text)
    inp_data = await state.get_data()

    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''
    INSERT INTO students (name, age, grade) VALUES (?, ?, ?)''', (inp_data['name'], inp_data['age'], inp_data['grade']))
    conn.commit()
    conn.close()
    await message.answer("Данные записаны. Введите /add для добавления нового ученика или /list для просмотра списка")
    await state.clear()


# Команда /list
@dp.message(Command('list'))
async def list_students(message: types.Message):
    query = 'SELECT * FROM students ORDER BY grade ASC, name ASC'

    # Открываем соединение с базой данных и выполняем запрос
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    result = cur.execute(query)
    rows = result.fetchall()
    # cursor.close()
    conn.close()

    # Формируем ответное сообщение
    response = 'Список учеников:\n\n'
    for row in rows:
        response += f'Имя: {row[1].ljust(8)}, Возраст: {str(row[2]).rjust(2)}, Класс: {row[3]}\n'

    # Отправляем сообщение пользователю
    await message.answer(response)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
