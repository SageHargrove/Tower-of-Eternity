import sys
import os
import shutil
import sqlite3
import re
import time

def migrate_db(db_path, profile_name):
    if not os.path.exists(db_path):
        return
        
    print(f"Migrating DB: {db_path} to profile '{profile_name}'")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        heroes = conn.execute("SELECT id, name, portrait_path FROM heroes").fetchall()
    except sqlite3.OperationalError:
        # Not a valid game DB?
        conn.close()
        return
        
    target_dir = f"../static/portraits/{profile_name}"
    os.makedirs(target_dir, exist_ok=True)
    
    for hero in heroes:
        hero_id = hero["id"]
        name = hero["name"]
        path = hero["portrait_path"]
        
        if not path or "default_" in path:
            continue
            
        safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', name.lower()).strip('_')
        
        # If it's already properly formatted in the target dir, skip
        if path.startswith(f"static/portraits/{profile_name}/") and safe_name in path:
            continue
            
        new_filename = f"hero_{safe_name}_{hero_id}_{int(time.time())}.png"
        new_path = f"static/portraits/{profile_name}/{new_filename}"
        
        local_old_path = f"../{path}"
        local_new_path = f"../{new_path}"
        
        if os.path.exists(local_old_path):
            try:
                # We COPY so we don't break other profiles if they share the image.
                # Wait, if we copy, we leave the old image.
                # But we WANT to remove it from the generic pool if it was in cached?
                # Actually, copying is safer so we don't accidentally break another DB that also references it.
                shutil.copy(local_old_path, local_new_path)
                conn.execute("UPDATE heroes SET portrait_path = ? WHERE id = ?", (new_path, hero_id))
                print(f"  Copied & Updated {path} -> {new_path}")
            except Exception as e:
                print(f"  Error moving {local_old_path}: {e}")
        else:
            pass
            
    conn.commit()
    conn.close()

def organize_cached():
    # Move stray cached_*.png in static/portraits/ into static/portraits/cached/
    portraits_dir = "../static/portraits"
    cached_dir = "../static/portraits/cached"
    os.makedirs(cached_dir, exist_ok=True)
    
    for file in os.listdir(portraits_dir):
        if file.startswith("cached_") and file.endswith(".png"):
            old_p = os.path.join(portraits_dir, file)
            new_p = os.path.join(cached_dir, file)
            shutil.move(old_p, new_p)
            print(f"Moved stray cached image {file} to cached/")
            
            # Update paths in all databases
            old_db_path = f"static/portraits/{file}"
            new_db_path = f"static/portraits/cached/{file}"
            
            dbs_to_check = ["../database.db"]
            if os.path.exists("../saves"):
                for sf in os.listdir("../saves"):
                    if sf.endswith(".db"):
                        dbs_to_check.append(os.path.join("../saves", sf))
                        
            for dbp in dbs_to_check:
                if os.path.exists(dbp):
                    try:
                        conn = sqlite3.connect(dbp)
                        conn.execute("UPDATE portrait_cache SET path = ? WHERE path = ?", (new_db_path, old_db_path))
                        # Just in case a hero owns it and we haven't migrated it yet
                        conn.execute("UPDATE heroes SET portrait_path = ? WHERE portrait_path = ?", (new_db_path, old_db_path))
                        conn.commit()
                        conn.close()
                    except:
                        pass

if __name__ == "__main__":
    organize_cached()
    # The current active DB is 'test' according to the user
    migrate_db("../database.db", "test")
    if os.path.exists("../saves"):
        for db_file in os.listdir("../saves"):
            if db_file.endswith(".db"):
                profile_name = db_file[:-3]
                migrate_db(os.path.join("../saves", db_file), profile_name)
    
    print("Migration complete!")
