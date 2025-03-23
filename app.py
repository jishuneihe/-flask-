from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于加密会话

# 配置数据库路径
DATABASE = 'users.db'

# 初始化数据库
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

# 检查用户是否已登录
def is_logged_in():
    return 'user_id' in session

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                flash('登录成功！', 'success')
                return redirect(url_for('notebook'))
            else:
                flash('用户名或密码错误！', 'danger')

    return render_template('login.html')

# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            try:
                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                flash('注册成功！请登录。', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('用户名已存在！请尝试其他用户名。', 'danger')

    return render_template('register.html')

# 修改密码页面
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE id=?", (session['user_id'],))
            user = cursor.fetchone()

            if user and check_password_hash(user[0], old_password):
                hashed_new_password = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password=? WHERE id=?", (hashed_new_password, session['user_id']))
                conn.commit()
                flash('密码修改成功！', 'success')
                return redirect(url_for('notebook'))
            else:
                flash('旧密码错误！', 'danger')

    return render_template('change_password.html')

# 记事本页面
@app.route('/notebook', methods=['GET', 'POST'])
def notebook():
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (user_id, content) VALUES (?, ?)", (session['user_id'], content))
            conn.commit()
            flash('笔记保存成功！', 'success')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM notes WHERE user_id=? ORDER BY id DESC LIMIT 1", (session['user_id'],))
        note = cursor.fetchone()

    return render_template('notebook.html', note=note[0] if note else '')

# 注销
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('您已成功注销！', 'success')
    return redirect(url_for('login'))

# 主页
@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('notebook'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()  # 初始化数据库
    app.run(debug=True)