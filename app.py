import sqlite3
from flask import Flask, request, render_template_string, redirect
from database import init_db, get_db
from werkzeug.security import generate_password_hash


app = Flask(__name__)

# Создаём таблицу при запуске
init_db()

# HTML-форма для добавления расхода

REGISTER_FORM_HTML = """
<h2>Регистрация</h2>
<form method="post">
    <label>Логин:</label><br>
    <input type="text" name="username" required><br><br>

    <label>Пароль:</label><br>
    <input type="password" name="password" required><br><br>

    <button type="submit">Зарегистроваться</button>
</form>
<p>Уже есть аккаунт?<a href="/login">Войти</a></p>
"""

INITIAL_FORM_HTML = """ 
<h2>Добро пожаловать!</h2>
<p>Введите вашу начальную сумму:</p>
<form method="POST">
    <input type="number" step="0.01" name="initial_balance" required>
    <button type="submit">Сохранить</button>
</form>
"""

TRANSACTIONS_FORM_HTML = """
<h2>Добавить запись</h2>
<form method="POST">
    <label>Сумма</label><br>
    <input type="number" step="0.01" name="amount" required><br><br>

    <label>Описание</label><br>
    <input type="text" name="description"><br><br>
    
    <label>Дата</label>
    <input type="date" name="date" required><br><br>

    <label>Тип</label>
    <select name="type">
        <option value="income">Доход</option>
        <option value="expense">Расход</option>
    </select><br><br>

    <button type="submit">Сохранить</button>
</form>
"""

def show_records(records):
   html=""
   for record in records:
        amount = f"{record[1]:.2f}"
        description = record[2]
        date = record[3]
        type = record[4]
        balance = f"{record[5]:.2f}"

        if type == "income":
            color = "#d4edda"
            text_color = "#155724"
        else: 
            color = "#f8d7da"
            text_color = "#721c24"

        style = (
            f"background: {color}; color: {text_color}; margin-bottom: 10px;"
            f"font-size: 20px;"
        )
        edit_link = f"<a href='/edit/{record[0]}'>Редактировать</a>"

        link = f"<a href='/delete/{record[0]}'>Удалить</a>"
        text = f"{amount} | {type} | {description} | {date} | {balance} "
        html += f"<div style = '{style}'>{text} {edit_link} {link} </div>"

        

   return html




def get_balance():

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE setting_key = 'initial_balance'")
    result = cursor.fetchall()

    balance = float(result[0][0])
    conn.close()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT amount, type FROM transactions")
    transactions = cursor.fetchall()
    conn.close()

    for trans in transactions:
        amount = trans[0]
        trans_type = trans[1]
        if trans_type == "income":
            balance += amount
        
        else: 
            balance -= amount
    return balance


def recalculate_balances():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM settings WHERE setting_key = 'initial_balance'")
    start_sum = cursor.fetchall()
    balance = float(start_sum[0][0])

    cursor.execute("SELECT id, amount, type FROM transactions ORDER BY id")
    transactions = cursor.fetchall()

    for trans in transactions:
        trans_id = trans[0]
        amount = trans[1]
        trans_type = trans[2]

        if trans_type == "income":
            balance += amount
        else:
            balance -= amount

        cursor.execute("""
            UPDATE transactions
            SET balance_after = ?
            WHERE id = ?
        """, (balance, trans_id))

    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"]) #ГЛАВНАЯ
def home():

    if request.method =="POST":
            amount = float(request.form["initial_balance"])

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings(setting_key, value)
                VALUES(?, ?)
            """, ("initial_balance", amount))
            conn.commit()
            conn.close()

            return redirect("/")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE setting_key = 'initial_balance'")
    result = cursor.fetchall()
    conn.close()
    
    # Если суммы нет — показываем форму
    if not result:
            return render_template_string(INITIAL_FORM_HTML)
    else:
        current_balance = get_balance()
 
    return f"""
        <h1>Финансовое приложение</h1>
        <p>Баланс: {current_balance:.2f} ₽</p>
        <a href="/transactions">Добавить запись</a><br>
        <a href="/history">История</a>
        """

@app.route("/transactions", methods=["GET", "POST"]) #ДОБАВЛЕНИЕ ТРАНЗАКЦИЙ
def transactions():
    if request.method == "GET":
        return render_template_string(TRANSACTIONS_FORM_HTML)

    if request.method == "POST":
        amount = float(request.form["amount"])
        description = request.form.get("description", "")
        date = request.form["date"]
        trans_type = request.form["type"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (amount, description, date, type, balance_after)
            VALUES (?, ?, ?, ?, ?)
        """, (amount, description, date, trans_type, 0))
        conn.commit()
        conn.close()

        recalculate_balances()

        return "Сохранено! <a href='/'>На главную</a>"

@app.route("/history") #ИСТОРИЯ ТРАНЗАКЦИЙ
def history_page():
    
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    html_transactions = show_records(transactions)

    conn.close()

    return f"""
    <h2>История</h2>
    {html_transactions}

    <a href="/">На главную</a>
    """


@app.route("/edit/<int:record_id>", methods=["GET", "POST"]) #РЕДАКТИРОВАНИЕ ТРАНЗАКЦИЙ
def edit_record(record_id):

    if request.method =="GET":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        conn.close()

        if not record:
            return "Запись не найдена"

        amount = record[1]
        description = record[2]
        date = record[3]
        type = record[4]

        return f"""
            <h2>Редактировать запись</h2>
            <form method="POST">
                <input type="number" step="0.01" name="amount" value="{amount}" required><br>
                <input type="text" name="description" value="{description}"><br>
                <input type="date" name="date" value="{date}"><br>
                <select name="type">
                    <option value="income" {'selected' if type == 'income' else ''}>Доход</option>
                    <option value="expense" {'selected' if type =='expense' else ''}>Расход</option>
                </select><br>
                <button type="submit">Сохранить</button>
            </form>
            """

    if request.method =="POST":
        amount = float(request.form["amount"])
        description = request.form.get("description", "")
        date = request.form["date"]
        type = request.form["type"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transactions
            SET amount = ?, description = ?, date = ?, type = ?
            WHERE id = ? 
            """, (amount, description, date, type, record_id))
        conn.commit()
        conn.close()

        recalculate_balances()

        return "Запись обновлена! <a href='/history'>Вернуться в историю</a>"


@app.route("/delete/<int:record_id>") #УДАЛЕНИЕ ЗАПИСЕЙ
def delete_record(record_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

    recalculate_balances()

    return "Запись удалена! <a href='/history'>Вернуться к истории</a>"


@app.route("/register", methods=["GET", "POST"]) #РЕГИСТРАЦИЯ
def register():
    if request.method == "GET":
        return render_template_string(REGISTER_FORM_HTML)

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
            """, (username, password_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Такой логин уже занят. <a href='/register'>Попробовать снова</a>"

        conn.close()
        return "Регистрация успешна! <a href='/login'>Войти</a>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
