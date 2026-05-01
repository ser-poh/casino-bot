from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import get_inventory, sell_item, update_balance, register_user

router = Router()

rarity_icons = {"Обычный": "⚪", "Редкий": "🔵", "Эпический": "🟣", "Легендарный": "🟡"}

def inventory_keyboard(items):
    buttons = []
    for item in items:
        label = f"Продать {item['emoji']} {item['name']} за {item['value']}💰"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"sell_{item['inv_id']}")])
    buttons.append([InlineKeyboardButton(text="💰 Продать всё", callback_data="sell_all")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text == "🎒 Инвентарь")
async def show_inventory(message: Message):
    user_id = message.from_user.id
    await register_user(user_id, message.from_user.username)
    items = await get_inventory(user_id)

    if not items:
        await message.answer("🎒 <b>Твой инвентарь пуст</b>\n\nОткрывай кейсы чтобы получить предметы!", parse_mode="HTML")
        return

    text = "🎒 <b>Твой инвентарь:</b>\n\n"
    total_value = 0
    for item in items:
        icon = rarity_icons.get(item['rarity'], "⚪")
        text += f"{item['emoji']} <b>{item['name']}</b> {icon} {item['rarity']} — {item['value']}💰\n"
        total_value += item['value']

    text += f"\n💰 <b>Общая стоимость: {total_value} монет</b>\n\n⬇️ Выбери что продать:"
    await message.answer(text, reply_markup=inventory_keyboard(items), parse_mode="HTML")

@router.callback_query(F.data.startswith("sell_") & ~F.data.startswith("sell_all"))
async def sell_one(callback: CallbackQuery):
    inv_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    value = await sell_item(inv_id, user_id)
    if value is None:
        await callback.answer("❌ Предмет не найден!", show_alert=True)
        return

    await update_balance(user_id, value)

    # Обновляем инвентарь
    items = await get_inventory(user_id)
    if not items:
        await callback.message.edit_text("🎒 <b>Инвентарь пуст</b>", parse_mode="HTML")
    else:
        text = "🎒 <b>Твой инвентарь:</b>\n\n"
        total_value = 0
        for item in items:
            icon = rarity_icons.get(item['rarity'], "⚪")
            text += f"{item['emoji']} <b>{item['name']}</b> {icon} {item['rarity']} — {item['value']}💰\n"
            total_value += item['value']
        text += f"\n💰 <b>Общая стоимость: {total_value} монет</b>\n\n⬇️ Выбери что продать:"
        await callback.message.edit_text(text, reply_markup=inventory_keyboard(items), parse_mode="HTML")

    await callback.answer(f"✅ Продано за {value}💰")

@router.callback_query(F.data == "sell_all")
async def sell_all(callback: CallbackQuery):
    user_id = callback.from_user.id
    items = await get_inventory(user_id)

    if not items:
        await callback.answer("❌ Инвентарь пуст!", show_alert=True)
        return

    total = 0
    for item in items:
        value = await sell_item(item['inv_id'], user_id)
        if value:
            total += value

    await update_balance(user_id, total)
    await callback.message.edit_text(
        f"💰 <b>Всё продано!</b>\n\nПолучено: <b>{total} монет</b>",
        parse_mode="HTML"
    )
    await callback.answer(f"✅ Продано всё за {total}💰")