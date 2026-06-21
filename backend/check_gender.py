import sqlite3
conn = sqlite3.connect('saves/main.db')
conn.row_factory = sqlite3.Row
for hero in conn.execute("SELECT name, gender, portrait_path FROM heroes").fetchall():
    print(f"{hero['name']}: gender={hero['gender']}, portrait={hero['portrait_path']}")
