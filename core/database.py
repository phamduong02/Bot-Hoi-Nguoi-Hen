import sqlite3

DB = "database.db"

def get_connection():
    return sqlite3.connect(DB)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 1. USERS (Tiền tệ)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        money INTEGER DEFAULT 1000
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS daily_claim (
        user_id TEXT PRIMARY KEY,
        last_claim TEXT,
        streak INTEGER DEFAULT 0
    )
    """)

    # 2. CHARACTERS (Nhân vật)
    c.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        char_name TEXT,
        class TEXT,
        rarity TEXT,
        hp INTEGER,
        atk_phys INTEGER,
        atk_magic INTEGER,
        def_phys INTEGER,
        def_magic INTEGER,
        spd INTEGER,
        crit INTEGER
    )
    """)

    # 3. TEAM (Đội hình chiến đấu 5 Slot)
    c.execute("""
    CREATE TABLE IF NOT EXISTS team (
        user_id TEXT PRIMARY KEY,
        slot1 INTEGER,
        slot2 INTEGER,
        slot3 INTEGER,
        slot4 INTEGER,
        slot5 INTEGER
    )
    """)

    # 4. USER_PROFILE (Level, EXP)
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        user_id TEXT PRIMARY KEY,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'Bronze'
    )
    """)

    # 5. USER_WEAPONS (Kho Vũ khí chuẩn RPG)
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_weapons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        weapon_code TEXT,
        hp INTEGER DEFAULT 0,
        rarity TEXT,
        rarity_roll INTEGER DEFAULT 0,
        atk_phys INTEGER DEFAULT 0,
        atk_magic INTEGER DEFAULT 0,
        def_phys INTEGER DEFAULT 0,
        def_magic INTEGER DEFAULT 0,
        crit INTEGER DEFAULT 0,
        spd INTEGER DEFAULT 0,
        equipped_to_char_id INTEGER DEFAULT 0
    )
    """)

    # ---- MIGRATIONS (add missing columns) ----
    # Older DB versions may not have hp/rarity/rarity_roll columns.
    c.execute("PRAGMA table_info(user_weapons)")
    existing_cols = {row[1] for row in c.fetchall()}
    if "hp" not in existing_cols:
        c.execute("ALTER TABLE user_weapons ADD COLUMN hp INTEGER DEFAULT 0")
    if "rarity" not in existing_cols:
        c.execute("ALTER TABLE user_weapons ADD COLUMN rarity TEXT")
    if "rarity_roll" not in existing_cols:
        c.execute("ALTER TABLE user_weapons ADD COLUMN rarity_roll INTEGER DEFAULT 0")

    # 6. USER_INVENTORY (Lưu trữ Rương)
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_inventory (
        user_id TEXT PRIMARY KEY,
        weapon_chests INTEGER DEFAULT 0
    )
    """)

    # 7. USER_ITEMS (Lưu trữ Vật phẩm Shop như Bình máu, Đá cường hóa)
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_items (
        user_id TEXT,
        item_key TEXT,
        quantity INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, item_key)
    )
    """)

    # =========================
    # DATA CLEANUP (Dọn dẹp tướng bị xóa khỏi game)
    # =========================
    removed_character_names = ("Aatrox", "Katarina", "God King Garen")
    placeholders = ",".join("?" for _ in removed_character_names)

    # Tháo tướng bị xóa khỏi cả 5 slot đội hình
    for i in range(1, 6):
        c.execute(
            f"UPDATE team SET slot{i} = NULL WHERE slot{i} IN (SELECT id FROM characters WHERE char_name IN ({placeholders}))",
            removed_character_names,
        )

    # Tháo vũ khí đang mặc trên các tướng bị xóa đưa về kho (equipped = 0)
    c.execute(
        f"UPDATE user_weapons SET equipped_to_char_id = 0 WHERE equipped_to_char_id IN (SELECT id FROM characters WHERE char_name IN ({placeholders}))",
        removed_character_names,
    )

    # Xóa hoàn toàn tướng đó
    c.execute(
        f"DELETE FROM characters WHERE char_name IN ({placeholders})",
        removed_character_names,
    )

    conn.commit()
    conn.close()

# =========================
# USER & PROFILE
# =========================

def get_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return get_user(user_id)

    conn.close()
    return user

