import os
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from parser.schedule_parser import find_teacher

router = Router()

# Храним фамилии пользователей
user_watchlist = {}


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет 👋\n"
        "Введи фамилию преподавателя,\n"
        "затем перешли PDF с расписанием."
    )


@router.message()
async def handle_message(message: Message):
    # ---- ФАМИЛИЯ ----
    if message.text and message.text.isalpha():
        user_watchlist[message.from_user.id] = message.text
        await message.answer(f"Фамилия **{message.text}** сохранена ✅")
        return

    # ---- PDF ----
    if message.document and message.document.mime_type == "application/pdf":
        await handle_pdf(message)


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
            f"👤 {lastname}\n"
            f"👥 Группа: {r['группа']}\n"
            f"⏰ Пара: {r['пара']}\n"
            f"📘 {r['предмет']}\n"
            f"🏫 {', '.join(r['аудитории'])}"
        )
