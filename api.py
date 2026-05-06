from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database.db import get_balance, get_inventory, get_top_users, get_all_cases, get_case, get_case_items, add_to_inventory, update_balance, sell_item, register_user
from collections import Counter
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище активных игр в мины (в памяти)
mines_sessions = {}

class BetRequest(BaseModel):
    user_id: int
    bet: int

class CoinRequest(BaseModel):
    user_id: int
    bet: int
    choice: str

class RouletteRequest(BaseModel):
    user_id: int
    bet: int
    color: str

class SellRequest(BaseModel):
    user_id: int
    inv_id: int

class MinesStartRequest(BaseModel):
    user_id: int
    bet: int
    mines_count: int

class MinesOpenRequest(BaseModel):
    user_id: int
    cell: int

class MinesCashoutRequest(BaseModel):
    user_id: int

@app.get("/user/{user_id}")
async def get_user_data(user_id: int, username: str = None):
    await register_user(user_id, username)
    balance = await get_balance(user_id)
    items = await get_inventory(user_id)
    return {"balance": balance, "inventory": [dict(i) for i in items]}

@app.get("/top")
async def top_users():
    users = await get_top_users()
    return [dict(u) for u in users]

@app.get("/cases")
async def get_cases():
    cases = await get_all_cases()
    return [dict(c) for c in cases]

@app.get("/cases/{case_id}/open/{user_id}")
async def open_case(case_id: int, user_id: int):
    case = await get_case(case_id)
    balance = await get_balance(user_id)
    if balance < case['price']:
        raise HTTPException(status_code=400, detail="Недостаточно монет")
    items = await get_case_items(case_id)
    chances = [item['chance'] for item in items]
    won_item = random.choices(items, weights=chances, k=1)[0]
    await update_balance(user_id, -case['price'])
    await add_to_inventory(user_id, won_item['id'])
    new_balance = await get_balance(user_id)
    return {"item": dict(won_item), "new_balance": new_balance}

@app.post("/games/slots")
async def play_slots(req: BetRequest):
    if req.bet < 10:
        raise HTTPException(status_code=400, detail="Минимальная ставка 10")
    if req.bet > 1_000_000:
        raise HTTPException(status_code=400, detail="Максимальная ставка 1000000")
    balance = await get_balance(req.user_id)
    if req.bet > balance:
        raise HTTPException(status_code=400, detail="Недостаточно монет")
    symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣", "⭐"]
    weights = [35, 25, 20, 10, 7, 3]
    result = random.choices(symbols, weights=weights, k=3)
    if result[0] == result[1] == result[2]:
        multipliers = {"7️⃣": 10, "💎": 7, "⭐": 5}
        multiplier = multipliers.get(result[0], 3)
        win = req.bet * multiplier
        await update_balance(req.user_id, -req.bet + win)
        outcome = f"ДЖЕКПОТ x{multiplier}! +{win} монет"
    elif result[0] == result[1] or result[1] == result[2]:
        await update_balance(req.user_id, req.bet)
        outcome = f"Два одинаковых! +{req.bet} монет"
    else:
        await update_balance(req.user_id, -req.bet)
        outcome = f"Не повезло! -{req.bet} монет"
    new_balance = await get_balance(req.user_id)
    return {"result": result, "outcome": outcome, "new_balance": new_balance}

@app.post("/games/slots7")
async def play_slots7(req: BetRequest):
    if req.bet < 10:
        raise HTTPException(status_code=400, detail="Минимальная ставка 10")
    if req.bet > 100_000:
        raise HTTPException(status_code=400, detail="Максимальная ставка 100000")
    balance = await get_balance(req.user_id)
    if req.bet > balance:
        raise HTTPException(status_code=400, detail="Недостаточно монет")
    symbols = ["🍒", "🍋", "🍊", "💎", "7️⃣", "⭐"]
    weights = [35, 25, 20, 10, 7, 3]
    result = random.choices(symbols, weights=weights, k=7)
    counts = Counter(result)
    max_count = max(counts.values())
    if max_count == 7:
        win = req.bet * 50
        outcome = f"МЕГАДЖЕКПОТ x50! +{win} монет"
    elif max_count == 6:
        win = req.bet * 20
        outcome = f"ДЖЕКПОТ x20! +{win} монет"
    elif max_count == 5:
        win = req.bet * 10
        outcome = f"Пять одинаковых! x10 +{win} монет"
    elif max_count == 4:
        win = req.bet * 4
        outcome = f"Четыре одинаковых! x4 +{win} монет"
    elif max_count == 3:
        win = req.bet * 2
        outcome = f"Три одинаковых! x2 +{win} монет"
    else:
        win = 0
        outcome = f"Не повезло! -{req.bet} монет"
    if win > 0:
        await update_balance(req.user_id, -req.bet + win)
    else:
        await update_balance(req.user_id, -req.bet)
    new_balance = await get_balance(req.user_id)
    return {"result": result, "outcome": outcome, "new_balance": new_balance}

