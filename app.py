import os
import base64
import pickle
import json
import random
import sqlite3
import hashlib
import hmac
from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, make_response

app = Flask(__name__)
DB_PATH = 'data.db'
SECRET_KEY = 'secret123'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS sensor_readings (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, type TEXT, value REAL)')
    cur.execute('CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, date TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS gate_state (id INTEGER PRIMARY KEY, state TEXT)')
    cur.execute('INSERT OR IGNORE INTO gate_state (id, state) VALUES (1, "closed")')
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def jwt_encode(payload: dict) -> str:
    header = {'alg': 'HS256', 'typ': 'JWT'}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=')
    message = header_b64 + b'.' + payload_b64
    signature = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=')
    return b'.'.join([header_b64, payload_b64, sig_b64]).decode()


def jwt_decode(token: str):
    try:
        header_b64, payload_b64, sig_b64 = token.split('.')
        message = f'{header_b64}.{payload_b64}'.encode()
        signature = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
        if base64.urlsafe_b64encode(signature).rstrip(b'=') != sig_b64.encode():
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=='))
        return payload
    except Exception:
        return None


def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('login'))
        data = jwt_decode(token)
        if not data:
            return redirect(url_for('login'))
        request.user = data
        return f(*args, **kwargs)
    return wrapper


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'viewer')
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hash_pw(password), role))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return 'Usuario existente', 400
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username=?', (username,))
        user = cur.fetchone()
        conn.close()
        if user and user['password'] == hash_pw(password):
            token = jwt_encode({'username': username, 'role': user['role']})
            resp = redirect(url_for('dashboard'))
            resp.set_cookie('token', token)
            return resp
        return 'Credenciales incorrectas', 401
    return render_template('login.html')


@app.route('/dashboard')
@require_login
def dashboard():
    user = request.user['username']
    role = request.user['role']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT state FROM gate_state WHERE id=1')
    gate_state = cur.fetchone()['state']
    sensors = {}
    for t in ('water_level', 'pressure', 'temperature'):
        cur.execute('SELECT value FROM sensor_readings WHERE type=? ORDER BY timestamp DESC LIMIT 1', (t,))
        row = cur.fetchone()
        if row:
            sensors[t] = row['value']
        else:
            sensors[t] = round(random.uniform(1, 100), 2)
    conn.close()
    return render_template('dashboard.html', user=user, role=role, sensors=sensors, gate_state=gate_state)


@app.route('/gate/<action>', methods=['POST'])
@require_login
def gate(action):
    role = request.user['role']
    if role not in ['engineer', 'admin']:
        return 'Acceso denegado', 403
    state = 'open' if action == 'open' else 'closed'
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE gate_state SET state=? WHERE id=1', (state,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/reports/<int:report_id>')
@require_login
def reports(report_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM reports WHERE id=?', (report_id,))
    report = cur.fetchone()
    conn.close()
    if not report:
        return 'No existe el informe', 404
    return render_template('report.html', report=report)


@app.route('/api/sensor_config', methods=['POST'])
def sensor_config():
    try:
        config = pickle.loads(base64.b64decode(request.data))
        print('Aplicando configuracion:', config)
    except Exception:
        return 'Datos invalidos', 400
    return 'Configuracion aplicada'


@app.route('/diagnostics/run_test', methods=['POST'])
def run_test():
    cmd = request.form.get('cmd', '')
    os.system(cmd)
    return f'Ejecutado: {cmd}'


@app.route('/firmware/update', methods=['GET', 'POST'])
def firmware_update():
    if request.method == 'POST':
        f = request.files.get('firmware')
        if not f:
            return 'Sin archivo', 400
        os.makedirs('firmware_uploads', exist_ok=True)
        path = os.path.join('firmware_uploads', f.filename)
        f.save(path)
        return 'Firmware actualizado con exito'
    return render_template('firmware_update.html')


@app.route('/sensor_data', methods=['POST'])
def sensor_data():
    data = request.get_json()
    if not data:
        return 'No data', 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO sensor_readings (type, value) VALUES (?, ?)', (data.get('type'), data.get('value')))
    conn.commit()
    conn.close()
    return 'ok'


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')
