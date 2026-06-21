import sqlite3
import requests
import time

conn = sqlite3.connect('saves/main.db')
hero = conn.execute("SELECT id FROM heroes WHERE name = 'Gideon Night'").fetchone()
conn.close()

if hero:
    print('Sending request to regenerate Gideon Night...')
    res = requests.post(f'http://127.0.0.1:8000/heroes/{hero[0]}/regenerate-profile')
    print(res.status_code, res.text)
