from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
from database.db import get_balance, update_balance, register_user

router = Router()

class BetState(StatesGroup):
    waiting_bet_slots = State()
    waiting_bet_coin = State()
    waiting_coin_choice = State()
    waiting_bet_roulette = State()
    waiting_roulette_color = State()

def games_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍒 Слоты", callback_data="game_slots")],
        [InlineKeyboardButton(text="🪙 Монетка", callback_data="game_coin")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="game_roulette")],
    ])

# ─── Меню игр ───────────────────────────────────────────

@router.message(F.text == "🎮 Игры")
async def show_games(message: Message):
    await message.answer("🎮 <b>Выбери игру:</b>", reply_markup=games_keyboard(), parse_mode="HTML")

# ─── СЛОТЫ ───────────────────────────────────────────

@router.callback_query(F.data == "game_slots")
async def slots_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BetState.waiting_bet_slots)
    await callback.message.answer("🍒 <b>Слоты</b>\n\nВведи сумму ставки:", parse_mode="HTML")
    await callback.answer()

@router.message(BetState.waiting_bet_slots)
async def slots_play(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введи число!")
        return

    bet = int(message.text)
    user_id = message.from_user.id
    balance = await get_balance(user_id)

    if bet < 10:
        await message.answer("❌ Минимальная ставка 10 монет!")
        return
    if bet > balance:
        await message.answer(f"❌ Недостаточно монет! Твой баланс: {balance}💰")
        return

    symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣", "⭐"]
    weights = [35, 25, 20, 10, 7, 3]
    result = random.choices(symbols, weights=weights, k=3)

    if result[0] == result[1] == result[2]:
        multipliers = {"7️⃣": 10, "💎": 7, "⭐": 5}
        multiplier = multipliers.get(result[0], 3)
        win = bet * multiplier
        await update_balance(user_id, -bet + win)
        new_balance = await get_balance(user_id)
        text = (f"🎰 {result[0]} {result[1]} {result[2]}\n\n"
                f"🎉 <b>ДЖЕКПОТ x{multiplier}! +{win} монет</b>\n"
                f"💳 Баланс: <b>{new_balance}</b>")
    elif result[0] == result[1] or result[1] == result[2]:
        win = bet
        await update_balance(user_id, win)
        new_balance = await get_balance(user_id)
        text = (f"🎰 {result[0]} {result[1]} {result[2]}\n\n"
                f"✨ <b>Два одинаковых! +{win} монет</b>\n"
                f"💳 Баланс: <b>{new_balance}</b>")
    else:
        await update_balance(user_id, -bet)
        new_balance = await get_balance(user_id)
        text = (f"🎰 {result[0]} {result[1]} {result[2]}\n\n"
                f"😔 <b>Не повезло! -{bet} монет</b>\n"
                f"💳 Баланс: <b>{new_balance}</b>")

    again_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё раз", callback_data="game_slots")],
        [InlineKeyboardButton(text="🎮 Другая игра", callback_data="back_to_games")]
    ])
    await state.clear()
    await message.answer(text, reply_markup=again_keyboard, parse_mode="HTML")

# ─── МОНЕТКА ───────────────────────────────────────────

@router.callback_query(F.data == "game_coin")
async def coin_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BetState.waiting_bet_coin)
    await callback.message.answer("🪙 <b>Монетка</b>\n\nВведи сумму ставки:", parse_mode="HTML")
    await callback.answer()

