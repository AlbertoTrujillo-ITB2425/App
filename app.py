from flask import Flask, render_template, request, send_file, abort
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

# Load multiple users from an environment variable
users = {}
app_users = os.getenv('APP_USERS', 'admin:1234')  # Use a default for demonstration
for user in app_users.split(','):
    username, password = user.split(':')
    users[username] = generate_password_hash(password)  # Hash the password

DATABASE = os.getenv('DATABASE_PATH', 'database.db')

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            salary REAL NOT NULL)
    ''')
    conn.commit()
    conn.close()

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

@app.route('/')
@auth.login_required
def index():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    conn.close()
    return render_template('index.html', employees=employees)

@app.route('/add', methods=['POST'])
@auth.login_required
def add_employee():
    name = request.form['name']
    position = request.form['position']
    salary = request.form['salary']
    
    if not(name and position and salary):
        abort(400, description="All fields are required")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO employees (name, position, salary) VALUES (?, ?, ?)", (name, position, float(salary)))
    conn.commit()
    conn.close()
    return "Employee added successfully! <a href='/'>Return</a>"

@app.route('/export', methods=['GET'])
@auth.login_required
def export_excel():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()

    file_path = "employees.xlsx"
    df.to_excel(file_path, index=False, engine='openpyxl')
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, ssl_context='adhoc')  # Run HTTPS in development
