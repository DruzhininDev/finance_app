import sqlite3

conn = sqlite3.connect("finance.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")
    conn.commit()
    print("Колонка user_id добавлена")
except sqlite3.OperationalError as e:
    print(f"Ошибка(возможно, колонка уже есть): {e}")

conn.close()