@router.message(BetState.waiting_bet_coin)
async def coin_bet_received(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введи число!")
        return

    bet = int(message.text)
    user_id = message.from_user.id
    balance = await get_balance(user_id)

    if bet < 10:
        await message.answer("❌ Минимальная ставка 10 монет!")
        return
    if bet > balance:
        await message.answer(f"❌ Недостаточно монет! Твой баланс: {balance}💰")
        return

    await state.update_data(bet=bet)
    await state.set_state(BetState.waiting_coin_choice)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Орёл", callback_data="coin_heads"),
         InlineKeyboardButton(text="🔤 Решка", callback_data="coin_tails")]
    ])
    await message.answer(f"Ставка: <b>{bet}</b> монет. Теперь выбери сторону:",
                         reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(BetState.waiting_coin_choice, F.data.in_({"coin_heads", "coin_tails"}))
async def coin_play(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data["bet"]
    user_id = callback.from_user.id

    choice = "👑 Орёл" if callback.data == "coin_heads" else "🔤 Решка"
    result = random.choice(["👑 Орёл", "🔤 Решка"])
    win = choice == result

    if win:
        await update_balance(user_id, bet)
        new_balance = await get_balance(user_id)
        text = (f"🪙 Выпало: <b>{result}</b>\n"
                f"Ты выбрал: <b>{choice}</b>\n\n"
                f"🎉 <b>Ты угадал! +{bet} монет</b>\n"
                f"💳 Баланс: <b>{new_balance}</b>")
    else:
        await update_balance(user_id, -bet)
        new_balance = await get_balance(user_id)
        text = (f"🪙 Выпало: <b>{result}</b>\n"
                f"Ты выбрал: <b>{choice}</b>\n\n"
                f"😔 <b>Не угадал! -{bet} монет</b>\n"
                f"💳 Баланс: <b>{new_balance}</b>")

    again_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё раз", callback_data="game_coin")],
        [InlineKeyboardButton(text="🎮 Другая игра", callback_data="back_to_games")]
    ])
    await state.clear()
    await callback.message.answer(text, reply_markup=again_keyboard, parse_mode="HTML")
    await callback.answer()

# ─── РУЛЕТКА ───────────────────────────────────────────

@router.callback_query(F.data == "game_roulette")
async def roulette_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BetState.waiting_bet_roulette)
    await callback.message.answer("🎡 <b>Рулетка</b>\n\nВведи сумму ставки:", parse_mode="HTML")
    await callback.answer()

@router.message(BetState.waiting_bet_roulette)
async def roulette_bet_received(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введи число!")
        return

    bet = int(message.text)
    user_id = message.from_user.id
    balance = await get_balance(user_id)

    if bet < 10:
        await message.answer("❌ Минимальная ставка 10 монет!")
        return
    if bet > balance:
        await message.answer(f"❌ Недостаточно монет! Твой баланс: {balance}💰")
        return

    await state.update_data(bet=bet)
    await state.set_state(BetState.waiting_roulette_color)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное x2", callback_data="roulette_red"),
         InlineKeyboardButton(text="⚫ Чёрное x2", callback_data="roulette_black")],
        [InlineKeyboardButton(text="🟢 Зелёное x14", callback_data="roulette_green")]
    ])
    await message.answer(f"Ставка: <b>{bet}</b> монет. Выбери цвет:",
                         reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(BetState.waiting_roulette_color, F.data.in_({"roulette_red", "roulette_black", "roulette_green"}))
async def roulette_play(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data["bet"]
    user_id = callback.from_user.id

    choice_map = {"roulette_red": ("🔴 Красное", 2), "roulette_black": ("⚫ Чёрное", 2), "roulette_green": ("🟢 Зелёное", 14)}
    choice_name, multiplier = choice_map[callback.data]

    # 18 красных, 18 чёрных, 2 зелёных
    spin = random.choices(["red", "black", "green"], weights=[18, 18, 2], k=1)[0]
    result_map = {"red": "🔴 Красное", "black": "⚫ Чёрное", "green": "🟢 Зелёное"}
    result_name = result_map[spin]

    chosen_color = callback.data.split("_")[1]
    win = spin == chosen_color

    if win:
        profit = bet * multiplier
        await update_balance(user_id, -bet + profit)
        new_balance = await get_balance(user_id)
        text = (f"🎡 Выпало: <b>{result_name}</b>\n"
                f"Ты поставил: <b>{choice_name}</b>\n\n"
                f"🎉 <b>Выигрыш x{multiplier}! +{profit - bet} монет</b>\n"
                f"💳 Баланс: <b>{new_balance}</b>")
    else:
        await update_balance(user_id, -bet)
        new_balance = await get_balance(user_id)
        text = (f"🎡 Выпало: <b>{result_name}</b>\n"
                f"Ты поставил: <b>{choice_name}</b>\n\n"
                f"😔 <b>Не повезло! -{bet} монет</b>\n"
                f"💳 Баланс: <b>{new_balance}</b>")

    again_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё раз", callback_data="game_roulette")],
        [InlineKeyboardButton(text="🎮 Другая игра", callback_data="back_to_games")]
    ])
    await state.clear()
    await callback.message.answer(text, reply_markup=again_keyboard, parse_mode="HTML")
    await callback.answer()

# ─── Назад к играм ───────────────────────────────────────────

@router.callback_query(F.data == "back_to_games")
async def back_to_games(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🎮 <b>Выбери игру:</b>", reply_markup=games_keyboard(), parse_mode="HTML")
    await callback.answer()