def update_money(user_id, new_amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET money = ? WHERE user_id = ?", (new_amount, user_id))
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
    data = c.fetchone()

    if not data:
        c.execute("INSERT INTO user_profile (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return get_profile(user_id)

    conn.close()
    return data

def add_exp(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    profile = get_profile(user_id)
    level = profile[1]
    exp = profile[2] + amount

    while True:
        needed = level * 100
        if exp >= needed:
            level += 1
            exp -= needed
        else:
            break

    c.execute("UPDATE user_profile SET level = ?, exp = ? WHERE user_id = ?", (level, exp, user_id))
    conn.commit()
    conn.close()

# =========================
# CHARACTER & TEAM
# =========================

def add_character(user_id, name, cls, rarity, stats):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO characters 
    (user_id, char_name, class, rarity, hp, atk_phys, atk_magic, def_phys, def_magic, spd, crit)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, name, cls, rarity,
        stats["hp"], stats["atk_phys"], stats["atk_magic"],
        stats["def_phys"], stats["def_magic"], stats["spd"], stats["crit"]
    ))
    conn.commit()
    conn.close()

def get_characters(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
    data = c.fetchall()
    conn.close()
    return data

def get_character_by_id(char_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM characters WHERE id = ? AND user_id = ?", (char_id, user_id))
    data = c.fetchone()
    conn.close()
    return data

def set_team(user_id, slot1, slot2, slot3, slot4=None, slot5=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO team (user_id, slot1, slot2, slot3, slot4, slot5)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
    slot1=excluded.slot1, slot2=excluded.slot2, slot3=excluded.slot3,
    slot4=excluded.slot4, slot5=excluded.slot5
    """, (user_id, slot1, slot2, slot3, slot4, slot5))
    conn.commit()
    conn.close()

def get_team(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM team WHERE user_id = ?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data

# =========================
# WEAPON SYSTEM
# =========================

def add_weapon(user_id, weapon_code, stats):
    from core.weapon_data import WEAPONS

    conn = get_connection()
    c = conn.cursor()

    weapon_def = WEAPONS.get(weapon_code) or {}
    rarity = stats.get("rarity") or weapon_def.get("rarity") or "Common"
    rarity_roll = int(stats.get("rarity_roll") or 0)

    c.execute("""
        INSERT INTO user_weapons 
        (user_id, weapon_code, hp, rarity, rarity_roll, atk_phys, atk_magic, def_phys, def_magic, crit, spd, equipped_to_char_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        user_id, weapon_code,
        stats.get("hp", 0),
        rarity,
        rarity_roll,
        stats.get("atk_phys", 0), stats.get("atk_magic", 0),
        stats.get("def_phys", 0), stats.get("def_magic", 0),
        stats.get("crit", 0), stats.get("spd", 0)
    ))
    conn.commit()
    conn.close()

def get_weapons(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, weapon_code, atk_phys, atk_magic, def_phys, def_magic, crit, spd, equipped_to_char_id, hp, rarity, rarity_roll
        FROM user_weapons WHERE user_id=?
    """, (user_id,))
    data = c.fetchall()
    conn.close()
    return data

def remove_weapon(weapon_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_weapons WHERE id = ?", (weapon_id,))
    conn.commit()
    conn.close()

def equip_weapon(user_id, char_id, weapon_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, equipped_to_char_id FROM user_weapons WHERE id=? AND user_id=?", (weapon_id, user_id))
    weapon = c.fetchone()
    if not weapon: return "not_found"
    if weapon[1] == char_id: return "already_equipped"

    c.execute("SELECT COUNT(*) FROM user_weapons WHERE user_id=? AND equipped_to_char_id=?", (user_id, char_id))
    if c.fetchone()[0] >= 2: return "full"

    c.execute("UPDATE user_weapons SET equipped_to_char_id = ? WHERE id=?", (char_id, weapon_id))
    conn.commit()
    conn.close()
    return "success"

def unequip_weapon(user_id, weapon_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE user_weapons SET equipped_to_char_id = 0 WHERE id=? AND user_id=?", (weapon_id, user_id))
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_weapons_of_char(char_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, weapon_code, atk_phys, atk_magic, def_phys, def_magic, crit, spd, hp, rarity, rarity_roll
        FROM user_weapons WHERE equipped_to_char_id = ?
    """, (char_id,))
    data = c.fetchall()
    conn.close()
    return data

# =========================
# DAILY CLAIM & INVENTORY (SHOP)
# =========================

def get_daily_claim(user_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM daily_claim WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row
 
def set_daily_claim(user_id: str, date_str: str, streak: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO daily_claim (user_id, last_claim, streak)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET last_claim = excluded.last_claim, streak = excluded.streak
    """, (user_id, date_str, streak))
    conn.commit()
    conn.close()

def add_weapon_chests(user_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_inventory (user_id, weapon_chests) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET weapon_chests = weapon_chests + ?
    """, (user_id, amount, amount))
    conn.commit()
    conn.close()

def get_weapon_chests(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT weapon_chests FROM user_inventory WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def spend_weapon_chests(user_id, amount: int = 1) -> bool:
    amount = int(amount or 0)
    if amount <= 0:
        return False

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT weapon_chests FROM user_inventory WHERE user_id=?", (user_id,))
    row = c.fetchone()
    current = int(row[0]) if row else 0
    if current < amount:
        conn.close()
        return False

    c.execute(
        "UPDATE user_inventory SET weapon_chests = weapon_chests - ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()
    conn.close()
    return True

def add_user_item(user_id, item_key, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_items (user_id, item_key, quantity) 
        VALUES (?, ?, ?) 
        ON CONFLICT(user_id, item_key) DO UPDATE SET quantity = quantity + ?
    """, (user_id, item_key, amount, amount))
    conn.commit()
    conn.close()

def get_user_items(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT item_key, quantity FROM user_items WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}
