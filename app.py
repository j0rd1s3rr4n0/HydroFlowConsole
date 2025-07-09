import base64
import pickle
import json
import time
import random
from threading import Thread
from flask import Flask, request, make_response, redirect, render_template, abort

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
DAM_AREA = 1000.0  # m^2 estimados del vaso
WATER_DENSITY = 1000.0  # kg/m^3
GRAVITY = 9.81  # m/s^2
RPM_MIN = 2000.0
RPM_WARN = 4500.0
RPM_MAX = 5000.0
POWER_MAX = 200.0
state = {
    'gates': [False] * NUM_GATES,  # False = cerrada
    'water_level': 50.0,           # metros
    'pressure': 56.0,              # bar (aprox)
    'flow': 0.0,                   # m3/s
    'weather': 'soleado',
    'temperature': 20.0,      # grados C
    'wind_speed': 5.0,        # km/h (simple aproximacion)
    'water_temp': 15.0,       # temperatura del agua
    'turbine_temps': [20.0] * NUM_GATES,
    'turbine_rpm': [0.0] * NUM_GATES,
    'turbine_broken': [False] * NUM_GATES,
    'power': 0.0,             # produccion electrica en MW
    'water_weight': 0.0,      # peso total del agua en toneladas
    'rain_timer': 0,
    'dam_broken': False,
    'overflow_start': None,
    'history': {
        'time': [],
        'water_level': [],
        'pressure': [],
        'flow': [],
        'temperature': [],
        'wind_speed': [],
        'water_temp': [],
        'turbine_temp': [],
        'power': [],
        'rpm': [],
        'water_weight': []
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

        # temperatura del agua se ajusta lentamente hacia la ambiental
        state['water_temp'] += (state['temperature'] - state['water_temp']) * 0.05
        state['water_temp'] += random.uniform(-0.1, 0.1)
        state['water_temp'] = max(4, min(state['water_temp'], 30))

        # calcula el numero de compuertas abiertas para estimar el caudal total
        open_count = sum(state['gates'])
        for i, open_ in enumerate(state['gates']):
            running = (
                open_ and not state['dam_broken'] and not state['turbine_broken'][i]
                and open_count > 2
            )
            if running:
                # rpm minima de funcionamiento y crecimiento segun presion
                target_rpm = max(state['pressure'] * 8, RPM_MIN)
                state['turbine_rpm'][i] += (target_rpm - state['turbine_rpm'][i]) * 0.2
            else:
                state['turbine_rpm'][i] = 0.0

            base_temp = state['temperature'] - 3
            if state['turbine_rpm'][i] > 0:
                state['turbine_temps'][i] = base_temp + state['turbine_rpm'][i] / 1000.0
            else:
                state['turbine_temps'][i] = base_temp

            if state['turbine_rpm'][i] > RPM_MAX:
                state['turbine_broken'][i] = True
                state['turbine_rpm'][i] = 0.0

            # la potencia final se calcula aparte usando caudal y altura

        if state['dam_broken']:
            # tras la rotura, el agua sale sin control pero sin generacion
            state['flow'] = 5.0
            state['water_level'] = max(state['water_level'] - state['flow'], 0)
            state['pressure'] = state['water_level'] * 1.12
            volume = state['water_level'] * DAM_AREA
            mass = volume * WATER_DENSITY
            state['water_weight'] = mass / 1000
            state['power'] = 0.0
        else:
            base_inflow = 0.2
            if state['weather'] == 'lluvia':
                inflow = base_inflow + 0.8
            elif state['weather'] == 'lluvia fuerte':
                inflow = base_inflow + 2.5
            else:
                inflow = base_inflow

            outflow = open_count * 1.0
            state['water_level'] += inflow - outflow
            state['water_level'] = max(state['water_level'], 0)
            state['flow'] = outflow
            state['pressure'] = state['water_level'] * 1.12
            # peso del agua segun el volumen embalsado
            volume = state['water_level'] * DAM_AREA
            mass = volume * WATER_DENSITY
            state['water_weight'] = mass / 1000  # toneladas
            # potencia total segun formula P = rho*g*Q*H (en MW)
            state['power'] = WATER_DENSITY * GRAVITY * state['flow'] * state['water_level'] / 1_000_000
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
        state['history']['water_temp'].append(state['water_temp'])
        state['history']['water_weight'].append(state['water_weight'])
        # para graficar se usa la temperatura media de las turbinas
        avg_turb = sum(state['turbine_temps'])/NUM_GATES
        state['history']['turbine_temp'].append(avg_turb)
        avg_rpm = sum(state['turbine_rpm'])/NUM_GATES
        state['history']['rpm'].append(avg_rpm)
        state['history']['power'].append(state['power'])
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

    if state['power'] > POWER_MAX:
        abort(500)

    # copia del estado con ruido para que cada cliente vea valores ligeramente
    # distintos; esto no afecta al estado real
    session_state = {
        'gates': list(state['gates']),
        'water_level': state['water_level'] + random.uniform(-0.5, 0.5),
        'pressure': state['pressure'] + random.uniform(-0.5, 0.5),
        'flow': (state['flow'] + random.uniform(-0.2, 0.2)) if state['flow'] > 0 else 0.0,
        'weather': state['weather'],
        'temperature': state['temperature'] + random.uniform(-0.5,0.5),
        'wind_speed': state['wind_speed'] + random.uniform(-0.5,0.5),
        'dam_broken': state['dam_broken'],
        'water_temp': state['water_temp'] + random.uniform(-0.2,0.2),
        'water_weight': state['water_weight'] + random.uniform(-50,50),
        'turbine_temps': [t + random.uniform(-0.5,0.5) for t in state['turbine_temps']],
        # añadimos algo de ruido pero si la turbina esta parada no debe moverse
        'turbine_rpm': [max(0.0, (r + random.uniform(-5,5)) if r > 0 else 0.0) for r in state['turbine_rpm']],
        'turbine_broken': list(state['turbine_broken']),
        'rpm_avg': max(0.0, sum(state['turbine_rpm'])/NUM_GATES + (random.uniform(-5,5) if any(state['turbine_rpm']) else 0)),
        'power': state['power'] + random.uniform(-0.2,0.2)
    }

    hist_copy = {
        'time': list(state['history']['time']),
        'water_level': [v + random.uniform(-0.5, 0.5) for v in state['history']['water_level']],
        'pressure': [v + random.uniform(-0.5, 0.5) for v in state['history']['pressure']],
        'flow': [v + random.uniform(-0.2, 0.2) if v > 0 else 0.0 for v in state['history']['flow']],
        'temperature': [v + random.uniform(-0.5,0.5) for v in state['history']['temperature']],
        'wind_speed': [v + random.uniform(-0.5,0.5) for v in state['history']['wind_speed']],
        'water_temp': [v + random.uniform(-0.2,0.2) for v in state['history']['water_temp']],
        'water_weight': [v + random.uniform(-50,50) for v in state['history']['water_weight']],
        'turbine_temp': [v + random.uniform(-0.5,0.5) for v in state['history']['turbine_temp']],
        'power': [v + random.uniform(-0.2,0.2) for v in state['history']['power']],
        'rpm': [v + random.uniform(-5,5) for v in state['history']['rpm']]
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


@app.route('/state')
def api_state():
    """Devuelve el estado actual con ruido para actualizaciones AJAX"""
    raw = request.cookies.get('session')
    if state['power'] > POWER_MAX:
        abort(500)

    session_state = {
        'gates': list(state['gates']),
        'water_level': state['water_level'] + random.uniform(-0.5, 0.5),
        'pressure': state['pressure'] + random.uniform(-0.5, 0.5),
        'flow': (state['flow'] + random.uniform(-0.2, 0.2)) if state['flow'] > 0 else 0.0,
        'weather': state['weather'],
        'temperature': state['temperature'] + random.uniform(-0.5, 0.5),
        'wind_speed': state['wind_speed'] + random.uniform(-0.5, 0.5),
        'dam_broken': state['dam_broken'],
        'water_temp': state['water_temp'] + random.uniform(-0.2, 0.2),
        'water_weight': state['water_weight'] + random.uniform(-50, 50),
        'turbine_temps': [t + random.uniform(-0.5, 0.5) for t in state['turbine_temps']],
        'turbine_rpm': [max(0.0, (r + random.uniform(-5, 5)) if r > 0 else 0.0) for r in state['turbine_rpm']],
        'turbine_broken': list(state['turbine_broken']),
        'rpm_avg': max(0.0, sum(state['turbine_rpm']) / NUM_GATES + (random.uniform(-5, 5) if any(state['turbine_rpm']) else 0)),
        'power': state['power'] + random.uniform(-0.2, 0.2)
    }

    hist_copy = {
        'time': list(state['history']['time']),
        'water_level': [v + random.uniform(-0.5, 0.5) for v in state['history']['water_level']],
        'pressure': [v + random.uniform(-0.5, 0.5) for v in state['history']['pressure']],
        'flow': [v + random.uniform(-0.2, 0.2) if v > 0 else 0.0 for v in state['history']['flow']],
        'temperature': [v + random.uniform(-0.5, 0.5) for v in state['history']['temperature']],
        'wind_speed': [v + random.uniform(-0.5, 0.5) for v in state['history']['wind_speed']],
        'water_temp': [v + random.uniform(-0.2, 0.2) for v in state['history']['water_temp']],
        'water_weight': [v + random.uniform(-50, 50) for v in state['history']['water_weight']],
        'turbine_temp': [v + random.uniform(-0.5, 0.5) for v in state['history']['turbine_temp']],
        'power': [v + random.uniform(-0.2, 0.2) for v in state['history']['power']],
        'rpm': [v + random.uniform(-5, 5) for v in state['history']['rpm']]
    }
    return {
        'state': session_state,
        'history': hist_copy,
        'MAX_LEVEL': MAX_LEVEL,
        'WEIGHT_WARN': WEIGHT_WARN,
        'WEIGHT_MAX': WEIGHT_MAX,
        'PRESSURE_WARN': PRESSURE_WARN,
        'PRESSURE_MAX': PRESSURE_MAX,
        'water_weight': session_state['water_weight']
    }


@app.errorhandler(500)
def fail(e):
    return "<h1>500 Internal Server Error</h1><p>flag{electric_power}</p>", 500


if __name__ == '__main__':
    Thread(target=update_state, daemon=True).start()
    app.run(debug=True, host='0.0.0.0')
