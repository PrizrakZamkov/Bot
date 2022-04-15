import asyncio
import json

from aiogram import Bot, types, Dispatcher, executor
# from auth_data import token
from parsing import get_data
from random import randint
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text, Command
from aiogram.utils.markdown import hbold, hlink
from auth_data import token

# bot = Bot(token="5330019151:AAFItAe6I30nsioD5dbpE2wqzV7Cek0yFQg", parse_mode=types.ParseMode.HTML)
bot = Bot(token=token, parse_mode=types.ParseMode.HTML)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

data = {}

free_jobs = []

i_am_worker = types.InlineKeyboardButton(
    text="Я ищу работу",
    callback_data="worker")
i_am_employer = types.InlineKeyboardButton(
    text="Я предлагаю работу",
    callback_data="employer")
start_menu = types.InlineKeyboardMarkup().row(i_am_worker, i_am_employer)

worker_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
worker_menu.add("Искать работу").row("Назад", "Устовить фильтры")

employer_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
employer_menu.add("Создать вакансию").row("Назад", "Мои вакансии")


def create_user(id):
    global data
    '''
        Создает пользователя с начальными параметрами
    '''
    data[id] = {
        "is_worker": True,
        "jobs": [],
        "filters": {
            "find": 0,
            "price_min": 0,
            "price_max": 1000000000,
            "remote": 0
        }
    }


def create_job_cart(job):
    return f"\U0001F58A {'Название:'}\n       {job['name']}" \
           f"\n\n\U0001F9FE	{'Описание:'}\n       {job['discription']}" \
           f"\n\n\U0001F4B5 {'Оплата:'}\n       {job['salary']} Руб" \
           f"\n\n\U0001F4CE {'Связь с работодателем:'}\n       {job['link']}"


@dp.message_handler(commands="start")
async def callback_start(message: types.Message):
    await bot.send_message(message.chat.id,
                           "Привет! Я sd_bot_1201. Я помогу тебе найти работу или работников по твоим запросам.",
                           reply_markup=start_menu)


@dp.message_handler(commands="menu")
async def callback_start(message: types.Message):
    if data[message.from_user.id]:
        await bot.send_message(message.chat.id, "", reply_markup=worker_menu)
    else:
        await bot.send_message(message.chat.id, "", reply_markup=employer_menu)


@dp.callback_query_handler(lambda c: c.data == 'worker')
async def callback(message: types.Message):
    if not (message.from_user.id in data):
        create_user(message.from_user.id)
    data[message.from_user.id]['is_worker'] = True
    with open('data_list.json', 'w') as data_list:
        json.dump(data, data_list, indent=4)
    await bot.send_message(
        chat_id=message.from_user.id,
        text="Приветствую соискатель",
        reply_markup=worker_menu
    )
    print(data)


@dp.callback_query_handler(lambda c: c.data == 'employer')
async def callback(message: types.Message):
    if not (message.from_user.id in data):
        create_user(message.from_user.id)
    data[message.from_user.id]['is_worker'] = False

    with open('data_list.json', 'w') as data_list:
        json.dump(data, data_list, indent=4)
    await bot.send_message(
        chat_id=message.from_user.id,
        text="Приветствую работодатель",
        reply_markup=employer_menu
    )
    print(data)


@dp.message_handler(Text(equals="Назад"))
async def get_data_projects(message: types.Message):
    await bot.send_message(message.chat.id,
                           "Привет! Я sd_bot_1201. Я помогу тебе найти работу или работников по твоим запросам.",
                           reply_markup=start_menu)


class FSMbot(StatesGroup):
    name = State()
    discription = State()
    salary = State()
    remote = State()
    tel = State()


