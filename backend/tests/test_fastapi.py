from fastapi.testclient import TestClient
from main import app
import json
import traceback
client = TestClient(app)
try:
    response = client.post('/gacha/pull', json={'count': 1})
    print(response.status_code, response.text)
except Exception as e:
    traceback.print_exc()
