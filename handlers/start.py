from aiogram import Router, F
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from database.db import register_user, get_balance
from keyboards.menus import main_menu

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    await register_user(message.from_user.id, message.from_user.username)
    balance = await get_balance(message.from_user.id)
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"🎰 Добро пожаловать в <b>Cristal Case</b>!\n\n"
        f"💰 Твой баланс: <b>{balance}</b> монет",
        reply_markup=main_menu,
        parse_mode="HTML"
    )

@router.message(F.text == "💰 Баланс")
async def balance(message: Message):
    await register_user(message.from_user.id, message.from_user.username)
    balance = await get_balance(message.from_user.id)
    await message.answer(
        f"💰 Твой баланс: <b>{balance}</b> монет",
        parse_mode="HTML"
    )