@app.post("/games/coin")
async def play_coin(req: CoinRequest):
    if req.bet < 10:
        raise HTTPException(status_code=400, detail="Минимальная ставка 10")
    if req.bet > 1_000_000:
        raise HTTPException(status_code=400, detail="Максимальная ставка 1000000")
    balance = await get_balance(req.user_id)
    if req.bet > balance:
        raise HTTPException(status_code=400, detail="Недостаточно монет")
    result = random.choice(["heads", "tails"])
    win = req.choice == result
    if win:
        await update_balance(req.user_id, req.bet)
        outcome = f"Угадал! +{req.bet} монет"
    else:
        await update_balance(req.user_id, -req.bet)
        outcome = f"Не угадал! -{req.bet} монет"
    new_balance = await get_balance(req.user_id)
    return {"result": result, "win": win, "outcome": outcome, "new_balance": new_balance}

@app.post("/games/roulette")
async def play_roulette(req: RouletteRequest):
    if req.bet < 10:
        raise HTTPException(status_code=400, detail="Минимальная ставка 10")
    if req.bet > 1_000_000:
        raise HTTPException(status_code=400, detail="Максимальная ставка 1000000")
    balance = await get_balance(req.user_id)
    if req.bet > balance:
        raise HTTPException(status_code=400, detail="Недостаточно монет")
    spin = random.choices(["red", "black", "green"], weights=[18, 18, 2], k=1)[0]
    multipliers = {"red": 2, "black": 2, "green": 14}
    win = spin == req.color
    if win:
        profit = req.bet * multipliers[spin]
        await update_balance(req.user_id, -req.bet + profit)
        outcome = f"Выиграл x{multipliers[spin]}! +{profit - req.bet} монет"
    else:
        await update_balance(req.user_id, -req.bet)
        outcome = f"Не повезло! -{req.bet} монет"
    new_balance = await get_balance(req.user_id)
    return {"result": spin, "win": win, "outcome": outcome, "new_balance": new_balance}

# ── МИНЫ ──────────────────────────────────────────────────────

def calc_multiplier(opened: int, mines: int) -> float:
    """Множитель растёт с каждой открытой клеткой"""
    safe = 25 - mines
    mult = 1.0
    for i in range(opened):
        mult *= (25 - mines - i) / (25 - i)
    if mult == 0:
        return 1.0
    return round(1 / mult * 0.97, 2)  # 3% комиссия казино

@app.post("/games/mines/start")
async def mines_start(req: MinesStartRequest):
    if req.bet < 10:
        raise HTTPException(status_code=400, detail="Минимальная ставка 10")
    if req.bet > 1_000_000:
        raise HTTPException(status_code=400, detail="Максимальная ставка 1000000")
    if req.mines_count not in [3, 5, 10, 15]:
        raise HTTPException(status_code=400, detail="Мин должно быть 3, 5, 10 или 15")
    balance = await get_balance(req.user_id)
    if req.bet > balance:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    # Списываем ставку
    await update_balance(req.user_id, -req.bet)

    # Генерируем поле
    mines_positions = set(random.sample(range(25), req.mines_count))

    mines_sessions[req.user_id] = {
        "bet": req.bet,
        "mines": mines_positions,
        "mines_count": req.mines_count,
        "opened": [],
        "active": True
    }

    new_balance = await get_balance(req.user_id)
    return {
        "ok": True,
        "new_balance": new_balance,
        "multiplier": calc_multiplier(0, req.mines_count)
    }

@app.post("/games/mines/open")
async def mines_open(req: MinesOpenRequest):
    session = mines_sessions.get(req.user_id)
    if not session or not session["active"]:
        raise HTTPException(status_code=400, detail="Нет активной игры")
    if req.cell < 0 or req.cell > 24:
        raise HTTPException(status_code=400, detail="Неверная клетка")
    if req.cell in session["opened"]:
        raise HTTPException(status_code=400, detail="Клетка уже открыта")

    is_mine = req.cell in session["mines"]

    if is_mine:
        # Проигрыш — показываем все мины
        session["active"] = False
        all_mines = list(session["mines"])
        del mines_sessions[req.user_id]
        new_balance = await get_balance(req.user_id)
        return {
            "is_mine": True,
            "all_mines": all_mines,
            "new_balance": new_balance
        }
    else:
        session["opened"].append(req.cell)
        opened_count = len(session["opened"])
        multiplier = calc_multiplier(opened_count, session["mines_count"])
        potential_win = round(session["bet"] * multiplier)
        return {
            "is_mine": False,
            "opened": session["opened"],
            "multiplier": multiplier,
            "potential_win": potential_win
        }

@app.post("/games/mines/cashout")
async def mines_cashout(req: MinesCashoutRequest):
    session = mines_sessions.get(req.user_id)
    if not session or not session["active"]:
        raise HTTPException(status_code=400, detail="Нет активной игры")
    if len(session["opened"]) == 0:
        raise HTTPException(status_code=400, detail="Открой хотя бы одну клетку")

    multiplier = calc_multiplier(len(session["opened"]), session["mines_count"])
    win = round(session["bet"] * multiplier)

    await update_balance(req.user_id, win)
    session["active"] = False
    all_mines = list(session["mines"])
    del mines_sessions[req.user_id]

    new_balance = await get_balance(req.user_id)
    return {
        "win": win,
        "multiplier": multiplier,
        "all_mines": all_mines,
        "new_balance": new_balance
    }

@app.post("/sell")
async def sell(req: SellRequest):
    value = await sell_item(req.inv_id, req.user_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    await update_balance(req.user_id, value)
    new_balance = await get_balance(req.user_id)
    return {"value": value, "new_balance": new_balance}