import sqlite3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from database import get_db_path

def clean():
    db_path = get_db_path()
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # 1. Delete all instances of 'The Square'
        conn.execute("DELETE FROM facilities WHERE type = 'The Square'")
        
        # 2. 'The Lobby' is no longer a facility. Delete all 'The Lobby' rows.
        conn.execute("DELETE FROM facilities WHERE type = 'The Lobby'")
        
        # 3. Clean up duplicates of 'The Market' and 'The Farm'
        # Keep only the one with the lowest ID
        for fac in ['The Market', 'The Farm']:
            min_id_row = conn.execute("SELECT MIN(id) as min_id FROM facilities WHERE type = ?", (fac,)).fetchone()
            if min_id_row and min_id_row['min_id']:
                min_id = min_id_row['min_id']
                conn.execute("DELETE FROM facilities WHERE type = ? AND id > ?", (fac, min_id))
        
        # 4. Remove assignments that point to non-existent facilities
        conn.execute("""
            DELETE FROM facility_assignments 
            WHERE facility_id NOT IN (SELECT id FROM facilities)
        """)
        
        conn.commit()
        print(f"Database {db_path} cleaned successfully!")

if __name__ == '__main__':
    clean()
