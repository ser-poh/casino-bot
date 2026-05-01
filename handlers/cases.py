from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
from database.db import get_user, update_balance, get_all_cases, get_case, get_case_items, add_to_inventory, \
    get_balance, register_user

router = Router()


@router.message(F.text == "🎁 Кейсы")
async def show_cases(message: Message):
    await register_user(message.from_user.id, message.from_user.username)
    cases = await get_all_cases()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{case['emoji']} {case['name']} — {case['price']}💰",
                              callback_data=f"case_{case['id']}")]
        for case in cases
    ])

    await message.answer(
        "🎁 <b>Выбери кейс для открытия:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("case_"))
async def open_case(callback: CallbackQuery):
    case_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    await register_user(user_id, callback.from_user.username)

    case = await get_case(case_id)
    balance = await get_balance(user_id)

    if balance < case['price']:
        await callback.answer(f"❌ Недостаточно монет! Нужно {case['price']}💰", show_alert=True)
        return

    items = await get_case_items(case_id)

    # Выбираем предмет по вероятности
    chances = [item['chance'] for item in items]
    won_item = random.choices(items, weights=chances, k=1)[0]

    # Списываем цену кейса и добавляем стоимость предмета
    await update_balance(user_id, -case['price'])
    await add_to_inventory(user_id, won_item['id'])

    new_balance = await get_balance(user_id)

    rarity_colors = {
        "Обычный": "⚪",
        "Редкий": "🔵",
        "Эпический": "🟣",
        "Легендарный": "🟡"
    }
    rarity_icon = rarity_colors.get(won_item['rarity'], "⚪")

    await callback.message.answer(
        f"🎰 <b>Открываем {case['emoji']} {case['name']}...</b>\n\n"
        f"✨ Тебе выпал предмет:\n"
        f"{won_item['emoji']} <b>{won_item['name']}</b>\n"
        f"{rarity_icon} Редкость: <b>{won_item['rarity']}</b>\n"
        f"💰 Стоимость: <b>{won_item['value']}</b> монет\n\n"
        f"💳 Баланс: <b>{new_balance}</b> монет",
        parse_mode="HTML"
    )
    await callback.answer()