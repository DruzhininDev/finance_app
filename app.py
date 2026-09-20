from flask import Flask, request, render_template_string
from database import init_db, get_db

EXPENSE_CATEGORIES = {
    "food": "Еда",
    "transport": "Транспорт",
    "health": "Здоровье",
    "entertainment": "Развлечения",
    "services": "Услуги",
    "other": "Другое",
}

INCOME_CATEGORIES = {
    "salary": "Зарплата",
    "debt": "Возврат долга",
    "dividends": "Дивиденды",
    "interest": "Проценты по счетам",
    "gift": "Подарок",
    "freelance": "Фриланс",
    "other_income": "Другое",
}





app = Flask(__name__)

# Создаём таблицу при запуске
init_db()

# HTML-форма для добавления расхода
FORM_HTML = """
<h2>Добавить расход</h2>
<form method="POST">
    <label>Сумма:</label><br>
    <input type="number" step="0.01" name="amount" required><br><br>
    
    <label>Категория:</label><br>
    <select name="category">
        <option value="food">Еда</option>
        <option value="transport">Транспорт</option>
        <option value="health">Здоровье</option>
        <option value="entertainment">Развлечения</option>
        <option value="services">Услуги</option>
        <option value="other">Другое</option>
    </select><br><br>
    
    <label>Описание (необязательно):</label><br>
    <input type="text" name="description"><br><br>
    
    <label>Дата:</label><br>
    <input type="date" name="date" required><br><br>
    
    <button type="submit">Сохранить</button>
</form>
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
INCOME_FORM_HTML = """
<h2>Добавить Доход</h2>
<form method="POST">
    <label>Сумма</label><br>
    <input type="number" step="0.01" name="amount" required><br><br>

    <label>Категория</label><br>
    <select name="category">
        <option value="salary">Зарплата</option>
        <option value="debt">Возврат долга</option>
        <option value="dividends">Дивиденды</option>
        <option value="interest">Проценты по счетам</option>
        <option value="gift">Подарок</option>
        <option value="freelance">Фриланс</option>
        <option value="other_income">Другое</option>
    </select><br><br>

    <label>Описание</label><br>
    <input type="text" name="description"><br><br>

    <label>Дата:</label><br>
    <input type="date" name="date" required><br><br>

    <button type="submit">Сохранить</button>
</form>
"""

MENU_HTML = """
<h1>Финансовое приложение</h1>
<p>Баланс: {current_balance} ₽</p>
<a href="/transactions">Добавить запись</a><br>
<a href="/history">История</a>
"""
def show_records(records):
   html=""
   for record in records:
        amount = record[1]
        description = record[2]
        date = record[3]
        type = record[4]
        balance = record[5]

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

@app.route("/edit/<int:record_id>", methods=["GET", "POST"])
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

        return "Запись обновлена! <a href='/history'>Вернуться в историю</a>"
@app.route("/", methods=["GET", "POST"])
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
        <p>Баланс: {current_balance} ₽</p>
        <a href="/transactions">Добавить запись</a><br>
        <a href="/history">История</a>
        """

@app.route("/delete/<int:record_id>")
def delete_record(record_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

    return "Запись удалена! <a href='/history'>Вернуться к истории</a>"


@app.route("/add_income", methods=["GET", "POST"])
def add_income_page():
    if request.method == "GET":
        return render_template_string(INCOME_FORM_HTML)
        
        # Если пользователь нажал "Сохранить" (POST-запрос)
    if request.method == "POST":
        amount = float(request.form["amount"])
        category = request.form["category"]
        description = request.form.get("description", "")
        date = request.form["date"]
            
            # Сохраняем в базу данных
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO incomes (amount, category, description, date)
            VALUES (?, ?, ?, ?)
        """, (amount, category, description, date))
        conn.commit()
        conn.close()
            
        return "Доход сохранён! <a href='/add'>Добавить расход</a> | <a href='/'>На главную</a> | <a href='/add_income'>Добавить ещё</a>"
    
@app.route("/initial", methods=["GET", "POST"])
def initial_page():
    if request.method == "GET":
        return render_template_string(INITIAL_FORM_HTML)

    if request.method =="POST":
        amount = float(request.form["initial_balance"])
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (ket, value)
            VALUES (?, ?)
        """, ("initial_balance", amount))
        conn.commit()
        conn.close()

        return "Начальная сумма сохранена! <a href='/'>На главную</a>"

@app.route("/history")
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
@app.route("/transactions", methods=["GET", "POST"])
def transactions():
    if request.method == "GET":
        return render_template_string(TRANSACTIONS_FORM_HTML)

    if request.method == "POST":
        amount = float(request.form["amount"])
        description = request.form.get("description", "")
        date = request.form["date"]
        trans_type = request.form["type"]

        current_balance = get_balance()

        if trans_type == "income":
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (amount, description, date, type, balance_after)
            VALUES (?, ?, ?, ?, ?)
        """, (amount, description, date, trans_type, new_balance))
        conn.commit()
        conn.close()

        return "Сохранено! <a href='/'>На главную</a>"

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    # Если пользователь просто открыл страницу (GET-запрос)
    if request.method == "GET":
        return render_template_string(FORM_HTML)
    
    # Если пользователь нажал "Сохранить" (POST-запрос)
    if request.method == "POST":
        amount = float(request.form["amount"])
        category = request.form["category"]
        description = request.form.get("description", "")
        date = request.form["date"]
        
        # Сохраняем в базу данных
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (amount, category, description, date)
            VALUES (?, ?, ?, ?)
        """, (amount, category, description, date))
        conn.commit()
        conn.close()
        
        return "Расход сохранён! <a href='/'>На главную</a> | <a href='/add'>Добавить ещё</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
