import sqlite3
conn = sqlite3.connect("finance.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM transactions")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
