import json
import random
import time
import urllib.request

URL = 'http://localhost:5000/sensor_data'


def send(reading_type, value):
    data = json.dumps({'type': reading_type, 'value': value}).encode()
    req = urllib.request.Request(URL, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        resp.read()


while True:
    send('water_level', round(random.uniform(20.0, 25.0), 2))
    send('pressure', round(random.uniform(100.0, 110.0), 2))
    send('temperature', round(random.uniform(10.0, 20.0), 2))
    time.sleep(10)
