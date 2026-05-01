import os
import aiosqlite
from config import DB_NAME, START_BALANCE

print("База данных будет создана здесь:", os.path.abspath(DB_NAME))
from config import DB_NAME, START_BALANCE


# ─── Создание таблиц ───────────────────────────────────────────

async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:

        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                balance     INTEGER DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица кейсов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                price   INTEGER NOT NULL,
                emoji   TEXT DEFAULT '📦'
            )
        """)

        # Таблица предметов в кейсах
        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id   INTEGER,
                name      TEXT NOT NULL,
                rarity    TEXT NOT NULL,
                chance    REAL NOT NULL,
                value     INTEGER NOT NULL,
                emoji     TEXT DEFAULT '🎁',
                FOREIGN KEY (case_id) REFERENCES cases(id)
            )
        """)

        # Инвентарь игрока
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                item_id    INTEGER,
                obtained   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)

        await db.commit()


# ─── Пользователи ─────────────────────────────────────────────

async def get_user(user_id: int):
    """Получить пользователя по ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        return await cursor.fetchone()


async def register_user(user_id: int, username: str):
    """Зарегистрировать нового пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?, ?, ?)",
            (user_id, username, START_BALANCE)
        )
        await db.commit()


async def get_balance(user_id: int) -> int:
    """Получить баланс пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT balance FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def update_balance(user_id: int, amount: int):
    """Изменить баланс (amount может быть отрицательным)"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


# ─── Кейсы и предметы ─────────────────────────────────────────

async def get_all_cases():
    """Получить список всех кейсов"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cases")
        return await cursor.fetchall()


async def get_case(case_id: int):
    """Получить кейс по ID"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM cases WHERE id = ?", (case_id,)
        )
        return await cursor.fetchone()


async def get_case_items(case_id: int):
    """Получить все предметы из кейса"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM items WHERE case_id = ?", (case_id,)
        )
        return await cursor.fetchall()


async def add_to_inventory(user_id: int, item_id: int):
    """Добавить предмет в инвентарь игрока"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO inventory (user_id, item_id) VALUES (?, ?)",
            (user_id, item_id)
        )
        await db.commit()


async def get_inventory(user_id: int):
    """Получить инвентарь игрока"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT inventory.id as inv_id, items.name, items.rarity, items.value, items.emoji,
                   inventory.obtained
            FROM inventory
            JOIN items ON inventory.item_id = items.id
            WHERE inventory.user_id = ?
            ORDER BY inventory.obtained DESC
        """, (user_id,))
        return await cursor.fetchall()

# ─── Заполнение начальными данными ────────────────────────────

async def seed_cases():
    """Добавить стартовые кейсы если их нет"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cases")
        count = (await cursor.fetchone())[0]
        if count > 0:
            return  # Уже заполнено

        # Добавляем кейсы
        await db.execute(
            "INSERT INTO cases (name, price, emoji) VALUES (?, ?, ?)",
            ("Стандартный", 100, "📦")
        )
        await db.execute(
            "INSERT INTO cases (name, price, emoji) VALUES (?, ?, ?)",
            ("Премиум", 500, "💎")
        )
        await db.execute(
            "INSERT INTO cases (name, price, emoji) VALUES (?, ?, ?)",
            ("Легендарный", 1000, "👑")
        )

        # Предметы для Стандартного кейса (id=1)
        standard_items = [
            (1, "Монетка",       "Обычный",    45.0,  50,   "🪙"),
            (1, "Значок",        "Обычный",    30.0,  80,   "🏅"),
            (1, "Жетон",         "Редкий",     15.0,  200,  "🎖️"),
            (1, "Кристалл",      "Редкий",      7.0,  400,  "💠"),
            (1, "Золотой слиток","Эпический",   2.5,  800,  "🥇"),
            (1, "Джекпот",       "Легендарный", 0.5, 2000,  "🏆"),
        ]
        # Предметы для Премиум кейса (id=2)
        premium_items = [
            (2, "Серебро",       "Обычный",    40.0,  300,  "🥈"),
            (2, "Рубин",         "Редкий",     30.0,  600,  "❤️"),
            (2, "Сапфир",        "Редкий",     18.0, 1000,  "💙"),
            (2, "Изумруд",       "Эпический",   8.0, 2000,  "💚"),
            (2, "Бриллиант",     "Эпический",   3.5, 4000,  "💎"),
            (2, "Мега джекпот",  "Легендарный", 0.5,10000,  "👑"),
        ]
        # Предметы для Легендарного кейса (id=3)
        legendary_items = [
            (3, "Осколок",        "Обычный",    40.0,   700,  "🔮"),
            (3, "Реликвия",       "Редкий",     30.0,  1500,  "🗿"),
            (3, "Артефакт",       "Редкий",     18.0,  3000,  "⚗️"),
            (3, "Корона",         "Эпический",   8.0,  6000,  "👑"),
            (3, "Астрал",         "Эпический",   3.5, 12000,  "🌌"),
            (3, "УЛЬТРА ДЖЕКПОТ", "Легендарный", 0.5, 50000,  "💫"),
        ]

        for item in standard_items + premium_items + legendary_items:
            await db.execute(
                "INSERT INTO items (case_id, name, rarity, chance, value, emoji) VALUES (?,?,?,?,?,?)",
                item
            )

        await db.commit()


async def sell_item(inv_id: int, user_id: int):
    """Продать предмет из инвентаря"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        # Проверяем что предмет принадлежит этому юзеру и берём его стоимость
        cursor = await db.execute("""
            SELECT items.value FROM inventory
            JOIN items ON inventory.item_id = items.id
            WHERE inventory.id = ? AND inventory.user_id = ?
        """, (inv_id, user_id))
        item = await cursor.fetchone()
        if not item:
            return None
        value = item['value']
        # Удаляем из инвентаря
        await db.execute("DELETE FROM inventory WHERE id = ? AND user_id = ?", (inv_id, user_id))
        await db.commit()
        return value

async def get_top_users(limit: int = 10):
    """Получить топ игроков по балансу"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT username, balance FROM users
            ORDER BY balance DESC
            LIMIT ?
        """, (limit,))
        return await cursor.fetchall()