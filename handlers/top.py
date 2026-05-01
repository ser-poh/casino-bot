from aiogram import Router, F
from aiogram.types import Message
from database.db import get_top_users, register_user

router = Router()

@router.message(F.text == "📊 Топ игроков")
async def show_top(message: Message):
    await register_user(message.from_user.id, message.from_user.username)
    users = await get_top_users()

    medals = ["🥇", "🥈", "🥉"]
    text = "📊 <b>Топ игроков:</b>\n\n"

    for i, user in enumerate(users):
        medal = medals[i] if i < 3 else f"{i+1}."
        username = f"@{user['username']}" if user['username'] else "Аноним"
        text += f"{medal} {username} — <b>{user['balance']}💰</b>\n"

    await message.answer(text, parse_mode="HTML")