import re

with open('routers/base.py', 'r') as f:
    content = f.read()

replacement = '''RESEARCH_UPGRADES = {
    "gold_boost": {"name": "Alchemical Transmutation", "desc": "+5% Gold from Tower", "max_level": 5, "base_cost": 100},
    "xp_boost": {"name": "Arcane Insight", "desc": "+10% Skill XP Gain", "max_level": 5, "base_cost": 150},
    "drop_boost": {"name": "Treasure Finding", "desc": "+5% Equipment Drop Rate", "max_level": 5, "base_cost": 200},
}

@router.get("/facilities/mage-tower/upgrades")
def get_research_upgrades():
    with db() as conn:
        base = conn.execute("SELECT research_points, global_buffs FROM base WHERE id = 1").fetchone()
        buffs = json.loads(base["global_buffs"] or "{}")
        
    res = []
    for uid, info in RESEARCH_UPGRADES.items():
        lvl = buffs.get(uid, 0)
        res.append({
            "id": uid,
            "name": info["name"],
            "desc": info["desc"],
            "level": lvl,
            "max_level": info["max_level"],
            "cost": info["base_cost"] * (lvl + 1)
        })
    return {"points": base["research_points"], "upgrades": res}

class BuyResearchReq(BaseModel):
    upgrade_id: str

@router.post("/facilities/mage-tower/buy")
def buy_research_upgrade(req: BuyResearchReq):
    with db() as conn:
        base = conn.execute("SELECT research_points, global_buffs FROM base WHERE id = 1").fetchone()
        buffs = json.loads(base["global_buffs"] or "{}")
        
        info = RESEARCH_UPGRADES.get(req.upgrade_id)
        if not info:
            raise HTTPException(status_code=400, detail="Invalid upgrade.")
            
        lvl = buffs.get(req.upgrade_id, 0)
        if lvl >= info["max_level"]:
            raise HTTPException(status_code=400, detail="Max level reached.")
            
        cost = info["base_cost"] * (lvl + 1)
        if base["research_points"] < cost:
            raise HTTPException(status_code=400, detail=f"Requires {cost} Research Points.")
            
        buffs[req.upgrade_id] = lvl + 1
        conn.execute("UPDATE base SET research_points = research_points - ?, global_buffs = ? WHERE id = 1", 
                     (cost, json.dumps(buffs)))
                     
    return {"ok": True}'''

content = re.sub(r'@router\.post\("/facilities/mage-tower/research"\).*?return \{"ok": True, "equipment": eq\}', replacement, content, flags=re.DOTALL)

with open('routers/base.py', 'w') as f:
    f.write(content)
print('Done!')
