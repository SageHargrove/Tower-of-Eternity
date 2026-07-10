from datetime import datetime, timezone
import math

def process_fatigue_decay(conn):
    # Fetch base info for last tick
    base = conn.execute("SELECT last_fatigue_tick FROM base WHERE id = 1").fetchone()
    if not base:
        return
        
    last_tick_str = base["last_fatigue_tick"]
    if not last_tick_str:
        # Initialize if missing
        conn.execute("UPDATE base SET last_fatigue_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return

    # Parse last tick
    # SQLite CURRENT_TIMESTAMP is UTC 'YYYY-MM-DD HH:MM:SS'
    try:
        last_tick = datetime.strptime(last_tick_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return # If it's malformed, just wait for a manual fix or ignore

    now = datetime.utcnow()
    diff = now - last_tick
    minutes_passed = int(diff.total_seconds() / 60)
    
    # Fatigue decays 1 point every 5 minutes
    decay_amount = minutes_passed // 5
    
    if decay_amount > 0:
        base_row = conn.execute("SELECT highest_floor FROM base WHERE id = 1").fetchone()
        unlocked_floors = max(1, base_row["highest_floor"] // 10)
        
        all_heroes = conn.execute("SELECT base_floor FROM heroes WHERE is_alive = 1").fetchall()
        floor_counts = {}
        for h in all_heroes:
            f = h["base_floor"]
            floor_counts[f] = floor_counts.get(f, 0) + 1
            
        fatigued_heroes = conn.execute("SELECT id, base_floor, fatigue FROM heroes WHERE fatigue > 0").fetchall()
        
        for hero in fatigued_heroes:
            f = hero["base_floor"]
            count = floor_counts.get(f, 1)
            lp_total = f * 100
            lp_per_hero = lp_total // max(1, count)
            
            # Base decay is 1 per 5 mins. Bonus: +1 per 50 LP
            bonus_decay = lp_per_hero // 50
            total_decay = decay_amount * (1 + bonus_decay)
            
            conn.execute(
                "UPDATE heroes SET fatigue = MAX(0, fatigue - ?) WHERE id = ?", 
                (total_decay, hero["id"])
            )
        
        # Advance the last tick by the exact chunk of 5 minutes we processed
        # leaving any remainder seconds for the next tick
        # But for simplicity, we can just set it to now since it's a casual game
        conn.execute("UPDATE base SET last_fatigue_tick = CURRENT_TIMESTAMP WHERE id = 1")

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
        
    facilities = conn.execute("SELECT id, type, level FROM facilities WHERE type IN ('Market', 'Farm', 'Vault', 'Skydock')").fetchall()

    PREFERRED_CLASSES = {
        'Market': ('Merchant', 'Quartermaster'),
        # Farmers work the Farm (was Merchant — a copy/paste from Market).
        'Farm': ('Farmer', 'Druid'),
        'Skydock': ('Magic Engineer',),
    }

    gold_gen = 0
    ingredients_gen = 0
    aether_gen = 0

    for f in facilities:
        assigned = conn.execute("""
            SELECT h.hero_class FROM facility_assignments fa
            JOIN heroes h ON fa.hero_id = h.id
            WHERE fa.facility_id = ? AND h.is_alive = 1
        """, (f["id"],)).fetchall()

        preferred = PREFERRED_CLASSES.get(f["type"], ())
        multiplier = 1.0
        for a in assigned:
            multiplier += 0.20 if a["hero_class"] in preferred else 0.10

        # Support revamp: a Merchant on the Market / Farmer on the Farm adds a
        # star-scaled bonus on top (support_service.INCOME_BONUS — up to +75%
        # at 7★), so a high-star economist is a real jackpot.
        try:
            from services.support_service import get_support_effects
            fx = get_support_effects(conn)
            if f["type"] == 'Market':
                multiplier += fx.get("merchant_income_bonus", 0)
            elif f["type"] == 'Farm':
                multiplier += fx.get("farmer_income_bonus", 0)
        except Exception:
            pass

        if f["type"] == 'Market':
            base_amt = 100 * f["level"]
            gold_gen += int(base_amt * multiplier) * ticks
        elif f["type"] == 'Farm':
            # The Farm grows alchemy ingredients (replaced the retired
            # supplies currency) — cooked into consumables at the Dining
            # Hall or brewed into potions at the Alchemist Lab.
            base_amt = 5 * f["level"]
            ingredients_gen += int(base_amt * multiplier) * ticks
        elif f["type"] == 'Skydock':
            # Aether condensers: the Skydock slowly refines raw mana into
            # Aether, the battleships' raid fuel. Deliberately slow — the
            # Alchemist Lab's refine-aether craft is the fast (but paid)
            # path; raids should feel like an expedition you PROVISION for.
            base_amt = 2 * f["level"]
            aether_gen += int(base_amt * multiplier) * ticks
        # Training Grounds XP is handled by services/training_service.py
        # now (regimen-aware — flat XP is just the "focus" default), so it's
        # no longer processed here to avoid double-ticking.

    # Athenaeum logistics research (Swift Logistics, Caravan Routes, …)
    # multiplies everything the base generates passively.
    try:
        from services.athenaeum_service import get_research_bonuses
        gen_pct = get_research_bonuses(conn).get("passive_gen_pct", 0)
        if gen_pct:
            mult = 1.0 + gen_pct / 100.0
            gold_gen = int(gold_gen * mult)
            ingredients_gen = int(ingredients_gen * mult)
            aether_gen = int(aether_gen * mult)
    except Exception:
        pass

    if gold_gen > 0 or ingredients_gen > 0 or aether_gen > 0:
        conn.execute(
            "UPDATE base SET gold = gold + ?, ingredients = ingredients + ?, aether = aether + ? WHERE id = 1",
            (gold_gen, ingredients_gen, aether_gen)
        )

    hero_assignments = conn.execute("""
        SELECT fa.hero_id
        FROM facilities f
        JOIN facility_assignments fa ON f.id = fa.facility_id
        WHERE f.type IN ('Market', 'Farm', 'Vault', 'Skydock')
    """).fetchall()

    for h in hero_assignments:
        conn.execute("UPDATE heroes SET xp = COALESCE(xp, 0) + ? WHERE id = ?", (20 * ticks, h["hero_id"]))
        
    conn.execute("UPDATE base SET last_research_tick = CURRENT_TIMESTAMP WHERE id = 1")
