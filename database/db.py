import os
import asyncpg
from config import START_BALANCE

DATABASE_URL = os.getenv("DATABASE_URL")


async def get_conn():
    return await asyncpg.connect(DATABASE_URL)


# ─── Создание таблиц ───────────────────────────────────────────

async def create_tables():
    conn = await get_conn()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     BIGINT PRIMARY KEY,
                username    TEXT,
                balance     INTEGER DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id      SERIAL PRIMARY KEY,
                name    TEXT NOT NULL,
                price   INTEGER NOT NULL,
                emoji   TEXT DEFAULT '📦'
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id        SERIAL PRIMARY KEY,
                case_id   INTEGER,
                name      TEXT NOT NULL,
                rarity    TEXT NOT NULL,
                chance    REAL NOT NULL,
                value     INTEGER NOT NULL,
                emoji     TEXT DEFAULT '🎁',
                FOREIGN KEY (case_id) REFERENCES cases(id)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id         SERIAL PRIMARY KEY,
                user_id    BIGINT,
                item_id    INTEGER,
                obtained   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)
    finally:
        await conn.close()


# ─── Пользователи ─────────────────────────────────────────────

async def get_user(user_id: int):
    conn = await get_conn()
    try:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
    finally:
        await conn.close()


async def register_user(user_id: int, username: str):
    conn = await get_conn()
    try:
        await conn.execute(
            "INSERT INTO users (user_id, username, balance) VALUES ($1, $2, $3) ON CONFLICT (user_id) DO UPDATE SET username = $2",
            user_id, username, START_BALANCE
        )
    finally:
        await conn.close()


async def get_balance(user_id: int) -> int:
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT balance FROM users WHERE user_id = $1", user_id)
        return row['balance'] if row else 0
    finally:
        await conn.close()


async def update_balance(user_id: int, amount: int):
    conn = await get_conn()
    try:
        await conn.execute(
            "UPDATE users SET balance = balance + $1 WHERE user_id = $2",
            amount, user_id
        )
    finally:
        await conn.close()


# ─── Кейсы и предметы ─────────────────────────────────────────

async def get_all_cases():
    conn = await get_conn()
    try:
        return await conn.fetch("SELECT * FROM cases")
    finally:
        await conn.close()


async def get_case(case_id: int):
    conn = await get_conn()
    try:
        return await conn.fetchrow("SELECT * FROM cases WHERE id = $1", case_id)
    finally:
        await conn.close()


async def get_case_items(case_id: int):
    conn = await get_conn()
    try:
        return await conn.fetch("SELECT * FROM items WHERE case_id = $1", case_id)
    finally:
        await conn.close()


async def add_to_inventory(user_id: int, item_id: int):
    conn = await get_conn()
    try:
        await conn.execute(
            "INSERT INTO inventory (user_id, item_id) VALUES ($1, $2)",
            user_id, item_id
        )
    finally:
        await conn.close()


async def get_inventory(user_id: int):
    conn = await get_conn()
    try:
        return await conn.fetch("""
            SELECT inventory.id as inv_id, items.name, items.rarity, items.value, items.emoji,
                   inventory.obtained
            FROM inventory
            JOIN items ON inventory.item_id = items.id
            WHERE inventory.user_id = $1
            ORDER BY inventory.obtained DESC
        """, user_id)
    finally:
        await conn.close()


# ─── Заполнение начальными данными ────────────────────────────

async def seed_cases():
    conn = await get_conn()
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM cases")
        if count > 0:
            return

        await conn.execute("INSERT INTO cases (name, price, emoji) VALUES ($1, $2, $3)", "Стандартный", 100, "📦")
        await conn.execute("INSERT INTO cases (name, price, emoji) VALUES ($1, $2, $3)", "Премиум", 500, "💎")
        await conn.execute("INSERT INTO cases (name, price, emoji) VALUES ($1, $2, $3)", "Легендарный", 1000, "👑")

        standard_items = [
            (1, "Монетка",        "Обычный",     45.0,   50,  "🪙"),
            (1, "Значок",         "Обычный",     30.0,   80,  "🏅"),
            (1, "Жетон",          "Редкий",      15.0,  200,  "🎖️"),
            (1, "Кристалл",       "Редкий",       7.0,  400,  "💠"),
            (1, "Золотой слиток", "Эпический",    2.5,  800,  "🥇"),
            (1, "Джекпот",        "Легендарный",  0.5, 2000,  "🏆"),
        ]
        premium_items = [
            (2, "Серебро",        "Обычный",     40.0,   300,  "🥈"),
            (2, "Рубин",          "Редкий",      30.0,   600,  "❤️"),
            (2, "Сапфир",         "Редкий",      18.0,  1000,  "💙"),
            (2, "Изумруд",        "Эпический",    8.0,  2000,  "💚"),
            (2, "Бриллиант",      "Эпический",    3.5,  4000,  "💎"),
            (2, "Мега джекпот",   "Легендарный",  0.5, 10000,  "👑"),
        ]
        legendary_items = [
            (3, "Осколок",        "Обычный",     40.0,    700,  "🔮"),
            (3, "Реликвия",       "Редкий",      30.0,   1500,  "🗿"),
            (3, "Артефакт",       "Редкий",      18.0,   3000,  "⚗️"),
            (3, "Корона",         "Эпический",    8.0,   6000,  "👑"),
            (3, "Астрал",         "Эпический",    3.5,  12000,  "🌌"),
            (3, "УЛЬТРА ДЖЕКПОТ", "Легендарный",  0.5,  50000,  "💫"),
        ]

        for item in standard_items + premium_items + legendary_items:
            await conn.execute(
                "INSERT INTO items (case_id, name, rarity, chance, value, emoji) VALUES ($1,$2,$3,$4,$5,$6)",
                *item
            )
    finally:
        await conn.close()


async def sell_item(inv_id: int, user_id: int):
    conn = await get_conn()
    try:
        item = await conn.fetchrow("""
            SELECT items.value FROM inventory
            JOIN items ON inventory.item_id = items.id
            WHERE inventory.id = $1 AND inventory.user_id = $2
        """, inv_id, user_id)
        if not item:
            return None
        value = item['value']
        await conn.execute("DELETE FROM inventory WHERE id = $1 AND user_id = $2", inv_id, user_id)
        return value
    finally:
        await conn.close()


async def get_top_users(limit: int = 10):
    conn = await get_conn()
    try:
        return await conn.fetch("""
            SELECT username, balance FROM users
            ORDER BY balance DESC
            LIMIT $1
        """, limit)
    finally:
        await conn.close()