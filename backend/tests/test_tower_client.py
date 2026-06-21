import sys, traceback
sys.path.append('c:/infinite gacha/tower-gacha/backend')
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
try:
    response = client.post('/tower/floor/enter', json={'floor_number': 1, 'team_id': 1})
    if response.status_code != 200:
        print('Error:', response.json())
    else:
        print('OK')
except Exception as e:
    traceback.print_exc()
