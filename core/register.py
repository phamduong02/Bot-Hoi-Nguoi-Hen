import sqlite3

DB = "database.db"


def get_connection():
    return sqlite3.connect(DB)


def init_register_table():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS registered (
            user_id TEXT PRIMARY KEY,
            agreed_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


def is_registered(user_id: str) -> bool:
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "SELECT 1 FROM registered WHERE user_id = ?",
        (str(user_id),)
    )

    result = c.fetchone()

    conn.close()

    return result is not None


def register_user(user_id: str):
    from core.database import get_user, get_profile

    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "INSERT OR IGNORE INTO registered (user_id) VALUES (?)",
        (str(user_id),)
    )

    conn.commit()
    conn.close()

    # Tạo dữ liệu cơ bản
    get_user(str(user_id))
    get_profile(str(user_id))