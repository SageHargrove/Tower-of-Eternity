from database import db
import random

def auto_assign_ego_team(ego_hero_id: int, team_id: int) -> list[int]:
    """
    Given an Ego Hero's ID, clear the current team and pick an optimal team
    based on their specific Ego Type.
    """
    with db() as conn:
        ego_hero = conn.execute("SELECT * FROM heroes WHERE id = ?", (ego_hero_id,)).fetchone()
        if not ego_hero:
            raise ValueError("Ego hero not found.")
            
        ego_type = ego_hero["ego_type"]
        if not ego_type:
            raise ValueError("Hero does not have an Ego.")

        alive_heroes = [dict(r) for r in conn.execute("SELECT * FROM heroes WHERE is_alive = 1 AND id != ?", (ego_hero_id,)).fetchall()]
        
    team = [ego_hero_id]
    
    # Sort alive_heroes based on the algorithm
    if ego_type == "Aggressive":
        # Prioritize high attack and speed
        alive_heroes.sort(key=lambda h: (h["attack"] + h["speed"]), reverse=True)
    elif ego_type == "Cautious":
        # Prioritize high defense, max_hp, and Clerics/Paladins
        alive_heroes.sort(key=lambda h: (h["defense"] + h["max_hp"] + (100 if h["hero_class"] in ["Cleric", "Paladin"] else 0)), reverse=True)
    elif ego_type == "Tactical":
        # Prioritize apt_tactical and diverse classes
        alive_heroes.sort(key=lambda h: h["apt_tactical"], reverse=True)
    elif ego_type == "Leader":
        # Prioritize lower level heroes to 'mentor' them (or high leadership)
        alive_heroes.sort(key=lambda h: (h["level"], -h["apt_leadership"]))
    elif ego_type == "Lone Wolf":
        # Refuses to team up with anyone unless they are extremely weak (meat shields)
        alive_heroes.sort(key=lambda h: (h["hp"] + h["attack"]))
    else:
        # Default: just grab highest level
        alive_heroes.sort(key=lambda h: h["level"], reverse=True)
        
    # Take top 4 to fill team of 5
    for h in alive_heroes[:4]:
        team.append(h["id"])
        
    # Save the new team
    with db() as conn:
        conn.execute("UPDATE heroes SET is_on_team = 0 WHERE is_on_team = ?", (team_id,))
        for idx, hid in enumerate(team):
            conn.execute("UPDATE heroes SET is_on_team = ?, team_position = ? WHERE id = ?", (team_id, idx, hid))
            
    return team
