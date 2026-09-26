import sqlite3

def get_db():
    """Подключение к базе данных"""
    conn = sqlite3.connect("finance.db")
    return conn

def init_db():
    """Создание таблиц, если их ещё нет"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Создаём таблицу расходов

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        balance_after REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT NOT NULL,
        value TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# При запуске файла — создаём базу
if __name__ == "__main__":
    init_db()
    print("База данных создана")