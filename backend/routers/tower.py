from fastapi import APIRouter, HTTPException
from database import db
from services.combat_service import run_combat
from services.morale_service import between_floor_recovery, witness_death_trauma, get_morale_state, apply_morale_delta, apply_stress, apply_trauma
from services.llm_service import generate_combat_narration, generate_event_narrative, generate_event_resolution_narrative
from services.event_service import select_event, resolve_event_choice
from services.floor_templates import (
    get_floor_type,
    generate_survival_floor, resolve_survival_floor,
    generate_defend_floor, resolve_defend_floor,
    generate_explore_floor, resolve_explore_floor,
    generate_escort_floor, resolve_escort_floor,
    generate_rest_floor, resolve_rest_floor,
)
import json
import random
from pydantic import BaseModel

router = APIRouter()

class EnterFloorRequest(BaseModel):
    team_id: int
    floor_number: int

@router.post("/floor/enter")
def enter_floor(req: EnterFloorRequest):
    """Resolve a single floor for a specific team without any 'Run' constraints."""
    with db() as conn:
        # Check base and supplies
        base_row = conn.execute("SELECT highest_floor, supplies FROM base WHERE id = 1").fetchone()
        if not base_row:
            raise HTTPException(status_code=500, detail="Base not found")
            
        if req.floor_number > base_row["highest_floor"] + 1:
            raise HTTPException(status_code=400, detail="Cannot skip floors.")

        supply_cost = 2
        if base_row["supplies"] < supply_cost:
            raise HTTPException(status_code=400, detail=f"Not enough supplies to enter the tower. Need {supply_cost}.")

        # Get heroes
        heroes = [dict(r) for r in conn.execute(
            "SELECT * FROM heroes WHERE is_on_team = ? AND is_alive = 1 ORDER BY team_position ASC, id ASC", (req.team_id,)
        ).fetchall()]
        
        if not heroes:
            raise HTTPException(status_code=400, detail=f"No heroes assigned to Team {req.team_id}.")

        for hero in heroes:
            if hero["fatigue"] >= 10:
                raise HTTPException(status_code=400, detail=f"{hero['name']} is exhausted (Fatigue 10) and must rest before entering the tower.")

        conn.execute("UPDATE base SET supplies = supplies - ? WHERE id = 1", (supply_cost,))

        from services.llm_service import generate_zone_theme
        zone_theme = generate_zone_theme(req.floor_number)
        floor_type = get_floor_type(req.floor_number)
        hero_list = [dict(h) for h in heroes]

        result = {}
        narrative = None

        # Resolve Floor Logic
        if floor_type in ("combat", "miniboss", "boss"):
            is_boss = floor_type == "boss"
            is_miniboss = floor_type == "miniboss"
            
            try:
                combat_result = run_combat(hero_list, req.floor_number, is_boss=is_boss, is_miniboss=is_miniboss, zone_theme=zone_theme)
            except Exception as e:
                print(f"Combat error: {e}")
                raise HTTPException(status_code=500, detail=f"Combat simulation failed: {str(e)}")
            
            result["combat"] = combat_result
            
            if combat_result["winner"] == "heroes":
                result["message"] = f"Floor {req.floor_number} Cleared!"
            else:
                result["message"] = f"Team defeated on Floor {req.floor_number}."
                result["run_over"] = True

            try:
                narrative = generate_combat_narration(zone_theme, combat_result)
            except Exception as e:
                print(f"Narration error: {e}")
                narrative = "A fierce battle took place."
                
            for dead_hero_row in combat_result["dead_heroes"]:
                dead_id = dead_hero_row if isinstance(dead_hero_row, int) else dead_hero_row["id"]
                conn.execute("UPDATE heroes SET is_alive = 0, is_on_team = 0 WHERE id = ?", (dead_id,))
                try:
                    from services.legacy_service import create_legacy
                    # If dead_hero_row is an int, we need to fetch the hero row for create_legacy
                    if isinstance(dead_hero_row, int):
                        hr = conn.execute("SELECT * FROM heroes WHERE id = ?", (dead_id,)).fetchone()
                        if hr:
                            create_legacy(dict(hr))
                    else:
                        create_legacy(dead_hero_row)
                except Exception:
                    pass

            if combat_result["winner"] != "heroes" and not combat_result["surviving_heroes"]:
                return {"result": "failed", "floor": req.floor_number, "log": combat_result["log"]}

            for surviving in combat_result["surviving_heroes"]:
                trauma_data = witness_death_trauma(is_close_ally=True)
                conn.execute("""
                    UPDATE heroes SET
                        trauma = MIN(100, trauma + ?),
                        stress = MIN(100, stress + ?)
                    WHERE id = ?
                """, (len(combat_result["dead_heroes"]) * trauma_data["trauma_delta"], 
                      len(combat_result["dead_heroes"]) * trauma_data["stress_delta"], surviving["id"]))

            for s in combat_result["surviving_heroes"]:
                hid = s["id"]
                hero_row = conn.execute("SELECT morale, trauma, skills FROM heroes WHERE id = ?", (hid,)).fetchone()
                if hero_row:
                    hero_dict = dict(hero_row)
                    new_morale = apply_morale_delta(hero_dict["morale"], hero_dict["trauma"], s["morale_delta"])
                    
                    # Apply skill upgrades if any
                    skills_json = hero_dict["skills"]
                    if hid in combat_result.get("skill_upgrades", {}):
                        upgrades = combat_result["skill_upgrades"][hid]
                        skills = json.loads(skills_json) if skills_json else []
                        for upg in upgrades:
                            for sk in skills:
                                if sk["id"] == upg["skill_id"]:
                                    sk["tier"] = upg["new_tier"]
                                    sk["level"] = 1
                                    sk["xp"] = 0
                                    sk["max_xp"] = 100
                        skills_json = json.dumps(skills)
                    
                    conn.execute("""
                        UPDATE heroes SET hp = MIN(max_hp, ?), morale = ?, morale_state = ?, skills = ? WHERE id = ?
                    """, (s["hp"], new_morale, get_morale_state(new_morale), skills_json, s["id"]))

            # Copy rewards to result so frontend can see them
            result["gold_gained"] = combat_result.get("gold_gained", 0)
            result["supplies_gained"] = combat_result.get("supplies_gained", 0)
            result["materials_gained"] = combat_result.get("materials_gained", {})
            
            # Apply 5% penalty for repeated runs
            if req.floor_number <= base_row["highest_floor"]:
                result["gold_gained"] = int(result["gold_gained"] * 0.05)
                result["supplies_gained"] = int(result["supplies_gained"] * 0.05)
                for m in list(result["materials_gained"].keys()):
                    if random.random() > 0.1:
                        result["materials_gained"][m] = 0
                result["materials_gained"] = {k:v for k,v in result["materials_gained"].items() if v > 0}

            if result["gold_gained"] > 0 or result["supplies_gained"] > 0 or result["materials_gained"]:
                conn.execute(
                    "UPDATE base SET gold = gold + ?, supplies = supplies + ? WHERE id = 1",
                    (result["gold_gained"], result["supplies_gained"])
                )
                if result["materials_gained"]:
                    base_row_current = conn.execute("SELECT materials FROM base WHERE id = 1").fetchone()
                    current_mats = json.loads(base_row_current["materials"]) if base_row_current["materials"] else {}
                    for m, qty in result["materials_gained"].items():
                        current_mats[m] = current_mats.get(m, 0) + qty
                    conn.execute("UPDATE base SET materials = ? WHERE id = 1", (json.dumps(current_mats),))

            if combat_result.get("equipment_drop"):
                try:
                    from services.equipment_service import save_equipment
                    save_equipment(combat_result["equipment_drop"])
                    result["equipment_drop"] = combat_result["equipment_drop"]
                except Exception as e:
                    print(f"Failed to save drop: {e}")

            result["floor_type"] = "combat"
            result["narrative"] = narrative

        elif floor_type == "event":
            event_data = select_event(req.floor_number, zone_theme)
            try:
                narrative = generate_event_narrative(zone_theme, event_data, [h["name"] for h in hero_list])
            except:
                narrative = event_data["description"]
                
            result = {
                "floor_type": "event",
                "event": event_data,
                "event_narrative": narrative,
                "awaiting_choice": True,
                "theme": zone_theme
            }

        elif floor_type == "survival":
            template = generate_survival_floor(req.floor_number)
            resolution = resolve_survival_floor(template, hero_list)
            for hr in resolution["hero_results"]:
                conn.execute("UPDATE heroes SET hp = MIN(max_hp, ?), stress = MIN(100, stress + ?) WHERE id = ?",
                             (hr["hp"], hr.get("stress_gained", 0), hr["id"]))
            if resolution.get("reward", {}).get("gold"):
                conn.execute("UPDATE base SET gold = gold + ? WHERE id = 1",
                             (resolution["reward"]["gold"],))
            result = {
                "floor_type": "survival",
                "resolution": resolution,
                "narrative": resolution["summary"],
                "log": resolution["log"],
            }

        elif floor_type == "defend":
            template = generate_defend_floor(req.floor_number)
            resolution = resolve_defend_floor(template, hero_list)
            for hr in resolution["hero_results"]:
                hero_data = next((h for h in hero_list if h["id"] == hr["id"]), None)
                if hero_data:
                    new_morale = max(0, min(100, hero_data["morale"] + hr.get("morale_delta", 0)))
                    conn.execute("UPDATE heroes SET hp = MIN(max_hp, ?), morale = ?, morale_state = ? WHERE id = ?",
                                 (hr["hp"], new_morale, get_morale_state(new_morale), hr["id"]))
            if resolution.get("reward", {}).get("gold"):
                conn.execute("UPDATE base SET gold = gold + ? WHERE id = 1",
                             (resolution["reward"]["gold"],))
            result = {
                "floor_type": "defend",
                "resolution": resolution,
                "narrative": resolution["summary"],
                "log": resolution["log"],
            }

        elif floor_type == "explore":
            template = generate_explore_floor(req.floor_number)
            resolution = resolve_explore_floor(template, "thorough", hero_list)
            for hr in resolution["hero_results"]:
                conn.execute("UPDATE heroes SET hp = MIN(max_hp, ?), stress = MIN(100, stress + ?) WHERE id = ?",
                             (hr["hp"], hr.get("stress_gained", 0), hr["id"]))
            loot = resolution.get("loot", {})
            if loot.get("type") == "gold":
                conn.execute("UPDATE base SET gold = gold + ? WHERE id = 1", (loot.get("amount", 0),))
            elif loot.get("type") in ("materials", "rare_materials"):
                base_row = conn.execute("SELECT materials FROM base WHERE id = 1").fetchone()
                current_mats = json.loads(base_row["materials"]) if base_row["materials"] else {}
                mat_name = loot.get("type", "materials")
                current_mats[mat_name] = current_mats.get(mat_name, 0) + loot.get("amount", 1)
                conn.execute("UPDATE base SET materials = ? WHERE id = 1", (json.dumps(current_mats),))
            result = {
                "floor_type": "explore",
                "resolution": resolution,
                "narrative": resolution["summary"],
                "log": resolution["log"],
            }

        elif floor_type == "escort":
            template = generate_escort_floor(req.floor_number)
            resolution = resolve_escort_floor(template, hero_list)
            for hr in resolution["hero_results"]:
                hero_data = next((h for h in hero_list if h["id"] == hr["id"]), None)
                if hero_data:
                    new_morale = max(0, min(100, hero_data["morale"] + hr.get("morale_delta", 0)))
                    conn.execute("UPDATE heroes SET hp = MIN(max_hp, ?), morale = ?, morale_state = ? WHERE id = ?",
                                 (hr["hp"], new_morale, get_morale_state(new_morale), hr["id"]))
            if resolution.get("reward", {}).get("gold"):
                conn.execute("UPDATE base SET gold = gold + ? WHERE id = 1",
                             (resolution["reward"]["gold"],))
            result = {
                "floor_type": "escort",
                "resolution": resolution,
                "narrative": resolution["summary"],
                "log": resolution["log"],
            }

        elif floor_type == "rest":
            template = generate_rest_floor(req.floor_number)
            resolution = resolve_rest_floor(template, hero_list)
            for hr in resolution["hero_results"]:
                hero_data = next((h for h in hero_list if h["id"] == hr["id"]), None)
                if hero_data:
                    new_morale = max(0, min(100, hero_data["morale"] + hr.get("morale_delta", 0)))
                    new_stress = max(0, hero_data["stress"] + hr.get("stress_gained", 0))
                    conn.execute("UPDATE heroes SET hp = MIN(max_hp, ?), morale = ?, stress = ?, morale_state = ? WHERE id = ?",
                                 (hr["hp"], new_morale, new_stress, get_morale_state(new_morale), hr["id"]))
            result = {
                "floor_type": "rest",
                "resolution": resolution,
                "narrative": resolution["summary"],
                "log": resolution["log"],
            }

        # Add fatigue to deployed heroes
        conn.execute(
            """
            UPDATE heroes 
            SET fatigue = MIN(10, fatigue + 1) 
            WHERE is_on_team = ? AND is_alive = 1
            """,
            (req.team_id,)
        )

        from services.level_service import recalculate_hero_level, level_up_summary
        surviving_ids = []
        
        survivors = []
        if result.get("combat") and "surviving_heroes" in result["combat"]:
            survivors = result["combat"]["surviving_heroes"]
        elif not result.get("run_over"):
            survivors = hero_list

        for s in survivors:
            hid = s["id"]
            surviving_ids.append(hid)
            kills_gained = s.get("kills_gained", 0)
            stress_delta = s.get("stress_delta", 0)
            conn.execute("""
                UPDATE heroes SET
                    floors_survived = floors_survived + 1,
                    kills = kills + ?,
                    stress = MIN(100, MAX(0, stress + ?))
                WHERE id = ?
            """, (kills_gained, stress_delta, hid))

            # Recalculate level
            hero_row = conn.execute("SELECT * FROM heroes WHERE id = ?", (hid,)).fetchone()
            if hero_row:
                hero_dict = dict(hero_row)
                old_level = hero_dict.get("level", 1)
                new_level = recalculate_hero_level(hero_dict)
                if new_level != old_level:
                    conn.execute("UPDATE heroes SET level = ? WHERE id = ?", (new_level, hid))
                    level_msgs = level_up_summary(old_level, new_level, hero_dict["name"])
                    result.setdefault("level_ups", []).extend(level_msgs)

        if len(surviving_ids) >= 2:
            for i in range(len(surviving_ids)):
                for j in range(i + 1, len(surviving_ids)):
                    a, b = min(surviving_ids[i], surviving_ids[j]), max(surviving_ids[i], surviving_ids[j])
                    conn.execute("""
                        INSERT INTO hero_bonds (hero_a_id, hero_b_id, bond_level, floors_together)
                        VALUES (?, ?, 1, 1)
                        ON CONFLICT(hero_a_id, hero_b_id) DO UPDATE SET
                            floors_together = floors_together + 1,
                            bond_level = floors_together / 5
                    """, (a, b))

        # IMPORTANT: Between floor recovery applied immediately since we return to base instantly!
        for hid in surviving_ids:
            hero_row = conn.execute("SELECT * FROM heroes WHERE id = ?", (hid,)).fetchone()
            if hero_row:
                recovery = between_floor_recovery(dict(hero_row))
                conn.execute("""
                    UPDATE heroes SET morale = ?, stress = ?, trauma = ?, morale_state = ? WHERE id = ?
                """, (recovery["morale"], recovery["stress"], recovery["trauma"], recovery["morale_state"], hid))

        if not result.get("run_over") and req.floor_number > base_row["highest_floor"]:
            gems_reward = 500 if req.floor_number % 5 == 0 else 100
            conn.execute("UPDATE base SET highest_floor = ?, gems = gems + ? WHERE id = 1", (req.floor_number, gems_reward))
            result["gems_gained"] = gems_reward

    result["floor"] = req.floor_number
    return result

