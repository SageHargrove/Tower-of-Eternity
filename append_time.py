def process_passive_generation(conn):
    base = conn.execute("SELECT last_research_tick FROM base WHERE id = 1").fetchone()
    if not base:
        return
        
    last_tick_str = base["last_research_tick"]
    if not last_tick_str:
        conn.execute("UPDATE base SET last_research_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return

    try:
        last_tick = datetime.strptime(last_tick_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return

    now = datetime.utcnow()
    diff = now - last_tick
    minutes_passed = int(diff.total_seconds() / 60)
    
    ticks = minutes_passed // 5
    if ticks <= 0:
        return
        
    facilities = conn.execute("""
        SELECT f.type, f.level, COUNT(fa.hero_id) as assigned
        FROM facilities f
        LEFT JOIN facility_assignments fa ON f.id = fa.facility_id
        WHERE f.type IN ('The Square', 'The Farm')
        GROUP BY f.id
    """).fetchall()
    
    gold_gen = 0
    supplies_gen = 0
    
    for f in facilities:
        # Base: 50 per tick per level
        base_amt = 50 * f["level"]
        # Assigned heroes increase rate by 10% each
        multiplier = 1.0 + (f["assigned"] * 0.10)
        
        if f["type"] == 'The Square':
            gold_gen += int(base_amt * multiplier) * ticks
        elif f["type"] == 'The Farm':
            supplies_gen += int(base_amt * multiplier) * ticks
            
    if gold_gen > 0 or supplies_gen > 0:
        conn.execute("UPDATE base SET gold = gold + ?, supplies = supplies + ? WHERE id = 1", (gold_gen, supplies_gen))
        
    conn.execute("UPDATE base SET last_research_tick = CURRENT_TIMESTAMP WHERE id = 1")
