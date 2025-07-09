from flask import Flask, request, make_response, render_template
import base64
import pickle
import json
import random

app = Flask(__name__)

# Simple role assignment based on username for demo purposes
ROLE_MAP = {
    'admin': 'admin',
    'engineer': 'engineer',
}

def get_role(username: str) -> str:
    return ROLE_MAP.get(username.lower(), 'viewer')

@app.route('/login/<user>')
def login(user):
    role = get_role(user)
    session_data = {'user': user, 'role': role}
    serialized = pickle.dumps(session_data)
    encoded = base64.b64encode(serialized).decode('utf-8')
    # Store the session info in an unsigned cookie for testing (insecure)
    resp = make_response(
        f"Logged in as {user} with role {role}. Go to /dashboard"
    )
    resp.set_cookie('session', encoded)
    return resp

@app.route('/dashboard')
def dashboard():
    cookie = request.cookies.get('session')
    if not cookie:
        return "No session cookie found", 400
    try:
        data = pickle.loads(base64.b64decode(cookie))
        user = data.get('user', 'Unknown')
        role = data.get('role', 'viewer')
    except Exception:
        return "Invalid session cookie", 400

    # Simulated sensor data with random history for graphs
    history = {
        'water_level': [round(random.uniform(22.0, 24.0), 2) for _ in range(12)],
        'pressure': [round(random.uniform(100.0, 105.0), 2) for _ in range(12)],
        'flow_rate': [round(random.uniform(1400, 1600), 2) for _ in range(12)],
    }

    sensors = {
        'water_level': f"{history['water_level'][-1]} m",
        'pressure': f"{history['pressure'][-1]} kPa",
        'flow_rate': f"{history['flow_rate'][-1]} m3/s",
    }

    return render_template(
        'dashboard.html',
        user=user,
        role=role,
        sensors=sensors,
        history=json.dumps(history)
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
