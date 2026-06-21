from database import db, set_profile
set_profile('main')
from services.combat_service import run_combat
from services.llm_service import generate_zone_theme

with db() as conn:
    conn.execute("INSERT INTO heroes (name, hero_class, attack, defense, hp, max_hp, speed, is_alive, is_on_team, base_floor) VALUES ('Dummy', 'Warrior', 10, 10, 100, 100, 10, 1, 1, 0)")
    heroes = [dict(r) for r in conn.execute('SELECT * FROM heroes WHERE is_alive = 1 LIMIT 3').fetchall()]
    
if heroes:
    try:
        res = run_combat(heroes, 1, False, False, generate_zone_theme(1))
        print('SUCCESS')
    except Exception as e:
        import traceback
        traceback.print_exc()
else:
    print('No heroes')
