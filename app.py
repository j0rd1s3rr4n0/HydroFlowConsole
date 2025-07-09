import base64
import pickle
import json
import time
import random
from threading import Thread
from flask import Flask, request, make_response, redirect, render_template

app = Flask(__name__)

# --- simulacion de estado de la presa ---
NUM_GATES = 5
state = {
    'gates': [False] * NUM_GATES,  # False = cerrada
    'water_level': 50.0,           # metros
    'pressure': 40.0,              # bar (aprox)
    'flow': 0.0,                   # m3/s
    'weather': 'soleado',
    'rain_timer': 0,
    'history': {
        'time': [],
        'water_level': [],
        'pressure': [],
        'flow': []
    }
}

# --- funciones auxiliares ---

def update_state():
    """Actualiza las lecturas cada 10 segundos y gestiona la lluvia intensa"""
    while True:
        # control de eventos meteorologicos
        if state['rain_timer'] > 0:
            state['rain_timer'] -= 10
            if state['rain_timer'] <= 0:
                state['weather'] = 'soleado'
        else:
            rnd = random.random()
            if rnd < 0.1:
                state['weather'] = 'lluvia'
            elif rnd < 0.15:  # 5% prob heavy rain
                state['weather'] = 'lluvia fuerte'
                state['rain_timer'] = 60
            else:
                state['weather'] = 'soleado'

        base_inflow = 0.5
        if state['weather'] == 'lluvia':
            inflow = base_inflow + 0.5
        elif state['weather'] == 'lluvia fuerte':
            inflow = base_inflow + 2.0
        else:
            inflow = base_inflow

        outflow = sum(state['gates']) * 1.0
        state['water_level'] += inflow - outflow
        state['water_level'] = max(state['water_level'], 0)
        state['flow'] = outflow
        state['pressure'] = 30 + state['water_level'] * 0.6

        t = int(time.time())
        state['history']['time'].append(t)
        state['history']['water_level'].append(state['water_level'])
        state['history']['pressure'].append(state['pressure'])
        state['history']['flow'].append(state['flow'])
        if len(state['history']['time']) > 50:
            for k in state['history']:
                state['history'][k].pop(0)

        time.sleep(10)

# --- autenticacion insegura ---

def create_cookie(user: str) -> str:
    if user == 'admin':
        role = 'admin'
    elif user.startswith('eng'):
        role = 'engineer'
    else:
        role = 'viewer'
    data = {'user': user, 'role': role}
    return base64.b64encode(pickle.dumps(data)).decode()


def load_cookie(cookie: str):
    return pickle.loads(base64.b64decode(cookie))


@app.route('/login/<user>')
def login(user):
    cookie = create_cookie(user)
    resp = make_response(redirect('/dashboard'))
    resp.set_cookie('session', cookie)
    return resp

# --- interfaz principal ---
@app.route('/dashboard')
def dashboard():
    raw = request.cookies.get('session')
    if not raw:
        return 'Cookie de sesion ausente. Usa /login/<usuario>', 400
    try:
        session = load_cookie(raw)
    except Exception:
        return 'Cookie invalida', 400

    hist = json.dumps(state['history'])
    return render_template('dashboard.html', user=session.get('user'),
                           role=session.get('role'), state=state,
                           history_json=hist)


@app.route('/gate/<int:gid>/<action>', methods=['POST'])
def gate(gid, action):
    raw = request.cookies.get('session')
    if not raw:
        return 'Sin sesion', 400
    try:
        session = load_cookie(raw)
    except Exception:
        return 'Sesion corrupta', 400

    if session.get('role') not in ('engineer', 'admin'):
        return 'Acceso denegado', 403

    if 0 <= gid < NUM_GATES:
        state['gates'][gid] = (action == 'open')
    return redirect('/dashboard')


if __name__ == '__main__':
    Thread(target=update_state, daemon=True).start()
    app.run(debug=True, host='0.0.0.0')
