import json
from datetime import datetime, timezone
from database import db

def process_research_points(conn):
    base = conn.execute("SELECT last_training_tick FROM base WHERE id = 1").fetchone()
    if not base: return
    
    last_tick_str = dict(base).get("last_training_tick")
    if not last_tick_str: return
    
    # We will just piggyback off the training tick, assuming training_service updates it.
    # Wait, if training_service updates last_training_tick to CURRENT_TIMESTAMP, 
    # we can't calculate minutes_passed here!
    # Let's add last_research_tick instead.
    pass

def process_mage_research(conn):
    base = conn.execute("SELECT last_research_tick FROM base WHERE id = 1").fetchone()
    if not base: return
    
    last_tick_str = dict(base).get("last_research_tick")
    if not last_tick_str:
        try:
            conn.execute("ALTER TABLE base ADD COLUMN last_research_tick TIMESTAMP")
        except:
            pass
        conn.execute("UPDATE base SET last_research_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return

    try:
        last_tick = datetime.strptime(last_tick_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        conn.execute("UPDATE base SET last_research_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return
        
    now = datetime.utcnow()
    diff = now - last_tick
    minutes_passed = int(diff.total_seconds() / 60)
    
    if minutes_passed > 0:
        mt = conn.execute("SELECT id FROM facilities WHERE type = 'Mage Tower' AND base_id = 1").fetchone()
        if not mt:
            return
            
        assignments = conn.execute("""
            SELECT fa.hero_id, h.hero_class, h.level, h.traits 
            FROM facility_assignments fa
            JOIN heroes h ON fa.hero_id = h.id
            WHERE fa.facility_id = ? AND h.is_alive = 1
        """, (mt["id"],)).fetchall()
        
        rp_gain = 0
        for a in assignments:
            # Base generation based on class
            if a["hero_class"] == "Mage":
                rp_gain += 5 * minutes_passed
            elif a["hero_class"] == "Magic Engineer":
                rp_gain += 4 * minutes_passed
            else:
                rp_gain += 1 * minutes_passed
                
            # Trait multipliers
            try:
                traits = json.loads(a["traits"] or "[]")
                trait_ids = [t["id"] for t in traits]
                if "talent_genius" in trait_ids:
                    rp_gain += 2 * minutes_passed
                if "talent_prodigy" in trait_ids:
                    rp_gain += 5 * minutes_passed
            except:
                pass
                
        if rp_gain > 0:
            conn.execute("UPDATE base SET research_points = COALESCE(research_points, 0) + ? WHERE id = 1", (rp_gain,))
            
        conn.execute("UPDATE base SET last_research_tick = CURRENT_TIMESTAMP WHERE id = 1")
