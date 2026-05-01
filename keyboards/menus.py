from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎁 Кейсы"), KeyboardButton(text="🎮 Игры")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="📊 Топ игроков")]
    ],
    resize_keyboard=True
)