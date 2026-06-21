import os
import sqlite3

saves_dir = "saves"
main_db = os.path.join(saves_dir, "main.db")
test_db = os.path.join(saves_dir, "test.db")

if os.path.exists(main_db):
    os.rename(main_db, test_db)
    print(f"Renamed {main_db} to {test_db}")

if os.path.exists(test_db):
    conn = sqlite3.connect(test_db)
    conn.execute("UPDATE base SET gold = gold + 1000000 WHERE id = 1")
    conn.commit()
    conn.close()
    print("Added 1,000,000 gold to test.db")
else:
    print("test.db not found!")