@dp.message_handler(state="*", commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel(message: types.Message, state: FSMContext):
    curent_state = await state.get_state()
    if curent_state is None:
        return
    await state.finish()


@dp.message_handler(Text(equals="Создать вакансию"), state=None)
async def callback(message: types.Message):
    await FSMbot.name.set()
    await message.reply("Напишите название вакасии (напишите 'отмена' для прекращения создания вакансии)")


@dp.message_handler(state=FSMbot.name)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_job:
        new_job['name'] = message.text
    await FSMbot.next()
    await message.reply('Введите описание вакансии')


@dp.message_handler(state=FSMbot.discription)
async def load_discription(message: types.Message, state: FSMContext):
    async with state.proxy() as new_job:
        new_job['discription'] = message.text
    await FSMbot.next()
    await message.reply('Введите зарплату (Только целое число)')


@dp.message_handler(state=FSMbot.salary)
async def load_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as new_job:
            new_job['salary'] = int(message.text)
        await FSMbot.next()
        await message.reply('Возможна ли удаленная работа? (Да/Нет)')
    except Exception:
        await message.reply('Введите только целое число')


@dp.message_handler(state=FSMbot.remote)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_job:
        if message.text in ['Нет', 'Да']:
            new_job['remote'] = ['Нет', 'Да'].index(message.text)
            await FSMbot.next()
            await message.reply('Добавьте средство связи (ссылку на соцсеть / номер телефона)')
        else:
            await message.reply('Ответы только Да и Нет')


@dp.message_handler(state=FSMbot.tel)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_job:
        new_job['link'] = message.text
    await FSMbot.next()
    data[message.from_user.id]["jobs"].append(
        new_job._data  # {'name': '', 'discription': '', 'salary': 0, 'remote': '', 'link': ''}
    )
    with open('data_list.json', 'w') as data_list:
        json.dump(data, data_list, indent=4)
    print(new_job._data)
    await message.reply('Вакансия успешно создана')
    await message.reply(create_job_cart(data[message.from_user.id]["jobs"][-1]))
    await state.finish()


class FilterBot(StatesGroup):
    '''
        find:
            поиск работы
            0 - и бот и фриланс
            1 - только бот
            2 - только фриланс

        price_min и price_max:
            минимальная и максимальная желаемая оплата

        remote:
            удаленная ли работа
            0 - и удаленная и очная
            1 - только удаленная
            2 - только очная
    '''
    find = State()
    price_min = State()
    price_max = State()
    remote = State()


@dp.message_handler(state="*", commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel(message: types.Message, state: FSMContext):
    curent_state = await state.get_state()
    if curent_state is None:
        return
    await state.finish()


@dp.message_handler(Text(equals="Установить фильтры"), state=None)
async def callback(message: types.Message):
    await FilterBot.find.set()
    await message.reply("Где вы желаете искать работу?"
                        "0 - и бот и freelance.ru\n"
                        "1 - только бот\n"
                        "2 - только freelance.ru\n"
                        "(напишите 'отмена' для прекращения изменения фильтров)")


@dp.message_handler(state=FilterBot.find)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_filter:
        if message.text in ['0', '1', '2']:
            new_filter['find'] = int(message.text)
            await FilterBot.next()
            await message.reply('Введите минимальную оплату')
        else:
            await message.reply('Ввод только от 0 до 2')


@dp.message_handler(state=FilterBot.price_min)
async def load_discription(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as new_filter:
            new_filter['discription'] = int(message.text)
        await FilterBot.next()
        await message.reply('Введите максимальную оплату')
    except Exception:
        await message.reply('Введите только целое число')


@dp.message_handler(state=FilterBot.price_max)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_filter:
        if message.text in ['0', '1', '2']:
            new_filter['salary'] = int(message.text)
            await FilterBot.next()
            await message.reply('Желаете ли вакансии с удаленной/очной работой?\n'
                                '0 - и удаленная и очная\n'
                                '1 - только удаленная\n'
                                '2 - только очная\n')
        else:
            await message.reply('Введите только целое число от 0 до 2')


@dp.message_handler(state=FilterBot.remote)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_filter:
        if message.text in ['0', '1', '2']:
            new_filter['link'] = int(message.text)
            await FilterBot.next()
            data[message.from_user.id]["filters"] = new_filter._data
            print(new_filter._data)
            with open('data_list.json', 'w') as data_list:
                json.dump(data, data_list, indent=4)
            await message.reply('Фильтры успешно установлены')
            await state.finish()
        else:
            await message.reply('Введите только целое число от 0 до 2')


@dp.message_handler(Text(equals="Мои вакансии"))
async def get_data_projects(message: types.Message):
    for index, item in enumerate(data[message.from_user.id]["jobs"]):
        delete = types.InlineKeyboardButton(
            text="Удалить",
            callback_data="delete_" + str(index + 1))
        delete_button = types.InlineKeyboardMarkup().add(delete)
        await bot.send_message(message.chat.id,
                               create_job_cart(item),
                               reply_markup=delete_button)


@dp.callback_query_handler(text_contains='delete_')
async def callback(call: types.CallbackQuery):
    try:
        if call.data and call.data.startswith("delete_"):
            cl = int(call.data.split('_')[1])
            del data[call.from_user.id]['jobs'][cl-1]
            with open('data_list.json', 'w') as data_list:
                json.dump(data, data_list, indent=4)
            await bot.send_message(call.from_user.id,
                                   'Удалено')
    except Exception as ex:
        print(ex)
        await bot.send_message(call.from_user.id,
                               'Ошибка в исполнении')


@dp.message_handler(Text(equals="Искать работу"))
async def get_data_projects(message: types.Message):
    data_jobs_from_employers = []
    for k in data:
        v = data[k]
        for i in v["jobs"]:
            data_jobs_from_employers.append(i)
    data_jobs_from_employers += free_jobs

    await message.reply(create_job_cart(data_jobs_from_employers[randint(0, len(data_jobs_from_employers))]))


if __name__ == "__main__":
    free_jobs = get_data()
    try:
        with open('data_list.json') as data_list:
            for k, v in json.load(data_list):
                data[int(k)] = v
        print(data)
    except Exception:
        data = {}
    executor.start_polling(dp)
