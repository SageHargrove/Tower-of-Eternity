from fastapi import APIRouter, HTTPException
from database import db
from services.gacha_service import pull_rarity, generate_base_stats, generate_aptitudes, get_pull_cost
from services.llm_service import generate_hero_profile
from services.portrait_cache import pop_cached_portrait, rename_portrait_for_hero, queue_custom_portrait
from services.class_service import assign_class, can_pilot
from services.level_service import recalculate_hero_level
from services.skills_service import assign_initial_skills
from pydantic import BaseModel
import json

router = APIRouter()

class PullRequest(BaseModel):
    count: int = 1

@router.post("/pull")
def pull_heroes(req: PullRequest):
    if req.count < 1 or req.count > 10:
        raise HTTPException(status_code=400, detail="Pull 1-10 heroes at a time")

    cost = 900 if req.count == 10 else 100 * req.count

    with db() as conn:
        base_row = conn.execute("SELECT gems FROM base WHERE id = 1").fetchone()
        if not base_row or base_row["gems"] < cost:
            raise HTTPException(status_code=400, detail=f"Not enough gems. Need {cost} Gems.")
        conn.execute("UPDATE base SET gems = gems - ? WHERE id = 1", (cost,))

    import random
    synergy_group_name = None
    synergy_indices = set()
    synergy_leader_idx = -1
    synergy_theme_desc = ""

    if req.count == 10 and random.random() < 0.25:
        themes = [
            ("The Crimson Vanguard", "wearing identical crimson cloaks and silver armor"),
            ("The Obsidian Order", "clad in heavy dark armor with violet glowing runes"),
            ("The Silent Brotherhood", "wearing dark leather rogue gear with hidden blades"),
            ("The Azure Circle", "wearing elegant blue mage robes with glowing staffs"),
            ("The Ironclads", "massive heavy plate armor and tower shields"),
            ("The Exiled Royalty", "tattered, ruined royal finery and broken crowns"),
            ("The Bloodmoon Sect", "crimson cultist robes with bone masks"),
        ]
        chosen = random.choice(themes)
        synergy_group_name = chosen[0]
        synergy_theme_desc = chosen[1]
        
        num_synergy = random.randint(3, 5)
        synergy_indices = set(random.sample(range(10), num_synergy))
        
        if random.random() < 0.20:
            synergy_leader_idx = random.choice(list(synergy_indices))

    results = []
    rolled_rarities = [pull_rarity() for _ in range(req.count)]
    
    if synergy_group_name:
        follower_rarities = [rolled_rarities[i] for i in synergy_indices if i != synergy_leader_idx]
        max_follower_rarity = max(follower_rarities) if follower_rarities else 1
        rolled_rarities[synergy_leader_idx] = max(rolled_rarities[synergy_leader_idx], max_follower_rarity + 1)
        rolled_rarities[synergy_leader_idx] = min(7, rolled_rarities[synergy_leader_idx])

    for idx in range(req.count):
        birth_star = rolled_rarities[idx]
        is_synergy = idx in synergy_indices
        is_leader = idx == synergy_leader_idx
        current_synergy = synergy_group_name if is_synergy else None

        # ─── Pity system ───
        with db() as conn:
            base_row = conn.execute("SELECT pity_counter, spark_points FROM base WHERE id = 1").fetchone()
            pity = (base_row["pity_counter"] if base_row else 0) or 0
            sparks = (base_row["spark_points"] if base_row else 0) or 0

            pity += 1
            sparks += 1

            # Pity: guaranteed 4★+ after 50 pulls
            if pity >= 50 and birth_star < 4:
                birth_star = 4
                pity = 0  # Reset pity

            # Reset pity on natural 4★+
            if birth_star >= 4:
                pity = 0

            conn.execute("UPDATE base SET pity_counter = ?, spark_points = ? WHERE id = 1",
                         (pity, sparks))

        stats = generate_base_stats(birth_star)
        aptitudes = generate_aptitudes(birth_star)
        
        cached_data = pop_cached_portrait(birth_star)
        old_path, p_gender, p_class = cached_data if cached_data else (None, None, None)
        
        hero_class, hidden_class = assign_class(birth_star)
        if p_class:
            hero_class = p_class
            
        # Assign starting skills and traits
        from services.skills_service import assign_initial_skills
        from services.traits_service import generate_traits
        skills = assign_initial_skills(hero_class, birth_star)
        skills_json = json.dumps(skills)
        traits = generate_traits(birth_star)
        traits_json = json.dumps(traits)

        # Basic stat scaling logic
        # 1-star: 1x, 2-star: 1.5x, 3-star: 2x, 4-star: 3x, 5-star: 4.5x, 6-star: 7x, 7-star: 10x
        multipliers = {1: 1.0, 2: 1.5, 3: 2.0, 4: 3.0, 5: 4.5, 6: 7.0, 7: 10.0}
        mult = multipliers.get(birth_star, 1.0)
        pilot = 1 if can_pilot(hero_class) else 0

        # Force leader to have higher aptitudes to ensure they are visibly stronger
        if is_leader:
            for k in aptitudes:
                aptitudes[k] = min(100, aptitudes[k] + random.randint(10, 20))
            stats["max_hp"] += 25
            stats["hp"] = stats["max_hp"]
            stats["attack"] += 5
            stats["defense"] += 3

        # LLM text generation with fallback
        llm_ok = True
        try:
            extra_prompt = ""
            if is_synergy:
                extra_prompt = f" Make them a member of {current_synergy}. In the visual prompt, describe them {synergy_theme_desc}."
            if is_leader:
                extra_prompt += " They are the powerful LEADER of this group."
            
            if p_class:
                extra_prompt += f" This hero's class is {p_class}."
            if p_gender and p_gender != "unknown":
                extra_prompt += f" This hero is {p_gender}."
                
            profile = generate_hero_profile(birth_star, aptitudes, extra_prompt)
        except Exception as e:
            print(f"LLM profile failed: {e}")
            llm_ok = False
            import random
            male_fallback_names = [
                "Valerius", "Kaelen", "Tavian", "Rykard", "Jerrick", "Darius", "Fenris", "Corvus", "Sylas", "Bram",
                "Thorne", "Lysander", "Rowan", "Orion", "Soren", "Caelum", "Silas", "Evander", "Theron", "Aelar",
                "Zephyr", "Kael", "Ignis", "Sol", "Alistair", "Lucius", "Gideon", "Caius", "Marcus", "Eldric", "Finn",
                "Ronan", "Declan", "Aldous", "Vane", "Kaelan", "Orik", "Varian", "Zane", "Jax", "Lars", "Rex"
            ]
            female_fallback_names = [
                "Elara", "Seris", "Isolde", "Nia", "Lorien", "Vanya", "Myra", "Gael", "Aria", "Cassia", "Kira", "Eira",
                "Vesper", "Juno", "Nyssa", "Lirael", "Rhea", "Lyra", "Nyx", "Nova", "Aura", "Seraphina", "Lumina",
                "Thalia", "Vespera", "Celeste", "Iris", "Maeve", "Senna", "Talia", "Ayla", "Mira", "Lina", "Cia"
            ]
            fallback_surnames = [
                "Blackwood", "Vane", "Ash", "Storm", "Frost", "Gale", "Silver", "Iron", "Crow", "Hawk",
                "Dusk", "Dawn", "Wraith", "Grim", "Vale", "Thorn", "Shadow", "Drake", "Wolf", "Moon",
                "Blood", "Blade", "Stone", "Fire", "Star", "Sun", "Night", "Day", "Sky", "Sea", "River",
                "Winter", "Summer", "Autumn", "Spring", "Gold", "Steel", "Copper", "Brass", "Glass"
            ]
            fallback_titles = [
                "the Forsaken", "the Lost", "the Wanderer", "the Quiet", "the Exile", "the Broken",
                "the Swift", "the Resolute", "the Shadow", "the Undying", "the Vengeful", "the Silent",
                "the Bloodied", "the Merciful", "the Iron-Willed", "the Fearless", "the Accursed", "the Blessed",
                "the Cursed", "the Damned", "the Doomed", "the Fated", "the Destined", "the Chosen"
            ]
            fallback_backstories = [
                "They have forgotten their past, or perhaps they simply refuse to speak of it. Only the tower remains for them.",
                "A former soldier from a ruined kingdom. They seek redemption in the endless floors.",
                "Born in the slums, they fought tooth and nail to survive. Now, they fight for gold.",
                "An exile from a noble house, stripped of their name and lands. They have nothing left to lose.",
                "A wandering mercenary who goes wherever the coin flows. The tower is just another job.",
                "They claim to be a hero from a forgotten age, awakened to climb the tower.",
                "A rogue mage who dabbled in forbidden arts. They seek ancient knowledge hidden in the spire.",
                "A sole survivor of a mercenary band wiped out on the lower floors. They climb to avenge their comrades.",
                "They woke up in the tower with no memory of how they got here. They climb to find answers.",
                "A zealot of a forgotten god, believing the top of the tower holds salvation."
            ]
            
            class FallbackProfile:
                pass
                
            profile = FallbackProfile()
            profile.gender = random.choice(["male", "female"])
            profile.name = random.choice(male_fallback_names if profile.gender == "male" else female_fallback_names) + " " + random.choice(fallback_surnames)
            profile.title = random.choice(fallback_titles)
            profile.backstory = random.choice(fallback_backstories)
            profile.personality = "Watchful and silent."
            
            from services.portrait_cache import build_varied_prompt
            profile.portrait_prompt = build_varied_prompt(birth_star, getattr(profile, "gender", "unknown"))[0]
            
            if is_synergy:
                profile.portrait_prompt += f", {synergy_theme_desc}"

        # Claim cached portrait instantly, or use default placeholder
        if old_path:
            portrait_path = old_path
        else:
            # No cached portrait available — use a default and queue generation
            portrait_path = f"static/portraits/default_{hero_class.lower().replace(' ', '_')}.png"

        with db() as conn:
            cursor = conn.execute("""
                INSERT INTO heroes (
                    name, title, backstory, personality, portrait_path, gender,
                    birth_star, hero_class, hidden_class, can_pilot, level, skills, traits,
                    hp, max_hp, attack, defense, speed,
                    apt_combat, apt_tactical, apt_survival, apt_mental, apt_leadership,
                    synergy_group, ego_type
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                profile.name, profile.title, profile.backstory,
                profile.personality, portrait_path, getattr(profile, "gender", "unknown"),
                birth_star, hero_class, hidden_class, pilot, 1, skills_json, traits_json,
                stats["hp"], stats["max_hp"], stats["attack"], stats["defense"], stats["speed"],
                aptitudes["apt_combat"], aptitudes["apt_tactical"], aptitudes["apt_survival"],
                aptitudes["apt_mental"], aptitudes["apt_leadership"],
                current_synergy, getattr(profile, "ego_type", None)
            ))
            hero_id = cursor.lastrowid
            
            # Convert cached image to a permanent custom image instantly
            if portrait_path and "cached_" in portrait_path:
                import os, time
                import database
                custom_dir = f"static/portraits/{database.ACTIVE_PROFILE}"
                os.makedirs(custom_dir, exist_ok=True)
                safe_name = profile.name.replace(" ", "_").lower()
                new_path = f"{custom_dir}/custom_hero_{hero_id}_{safe_name}_{int(time.time())}.png"
                try:
                    os.rename(portrait_path, new_path)
                    conn.execute("UPDATE heroes SET portrait_path = ? WHERE id = ?", (new_path, hero_id))
                    conn.execute("DELETE FROM portrait_cache WHERE path = ?", (portrait_path,))
                    portrait_path = new_path
                except Exception as e:
                    print(f"Failed to rename cached portrait: {e}")

            hero = conn.execute("SELECT * FROM heroes WHERE id = ?", (hero_id,)).fetchone()
            results.append(dict(hero))

        # Queue custom portrait in background if we used a fallback placeholder
        if "default_" in portrait_path:
            queue_custom_portrait(hero_id, profile.portrait_prompt, profile.name, getattr(profile, "gender", "unknown"))

    with db() as conn:
        base_row = conn.execute("SELECT gems FROM base WHERE id = 1").fetchone()
        new_gems = base_row["gems"] if base_row else 0

    return {"pulled": results, "cost": cost, "gems": new_gems}

@router.get("/odds")
def get_odds():
    from services.gacha_service import RARITY_WEIGHTS, TOTAL_WEIGHT
    return {
        str(star): {
            "weight": w,
            "percent": round(w / TOTAL_WEIGHT * 100, 4)
        }
        for star, w in RARITY_WEIGHTS.items()
    }

@router.get("/cache-status")
def cache_status():
    from services.portrait_cache import get_cache_counts
    counts = get_cache_counts()
    return {"available": counts, "total": sum(counts.values())}

@router.get("/class-info")
def class_info():
    from services.class_service import CLASS_ICONS, CLASS_DESCRIPTIONS
    return {"icons": CLASS_ICONS, "descriptions": CLASS_DESCRIPTIONS}


@router.get("/pity-info")
def pity_info():
    """Get current pity counter and spark points."""
    with db() as conn:
        base = conn.execute("SELECT pity_counter, spark_points FROM base WHERE id = 1").fetchone()
        pity = (base["pity_counter"] if base else 0) or 0
        sparks = (base["spark_points"] if base else 0) or 0
    return {
        "pity_counter": pity,
        "pity_threshold": 50,
        "pulls_until_pity": max(0, 50 - pity),
        "spark_points": sparks,
        "spark_threshold": 100,
        "sparks_until_redeem": max(0, 100 - sparks),
    }


@router.post("/spark-redeem")
def spark_redeem():
    """Spend 100 spark points for a guaranteed random 5★ hero."""
    with db() as conn:
        base = conn.execute("SELECT spark_points, gold FROM base WHERE id = 1").fetchone()
        sparks = (base["spark_points"] if base else 0) or 0
        if sparks < 100:
            raise HTTPException(status_code=400, detail=f"Need 100 spark points. Have {sparks}.")

        # Deduct sparks
        conn.execute("UPDATE base SET spark_points = spark_points - 100 WHERE id = 1")

    # Pull a guaranteed 5★ using the normal pull mechanism but overriding rarity
    from services.gacha_service import generate_base_stats, generate_aptitudes
    from services.portrait_cache import pop_cached_portrait, rename_portrait_for_hero, queue_custom_portrait
    from services.class_service import assign_class, can_pilot

    birth_star = 5  # guaranteed 5★
    stats = generate_base_stats(birth_star)
    aptitudes = generate_aptitudes(birth_star)
    
    cached_data = pop_cached_portrait(birth_star)
    old_path, p_gender, p_class = cached_data if cached_data else (None, None, None)
    
    hero_class, hidden_class = assign_class(birth_star)
    if p_class:
        hero_class = p_class
        
    pilot = 1 if can_pilot(hero_class) else 0
    skills = assign_initial_skills(hero_class, birth_star)
    skills_json = json.dumps(skills)
    
    from services.traits_service import generate_traits
    traits = generate_traits(birth_star)
    traits_json = json.dumps(traits)

    try:
        extra_prompt = ""
        if p_class:
            extra_prompt += f" This hero's class is {p_class}."
        if p_gender and p_gender != "unknown":
            extra_prompt += f" This hero is {p_gender}."
        profile = generate_hero_profile(birth_star, aptitudes, extra_prompt)
    except Exception:
        class FallbackProfile:
            name = f"Spark Champion"
            title = "Born of Determination"
            backstory = "Summoned through sheer persistence and accumulated will."
            personality = "Resolute. Unbreakable."
            gender = "unknown"
            portrait_prompt = "dark fantasy anime warrior portrait, 5 star champion, golden aura"
        profile = FallbackProfile()

    if old_path:
        portrait_path = old_path
    else:
        portrait_path = f"static/portraits/default_{hero_class.lower().replace(' ', '_')}.png"

    with db() as conn:
        cursor = conn.execute("""
            INSERT INTO heroes (
                name, title, backstory, personality, portrait_path, gender,
                birth_star, hero_class, hidden_class, can_pilot, level, skills, traits,
                hp, max_hp, attack, defense, speed,
                apt_combat, apt_tactical, apt_survival, apt_mental, apt_leadership
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            profile.name, profile.title, profile.backstory,
            profile.personality, portrait_path, getattr(profile, "gender", "unknown"),
            birth_star, hero_class, hidden_class, pilot, 1, skills_json, traits_json,
            stats["hp"], stats["max_hp"], stats["attack"],
            stats["defense"], stats["speed"],
            aptitudes["apt_combat"], aptitudes["apt_tactical"],
            aptitudes["apt_survival"], aptitudes["apt_mental"],
            aptitudes["apt_leadership"],
        ))
        hero_id = cursor.lastrowid
        
        # Convert cached image to a permanent custom image instantly
        if portrait_path and "cached_" in portrait_path:
            import os, time
            import database
            custom_dir = f"static/portraits/{database.ACTIVE_PROFILE}"
            os.makedirs(custom_dir, exist_ok=True)
            safe_name = profile.name.replace(" ", "_").lower()
            new_path = f"{custom_dir}/custom_spark_{hero_id}_{safe_name}_{int(time.time())}.png"
            try:
                os.rename(portrait_path, new_path)
                conn.execute("UPDATE heroes SET portrait_path = ? WHERE id = ?", (new_path, hero_id))
                conn.execute("DELETE FROM portrait_cache WHERE path = ?", (portrait_path,))
                portrait_path = new_path
            except Exception as e:
                print(f"Failed to rename cached portrait: {e}")
                
        hero = conn.execute("SELECT * FROM heroes WHERE id = ?", (hero_id,)).fetchone()

    try:
        queue_custom_portrait(hero_id, profile.portrait_prompt, profile.name, getattr(profile, "gender", "unknown"))
    except Exception:
        pass

    return {"hero": dict(hero), "spark_cost": 100}