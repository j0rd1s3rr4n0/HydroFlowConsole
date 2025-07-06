from flask import Flask, request, make_response, render_template
import base64
import pickle

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
    resp = make_response(f"Logged in as {user} with role {role}. Go to /dashboard")
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

    # Simulated sensor data
    sensors = {
        'water_level': '23.5m',
        'pressure': '101.3 kPa',
        'flow_rate': '1500 m3/s'
    }
    return render_template('dashboard.html', user=user, role=role, sensors=sensors)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
