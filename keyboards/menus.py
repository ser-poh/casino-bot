from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎁 Кейсы"), KeyboardButton(text="🎮 Игры")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="📊 Топ игроков")],
        [KeyboardButton(text="🌐 Открыть Mini App", web_app=WebAppInfo(url="https://ser-poh.github.io/casino-bot"))]
    ],
    resize_keyboard=True
)