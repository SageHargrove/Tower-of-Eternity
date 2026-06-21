import urllib.request, json
try:
    req = urllib.request.Request('http://localhost:8000/gacha/pull', data=b'{\"count\": 1}', headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    print('Gacha OK')
except Exception as e:
    print('Gacha ERROR:', e.read().decode('utf-8') if hasattr(e, 'read') else e)
try:
    req = urllib.request.Request('http://localhost:8000/tower/floor/enter', data=b'{\"floor_number\": 1, \"team_id\": 1}', headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    print('Tower OK')
except Exception as e:
    print('Tower ERROR:', e.read().decode('utf-8') if hasattr(e, 'read') else e)
