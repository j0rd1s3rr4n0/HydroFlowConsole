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
# altura maxima de la presa antes de que el agua la supere (metros)
MAX_LEVEL = 250.0
# limites para avisos de seguridad
WEIGHT_WARN = 60000.0
WEIGHT_MAX = 80000.0
PRESSURE_WARN = WEIGHT_WARN / 1000 * 1.12  # bar equivalentes
PRESSURE_MAX = WEIGHT_MAX / 1000 * 1.12
state = {
    'gates': [False] * NUM_GATES,  # False = cerrada
    'water_level': 50.0,           # metros
    'pressure': 56.0,              # bar (aprox)
    'flow': 0.0,                   # m3/s
    'weather': 'soleado',
    'temperature': 20.0,      # grados C
    'wind_speed': 5.0,        # km/h (simple aproximacion)
    'rain_timer': 0,
    'dam_broken': False,
    'overflow_start': None,
    'history': {
        'time': [],
        'water_level': [],
        'pressure': [],
        'flow': [],
        'temperature': [],
        'wind_speed': []
    }
}

# --- funciones auxiliares ---

UPDATE_INTERVAL = 3  # segundos

def update_state():
    """Actualiza la simulación de la presa cada pocos segundos"""
    while True:
        # eventos meteorológicos
        if state['rain_timer'] > 0:
            state['rain_timer'] -= 10
            if state['rain_timer'] <= 0:
                state['weather'] = 'soleado'
        else:
            rnd = random.random()
            if rnd < 0.1:
                state['weather'] = 'lluvia'
            elif rnd < 0.15:
                state['weather'] = 'lluvia fuerte'
                state['rain_timer'] = 60
            else:
                state['weather'] = 'soleado'

        # actualiza temperatura y viento de forma simple segun el clima
        if state['weather'] == 'lluvia fuerte':
            state['temperature'] += random.uniform(-0.4, 0.2) - 1
            state['wind_speed'] += random.uniform(1, 3)
        elif state['weather'] == 'lluvia':
            state['temperature'] += random.uniform(-0.3, 0.3) - 0.5
            state['wind_speed'] += random.uniform(-0.5, 1)
        else:
            state['temperature'] += random.uniform(-0.2, 0.5)
            state['wind_speed'] += random.uniform(-0.5, 0.5)
        state['temperature'] = max(5, min(state['temperature'], 35))
        state['wind_speed'] = max(0, min(state['wind_speed'], 40))

        if state['dam_broken']:
            # tras la rotura, el agua sale sin control
            state['flow'] = 5.0
            state['water_level'] = max(state['water_level'] - state['flow'], 0)
            # presion aproximada en bar (escala simplificada)
            state['pressure'] = state['water_level'] * 1.12
            if state['pressure'] >= 280 or state['water_level'] > MAX_LEVEL:
                state['dam_broken'] = True
        else:
            base_inflow = 0.2
            if state['weather'] == 'lluvia':
                inflow = base_inflow + 0.8
            elif state['weather'] == 'lluvia fuerte':
                inflow = base_inflow + 2.5
            else:
                inflow = base_inflow

            outflow = sum(state['gates']) * 1.0
            state['water_level'] += inflow - outflow
            state['water_level'] = max(state['water_level'], 0)
            state['flow'] = outflow
            state['pressure'] = state['water_level'] * 1.12
            if state['pressure'] >= 280:
                state['dam_broken'] = True

            if state['water_level'] > MAX_LEVEL:
                if not any(state['gates']):
                    if state['overflow_start'] is None:
                        state['overflow_start'] = time.time()
                    elif time.time() - state['overflow_start'] >= 60:
                        state['dam_broken'] = True
                else:
                    state['overflow_start'] = None
            else:
                state['overflow_start'] = None

        t = int(time.time())
        state['history']['time'].append(t)
        state['history']['water_level'].append(state['water_level'])
        state['history']['pressure'].append(state['pressure'])
        state['history']['flow'].append(state['flow'])
        state['history']['temperature'].append(state['temperature'])
        state['history']['wind_speed'].append(state['wind_speed'])
        if len(state['history']['time']) > 50:
            for k in state['history']:
                state['history'][k].pop(0)

        time.sleep(UPDATE_INTERVAL)

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
    resp = make_response(redirect('/'))
    resp.set_cookie('session', cookie)
    return resp


@app.route('/logout')
def logout():
    """Elimina la cookie de sesion"""
    resp = make_response(redirect('/'))
    resp.delete_cookie('session')
    return resp


@app.route('/')
def index():
    """Muestra el tablero principal con vista de la ciudad y la presa"""
    raw = request.cookies.get('session')
    session = None
    if raw:
        try:
            session = load_cookie(raw)
        except Exception:
            session = None

    # copia del estado con ruido para que cada cliente vea valores ligeramente
    # distintos; esto no afecta al estado real
    session_state = {
        'gates': list(state['gates']),
        'water_level': state['water_level'] + random.uniform(-0.5, 0.5),
        'pressure': state['pressure'] + random.uniform(-0.5, 0.5),
        'flow': state['flow'] + random.uniform(-0.2, 0.2),
        'weather': state['weather'],
        'temperature': state['temperature'] + random.uniform(-0.5,0.5),
        'wind_speed': state['wind_speed'] + random.uniform(-0.5,0.5),
        'dam_broken': state['dam_broken']
    }

    hist_copy = {
        'time': list(state['history']['time']),
        'water_level': [v + random.uniform(-0.5, 0.5) for v in state['history']['water_level']],
        'pressure': [v + random.uniform(-0.5, 0.5) for v in state['history']['pressure']],
        'flow': [v + random.uniform(-0.2, 0.2) for v in state['history']['flow']],
        'temperature': [v + random.uniform(-0.5,0.5) for v in state['history']['temperature']],
        'wind_speed': [v + random.uniform(-0.5,0.5) for v in state['history']['wind_speed']]
    }

    hist_json = json.dumps(hist_copy)
    return render_template(
        'index.html', session=session, state=session_state,
        history_json=hist_json, MAX_LEVEL=MAX_LEVEL,
        WEIGHT_WARN=WEIGHT_WARN, WEIGHT_MAX=WEIGHT_MAX,
        PRESSURE_WARN=PRESSURE_WARN, PRESSURE_MAX=PRESSURE_MAX
    )

# --- interfaz principal ---
@app.route('/dashboard')
def dashboard():
    """Alias legacy que redirige a la pagina principal"""
    return redirect('/')


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
    return redirect('/')


if __name__ == '__main__':
    Thread(target=update_state, daemon=True).start()
    app.run(debug=True, host='0.0.0.0')