class ResolveEventRequest(BaseModel):
    floor_number: int
    team_id: int
    template_id: str
    choice_id: str
    theme: str = "An event occurred."

@router.post("/floor/event/resolve")
def resolve_event_floor(data: ResolveEventRequest):
    """Resolve a player's event floor choice."""
    with db() as conn:
        heroes = conn.execute(
            "SELECT * FROM heroes WHERE is_on_team = ? AND is_alive = 1", (data.team_id,)
        ).fetchall()
        hero_list = [dict(h) for h in heroes]
        hero_names = [h["name"] for h in hero_list]

        resolution = resolve_event_choice(data.template_id, data.choice_id, hero_list)
        if "error" in resolution:
            raise HTTPException(status_code=400, detail=resolution["error"])

        effects = resolution["effects"]

        if "gold" in effects and effects["gold"] != 0:
            conn.execute("UPDATE base SET gold = gold + ? WHERE id = 1", (effects["gold"],))

        if "item" in effects:
            try:
                from services.equipment_service import save_equipment
                equip = {
                    "name": effects["item"],
                    "slot": "accessory",
                    "rarity": 6,
                    "stats": {"hp": 150, "atk": 15, "def": 10, "spd": 5},
                    "description": "A legendary artifact found in the tower."
                }
                save_equipment(equip)
            except Exception as e:
                print(f"Failed to grant event item: {e}")

        sacrificed_name = None
        if effects.get("sacrifice_hero") and hero_list:
            import random
            sacrificed = random.choice(hero_list)
            sacrificed_name = sacrificed["name"]
            conn.execute("UPDATE heroes SET is_alive = 0, is_on_team = 0 WHERE id = ?", (sacrificed["id"],))
            hero_list = [h for h in hero_list if h["id"] != sacrificed["id"]]
            try:
                from services.legacy_service import create_legacy
                create_legacy(sacrificed)
            except Exception:
                pass

        for hero in hero_list:
            hid = hero["id"]
            updates = []
            params = []

            if "hp_pct" in effects and effects["hp_pct"] != 0:
                hp_change = int(hero["max_hp"] * effects["hp_pct"])
                new_hp = max(1, min(hero["max_hp"], hero["hp"] + hp_change))
                updates.append("hp = ?")
                params.append(new_hp)

            if "morale" in effects and effects["morale"] != 0:
                new_morale = max(0, min(100, hero["morale"] + effects["morale"]))
                updates.append("morale = ?")
                params.append(new_morale)

            if "stress" in effects and effects["stress"] != 0:
                new_stress = max(0, min(100, hero["stress"] + effects["stress"]))
                updates.append("stress = ?")
                params.append(new_stress)

            if "trauma" in effects and effects["trauma"] != 0:
                new_trauma = max(0, min(100, hero["trauma"] + effects["trauma"]))
                updates.append("trauma = ?")
                params.append(new_trauma)

            if updates:
                params.append(hid)
                conn.execute(f"UPDATE heroes SET {', '.join(updates)} WHERE id = ?", params)

        try:
            narrative = generate_event_resolution_narrative(
                data.theme, resolution["choice_label"], effects, hero_names
            )
        except Exception:
            narrative = f"The party chose: {resolution['choice_label']}."
            
        base_row = conn.execute("SELECT highest_floor FROM base WHERE id = 1").fetchone()
        if data.floor_number > base_row["highest_floor"]:
            gems_reward = 500 if data.floor_number % 5 == 0 else 100
            conn.execute("UPDATE base SET highest_floor = ?, gems = gems + ? WHERE id = 1", (data.floor_number, gems_reward))
            effects["gems"] = gems_reward

    return {
        "ok": True,
        "choice_label": resolution["choice_label"],
        "effects": effects,
        "narrative": narrative,
    }
