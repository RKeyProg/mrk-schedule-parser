import os
import re
from datetime import datetime, timedelta
from typing import Optional
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from parser.schedule_parser import find_teacher

router = Router()

# Храним фамилии пользователей
user_watchlist = {}

# Состояние пользователя для изменения преподавателя
user_changing_teacher = {}


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает главную клавиатуру с кнопками управления"""
    keyboard = [
        [KeyboardButton(text="👨‍🏫 Преподаватель")],
        [KeyboardButton(text="📅 На сегодня"), KeyboardButton(text="➡️ На следующий день")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_schedule_file(date: datetime) -> Optional[str]:
    """Ищет файл расписания по дате в папке downloads"""
    filename = date.strftime("%d.%m.%Y.pdf")
    filepath = f"downloads/{filename}"
    return filepath if os.path.exists(filepath) else None


def get_next_workday(current_date: datetime) -> datetime:
    """Возвращает следующий рабочий день (пн-сб)"""
    next_day = current_date + timedelta(days=1)
    # Если воскресенье (6), переходим на понедельник
    if next_day.weekday() == 6:
        next_day = next_day + timedelta(days=1)
    return next_day


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет 👋\n"
        "Введи фамилию преподавателя,\n"
        "затем перешли PDF с расписанием.",
        reply_markup=get_main_keyboard()
    )


@router.message()
async def handle_message(message: Message):
    if not message.text:
        # ---- PDF ----
        if message.document and message.document.mime_type == "application/pdf":
            await handle_pdf(message)
        return

    text = message.text.strip()

    # ---- КНОПКА "Преподаватель" ----
    if text == "👨‍🏫 Преподаватель":
        user_changing_teacher[message.from_user.id] = True
        current_teacher = user_watchlist.get(message.from_user.id)
        if current_teacher:
            await message.answer(
                f"Текущий преподаватель: {current_teacher}\n\n"
                "Введи новую фамилию преподавателя (можно с инициалами):"
            )
        else:
            await message.answer("Введи фамилию преподавателя (можно с инициалами):")
        return

    # ---- КНОПКА "На сегодня" ----
    if text == "📅 На сегодня":
        await handle_schedule_request(message, datetime.now())
        return

    # ---- КНОПКА "На следующий день" ----
    if text == "➡️ На следующий день":
        next_day = get_next_workday(datetime.now())
        await handle_schedule_request(message, next_day)
        return

    # ---- ФАМИЛИЯ ----
    # Убираем лишние пробелы
    teacher_input = " ".join(text.split())
    
    # Проверка формата: буквы, пробелы, точки (поддержка инициалов)
    # Формат: "Фамилия", "Фамилия И.", "Фамилия И.В.", "Фамилия И. В."
    if re.match(r"^[А-Яа-яA-Za-zёЁ]+([\s\.]*[А-Яа-яA-Za-zёЁ])*\.?$", teacher_input):
        user_watchlist[message.from_user.id] = teacher_input
        user_changing_teacher.pop(message.from_user.id, None)
        await message.answer(
            f"Фамилия **{teacher_input}** сохранена ✅",
            reply_markup=get_main_keyboard()
        )
        return

    # ---- PDF ----
    if message.document and message.document.mime_type == "application/pdf":
        await handle_pdf(message)


async def handle_schedule_request(message: Message, date: datetime):
    """Обработка запроса расписания на определенную дату"""
    lastname = user_watchlist.get(message.from_user.id)

    if not lastname:
        await message.answer("❗ Сначала введи фамилию преподавателя")
        return

    schedule_file = get_schedule_file(date)
    
    if not schedule_file:
        date_str = date.strftime("%d.%m.%Y")
        await message.answer(f"📭 Расписание на {date_str} еще не загружено")
        return

    await message.answer("📄 Анализирую расписание...")

    results = find_teacher(lastname, schedule_file)

    if not results:
        await message.answer("Ничего не найдено 😕")
        return

    date_str = date.strftime("%d.%m.%Y")
    await message.answer(f"📅 Расписание на {date_str}:")

    for r in results:
        await message.answer(
            f"👥 Группа: {r['группа']}\n"
            f"⏰ Пара: {r['пара']}\n"
            f"📘 {r['предмет']}\n"
            f"👤 {r['преподаватели']}\n"
            f"🏫 {r['аудитории']}"
        )


async def handle_pdf(message: Message):
    lastname = user_watchlist.get(message.from_user.id)

    if not lastname:
        await message.answer("❗ Сначала введи фамилию")
        return

    os.makedirs("downloads", exist_ok=True)

    file = await message.bot.get_file(message.document.file_id)
    pdf_path = f"downloads/{message.document.file_name}"

    await message.bot.download_file(file.file_path, pdf_path)

    await message.answer("📄 Расписание получено, анализирую...")

    results = find_teacher(lastname, pdf_path)

    if not results:
        await message.answer("Ничего не найдено 😕")
        return

    for r in results:
        await message.answer(
            f"👥 Группа: {r['группа']}\n"
            f"⏰ Пара: {r['пара']}\n"
            f"📘 {r['предмет']}\n"
            f"👤 {r['преподаватели']}\n"
            f"🏫 {r['аудитории']}"
        )
