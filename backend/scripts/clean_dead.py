import os
import sqlite3

def clean_dead_portraits(db_path):
    if not os.path.exists(db_path):
        return
        
    print(f"Cleaning dead portraits in {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        dead_heroes = conn.execute("SELECT id, name, portrait_path FROM heroes WHERE is_alive = 0").fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return
    
    for hero in dead_heroes:
        path = hero["portrait_path"]
        if not path or "default_" in path:
            continue
            
        local_path = f"../{path}"
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                print(f"Deleted dead hero portrait: {path} (Hero: {hero['name']})")
            except Exception as e:
                print(f"Failed to delete {local_path}: {e}")
                
    conn.close()

if __name__ == "__main__":
    clean_dead_portraits("../database.db")
    if os.path.exists("../saves/test.db"):
        clean_dead_portraits("../saves/test.db")
