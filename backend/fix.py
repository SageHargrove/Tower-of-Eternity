import sqlite3
import os

db_path = 'saves/main.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM facilities WHERE type = 'The Square' AND id > (SELECT MIN(id) FROM facilities WHERE type = 'The Square')")
    conn.commit()
    conn.close()
    print("Fixed duplicate squares in DB")
