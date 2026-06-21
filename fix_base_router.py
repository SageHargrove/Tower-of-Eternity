import re

with open('backend/routers/base.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_route = '''
@router.post("/upgrade")
def upgrade_base():
    """Upgrades the base level and increases max heroes."""
    from database import db
    from fastapi import HTTPException
    with db() as conn:
        base = conn.execute("SELECT level, gold, max_roster_size FROM base WHERE id = 1").fetchone()
        lvl = base["level"]
        cost = 5000 * lvl
        if base["gold"] < cost:
            raise HTTPException(status_code=400, detail=f"Not enough gold. Need {cost}.")
        conn.execute("UPDATE base SET gold = gold - ?, level = level + 1, max_roster_size = max_roster_size + 10 WHERE id = 1", (cost,))
    return {"ok": True}

@router.post("/rest")
'''

c = c.replace('@router.post("/rest")', new_route.strip())

with open('backend/routers/base.py', 'w', encoding='utf-8') as f:
    f.write(c)
