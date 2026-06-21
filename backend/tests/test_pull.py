import urllib.request, urllib.error
req = urllib.request.Request('http://localhost:8000/gacha/pull', data=b'{\"count\": 1}', headers={'Content-Type': 'application/json'})
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
