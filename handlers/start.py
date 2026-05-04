from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from database.db import register_user, get_balance

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    await register_user(user_id, message.from_user.username)
    balance = await get_balance(user_id)

    url = f"https://ser-poh.github.io/casino-bot?uid={user_id}"

    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 Открыть Cristal Case", web_app=WebAppInfo(url=url))]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"🎰 Добро пожаловать в <b>Cristal Case</b>!\n\n"
        f"💰 Твой баланс: <b>{balance}</b> монет\n\n"
        f"👇 Нажми кнопку ниже чтобы открыть казино!",
        reply_markup=main_menu,
        parse_mode="HTML"
    )