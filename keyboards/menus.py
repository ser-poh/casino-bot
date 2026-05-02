from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎰 Открыть Cristal Case", web_app=WebAppInfo(url="https://ser-poh.github.io/casino-bot"))]
    ],
    resize_keyboard=True
)