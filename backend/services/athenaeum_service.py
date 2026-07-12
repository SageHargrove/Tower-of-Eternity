"""The Athenaeum — the company's research hall (unlocks at floor 8).

Five disciplines, four tiers each, studied one node at a time: assigned
scholars generate Insight per hour, and all of it flows into whichever node
is currently IN STUDY. Deeper tiers also demand an Aether unseal fee the
first time a study begins. Mastering two disciplines unseals their
CONFLUENCE — an emergent second-order tree no single school could hold.

Completed nodes grant permanent, roster-wide effects. Effect keys and who
consumes them:
  atk/int/agi/def/hp/luck/all _pct -> combat_service.resolve_hero_stats
  gold_pct / drop_pct             -> combat_service._apply_combat_drops
  passive_gen_pct                 -> time_service.process_passive_generation
  insight_pct                     -> this file's own rate calc
"""
import json
from datetime import datetime
from database import db

# Scholars: the same magical-academic classes the Mage Tower favors, plus
# Priests (theology counts). Multiplier on a scholar's personal output.
SCHOLAR_CLASS_MULT = {"Magic Engineer": 2.0, "Mage": 2.0, "Spellsword": 1.5, "Priest": 1.5}

# Insight cost per tier (T1-T4), and the Aether unseal fee charged the FIRST
# time a study on that node begins. Confluence nodes use the second rows.
TIER_INSIGHT = [12, 30, 70, 140]
TIER_AETHER = [0, 40, 140, 260]
CONF_INSIGHT = [90, 140, 200, 300]
CONF_AETHER = [200, 300, 420, 600]

DISCIPLINES = [
    {
        "id": "magic_foundations", "name": "Magic Foundations", "sigil": "✦",
        "flavor": "The grammar beneath every spell — runes, ley, and the elements.",
        "nodes": [
            {"id": "runic_literacy", "name": "Runic Literacy", "desc": "INT +4%", "effects": {"int_pct": 4}},
            {"id": "ley_attunement", "name": "Ley Attunement", "desc": "Willpower +6%", "effects": {"def_pct": 6}},
            {"id": "elemental_theory", "name": "Elemental Theory", "desc": "INT +6%", "effects": {"int_pct": 6}},
            {"id": "spellweave", "name": "Spellweave", "desc": "INT +8%, Willpower +4%", "effects": {"int_pct": 8, "def_pct": 4}},
        ],
    },
    {
        "id": "battle_tactics", "name": "Battle Tactics", "sigil": "⚔",
        "flavor": "Formation doctrine, drilled until the Tower stops surprising you.",
        "nodes": [
            {"id": "flanking_drill", "name": "Flanking Drill", "desc": "ATK +5%", "effects": {"atk_pct": 5}},
            {"id": "shield_wall", "name": "Shield Wall", "desc": "DEF +6%", "effects": {"def_pct": 6}},
            {"id": "war_horns", "name": "War Horns", "desc": "SPD +5%", "effects": {"agi_pct": 5}},
            {"id": "vanguard_doctrine", "name": "Vanguard Doctrine", "desc": "ATK +6%, SPD +3%", "effects": {"atk_pct": 6, "agi_pct": 3}},
        ],
    },
    {
        "id": "logistics", "name": "Logistics", "sigil": "⬡",
        "flavor": "Wars are won in the supply train. So are climbs.",
        "nodes": [
            {"id": "swift_logistics", "name": "Swift Logistics", "desc": "Passive gen +10%", "effects": {"passive_gen_pct": 10}},
            {"id": "deeper_pockets", "name": "Deeper Pockets", "desc": "Tower gold +8%", "effects": {"gold_pct": 8}},
            {"id": "caravan_routes", "name": "Caravan Routes", "desc": "Passive gen +15%", "effects": {"passive_gen_pct": 15}},
            {"id": "grand_depot", "name": "Grand Depot", "desc": "Tower gold +12%, drops +3%", "effects": {"gold_pct": 12, "drop_pct": 3}},
        ],
    },
    {
        "id": "warding", "name": "Warding", "sigil": "◈",
        "flavor": "Circles, thresholds, and the patience to draw them properly.",
        "nodes": [
            {"id": "threshold_glyphs", "name": "Threshold Glyphs", "desc": "HP +4%", "effects": {"hp_pct": 4}},
            {"id": "circle_of_salt", "name": "Circle of Salt", "desc": "DEF +5%", "effects": {"def_pct": 5}},
            {"id": "abjurers_patience", "name": "Abjurer's Patience", "desc": "HP +6%", "effects": {"hp_pct": 6}},
            {"id": "unbroken_seal", "name": "The Unbroken Seal", "desc": "HP +8%, DEF +4%", "effects": {"hp_pct": 8, "def_pct": 4}},
        ],
    },
    {
        "id": "beastcraft", "name": "Beastcraft", "sigil": "❋",
        "flavor": "What the Tower's creatures know, and how to make it yours.",
        "nodes": [
            {"id": "beast_tongue", "name": "Beast Tongue", "desc": "LUCK +6%", "effects": {"luck_pct": 6}},
            {"id": "pack_instinct", "name": "Pack Instinct", "desc": "SPD +4%", "effects": {"agi_pct": 4}},
            {"id": "apex_studies", "name": "Apex Studies", "desc": "ATK +4%, LUCK +4%", "effects": {"atk_pct": 4, "luck_pct": 4}},
            {"id": "chimeric_theory", "name": "Chimeric Theory", "desc": "Drops +5%", "effects": {"drop_pct": 5}},
        ],
    },
]

# Second-order confluences: master BOTH parent disciplines to unseal the
# knot, then study its tree like any other discipline (steeper costs).
CONFLUENCES = [
    {
        "id": "war_sorcery", "name": "War Sorcery", "sigil": "❖",
        "parents": ["magic_foundations", "battle_tactics"],
        "flavor": "Spells that scale with formation — the line IS the wand.",
        "nodes": [
            {"id": "battle_chant", "name": "Battle Chant", "desc": "INT +5%, ATK +3%", "effects": {"int_pct": 5, "atk_pct": 3}},
            {"id": "sigil_vanguard", "name": "Sigil of the Vanguard", "desc": "SPD +6%", "effects": {"agi_pct": 6}},
            {"id": "arcane_volley", "name": "Arcane Volley", "desc": "INT +8%", "effects": {"int_pct": 8}},
            {"id": "formation_arcanum", "name": "The Formation Arcanum", "desc": "ALL stats +3%", "effects": {"all_pct": 3}},
        ],
    },
    {
        "id": "warders_march", "name": "Warder's March", "sigil": "❖",
        "parents": ["logistics", "warding"],
        "flavor": "Supply lines under sanctified escort. Nothing spoils; nothing burns.",
        "nodes": [
            {"id": "warded_caravans", "name": "Warded Caravans", "desc": "Passive gen +20%", "effects": {"passive_gen_pct": 20}},
            {"id": "tithe_of_safety", "name": "Tithe of Safety", "desc": "Tower gold +10%", "effects": {"gold_pct": 10}},
            {"id": "bulwark_convoy", "name": "Bulwark Convoy", "desc": "DEF +6%, HP +4%", "effects": {"def_pct": 6, "hp_pct": 4}},
            {"id": "endless_train", "name": "The Endless Train", "desc": "Passive gen +25%, drops +4%", "effects": {"passive_gen_pct": 25, "drop_pct": 4}},
        ],
    },
    {
        "id": "wild_arcana", "name": "Wild Arcana", "sigil": "❖",
        "parents": ["magic_foundations", "beastcraft"],
        "flavor": "Beast-bonded spellcraft. The familiar was never just a pet.",
        "nodes": [
            {"id": "scent_for_secrets", "name": "Scent for Secrets", "desc": "Drops +6%", "effects": {"drop_pct": 6}},
            {"id": "familiar_bonds", "name": "Familiar Bonds", "desc": "INT +5%, LUCK +5%", "effects": {"int_pct": 5, "luck_pct": 5}},
            {"id": "primal_channeling", "name": "Primal Channeling", "desc": "ATK +6%, INT +4%", "effects": {"atk_pct": 6, "int_pct": 4}},
            {"id": "chimeric_court", "name": "The Chimeric Court", "desc": "ALL stats +3%, LUCK +6%", "effects": {"all_pct": 3, "luck_pct": 6}},
        ],
    },
]


def _ensure_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS athenaeum_studies (
            node_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'studying',
            progress REAL NOT NULL DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    try:
        conn.execute("ALTER TABLE base ADD COLUMN last_athenaeum_tick TIMESTAMP")
    except Exception:
        pass


def _node_index():
    """node_id -> (node def, insight cost, aether fee, tier idx, tree id, prereq node_id or None, is_confluence)"""
    idx = {}
    for d in DISCIPLINES:
        for t, n in enumerate(d["nodes"]):
            prereq = d["nodes"][t - 1]["id"] if t > 0 else None
            idx[n["id"]] = {"node": n, "insight": TIER_INSIGHT[t], "aether": TIER_AETHER[t],
                            "tier": t, "tree": d["id"], "prereq": prereq, "confluence": False}
    for c in CONFLUENCES:
        for t, n in enumerate(c["nodes"]):
            prereq = c["nodes"][t - 1]["id"] if t > 0 else None
            idx[n["id"]] = {"node": n, "insight": CONF_INSIGHT[t], "aether": CONF_AETHER[t],
                            "tier": t, "tree": c["id"], "prereq": prereq, "confluence": True}
    return idx


NODE_INDEX = _node_index()


def _completed_ids(conn):
    _ensure_schema(conn)
    rows = conn.execute("SELECT node_id FROM athenaeum_studies WHERE status = 'complete'").fetchall()
    return {r["node_id"] for r in rows}


def _discipline_mastered(disc_id: str, completed: set) -> bool:
    d = next(d for d in DISCIPLINES if d["id"] == disc_id)
    return all(n["id"] in completed for n in d["nodes"])


def get_insight_rate(conn):
    """(rate per hour, scholar count). Scales with facility level plus each
    assigned scholar's class and Mental aptitude."""
    fac = conn.execute("SELECT id, level FROM facilities WHERE type = 'Athenaeum' AND base_id = 1").fetchone()
    if not fac:
        return 0.0, 0
    scholars = conn.execute("""
        SELECT h.hero_class, h.apt_mental FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1
    """, (fac["id"],)).fetchall()
    rate = 0.4 * fac["level"]
    for s in scholars:
        mult = SCHOLAR_CLASS_MULT.get(s["hero_class"], 1.0)
        rate += mult * (0.5 + ((s["apt_mental"] or 50) / 100.0))
    # Completed insight_pct research feeds back into the rate itself.
    bonuses = get_research_bonuses(conn)
    rate *= 1.0 + bonuses.get("insight_pct", 0) / 100.0
    # Blacksmith · Artificer (Runework): runic instruments speed every study.
    try:
        from services.support_service import get_support_effects
        rate *= 1.0 + get_support_effects(conn).get("smith_research_pct", 0) / 100.0
    except Exception:
        pass
    return round(rate, 2), len(scholars)


def process_athenaeum(conn):
    """Tick: all Insight flows into the single node currently in study."""
    _ensure_schema(conn)
    fac = conn.execute("SELECT id FROM facilities WHERE type = 'Athenaeum' AND base_id = 1").fetchone()
    if not fac:
        return

    base = conn.execute("SELECT last_athenaeum_tick FROM base WHERE id = 1").fetchone()
    last_tick_str = dict(base).get("last_athenaeum_tick") if base else None
    if not last_tick_str:
        conn.execute("UPDATE base SET last_athenaeum_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return
    try:
        last_tick = datetime.strptime(last_tick_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        conn.execute("UPDATE base SET last_athenaeum_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return

    minutes = int((datetime.utcnow() - last_tick).total_seconds() / 60)
    if minutes <= 0:
        return

    active = conn.execute("SELECT node_id, progress FROM athenaeum_studies WHERE status = 'studying'").fetchone()
    if active and active["node_id"] in NODE_INDEX:
        info = NODE_INDEX[active["node_id"]]
        rate, _ = get_insight_rate(conn)
        new_progress = active["progress"] + (rate / 60.0) * minutes
        if new_progress >= info["insight"]:
            conn.execute(
                "UPDATE athenaeum_studies SET status = 'complete', progress = ?, completed_at = CURRENT_TIMESTAMP WHERE node_id = ?",
                (info["insight"], active["node_id"]))
        else:
            conn.execute("UPDATE athenaeum_studies SET progress = ? WHERE node_id = ?",
                         (new_progress, active["node_id"]))
    conn.execute("UPDATE base SET last_athenaeum_tick = CURRENT_TIMESTAMP WHERE id = 1")


def begin_study(node_id: str):
    """Begin (or resume) study on a node. Charges the Aether unseal fee only
    the first time; any other in-study node is paused, keeping its progress."""
    if node_id not in NODE_INDEX:
        raise ValueError("Unknown research.")
    info = NODE_INDEX[node_id]

    with db() as conn:
        _ensure_schema(conn)
        fac = conn.execute("SELECT id FROM facilities WHERE type = 'Athenaeum' AND base_id = 1").fetchone()
        if not fac:
            raise ValueError("The Athenaeum is not built.")

        # Settle accrual before switching so the old study keeps its due.
        process_athenaeum(conn)

        completed = _completed_ids(conn)
        if node_id in completed:
            raise ValueError("Already mastered.")

        if info["confluence"]:
            conf = next(c for c in CONFLUENCES if c["id"] == info["tree"])
            if not all(_discipline_mastered(p, completed) for p in conf["parents"]):
                raise ValueError("The confluence is still sealed — master both parent disciplines first.")
        if info["prereq"] and info["prereq"] not in completed:
            raise ValueError("The previous study in this discipline must be completed first.")

        existing = conn.execute("SELECT status FROM athenaeum_studies WHERE node_id = ?", (node_id,)).fetchone()
        if existing and existing["status"] == "studying":
            raise ValueError("Already in study.")

        if not existing and info["aether"] > 0:
            base = conn.execute("SELECT aether FROM base WHERE id = 1").fetchone()
            if (base["aether"] or 0) < info["aether"]:
                raise ValueError(f"Requires {info['aether']} Aether to unseal this study.")
            conn.execute("UPDATE base SET aether = aether - ? WHERE id = 1", (info["aether"],))

        conn.execute("UPDATE athenaeum_studies SET status = 'paused' WHERE status = 'studying'")
        if existing:
            conn.execute("UPDATE athenaeum_studies SET status = 'studying' WHERE node_id = ?", (node_id,))
        else:
            conn.execute("INSERT INTO athenaeum_studies (node_id, status, progress) VALUES (?, 'studying', 0)", (node_id,))
    return {"ok": True}


def _tree_payload(tree, completed, rows, unsealed=True, insight_costs=TIER_INSIGHT, aether_costs=TIER_AETHER):
    nodes = []
    for t, n in enumerate(tree["nodes"]):
        row = rows.get(n["id"])
        prereq_ok = unsealed and (t == 0 or tree["nodes"][t - 1]["id"] in completed)
        if n["id"] in completed:
            status = "complete"
        elif row and row["status"] == "studying":
            status = "studying"
        elif row and row["status"] == "paused":
            status = "paused"
        elif prereq_ok:
            status = "available"
        else:
            status = "locked"
        nodes.append({
            "id": n["id"], "name": n["name"], "desc": n["desc"], "tier": t + 1,
            "status": status,
            "progress": row["progress"] if row else 0,
            "insight_cost": insight_costs[t],
            "aether_cost": 0 if row else aether_costs[t],
            "pct": round(100 * (row["progress"] if row else 0) / insight_costs[t]) if status != "complete" else 100,
        })
    return nodes


def get_state():
    with db() as conn:
        _ensure_schema(conn)
        process_athenaeum(conn)
        fac = conn.execute("SELECT id, level FROM facilities WHERE type = 'Athenaeum' AND base_id = 1").fetchone()
        base = conn.execute("SELECT aether, gold FROM base WHERE id = 1").fetchone()
        if not fac:
            return {"built": False}

        rows = {r["node_id"]: dict(r) for r in conn.execute("SELECT * FROM athenaeum_studies").fetchall()}
        completed = {nid for nid, r in rows.items() if r["status"] == "complete"}
        rate, scholars = get_insight_rate(conn)

        disciplines = []
        for d in DISCIPLINES:
            nodes = _tree_payload(d, completed, rows)
            done = sum(1 for n in nodes if n["status"] == "complete")
            disciplines.append({
                "id": d["id"], "name": d["name"], "sigil": d["sigil"], "flavor": d["flavor"],
                "nodes": nodes, "tiers_done": done, "mastered": done == len(nodes),
            })

        confluences = []
        for c in CONFLUENCES:
            unsealed = all(_discipline_mastered(p, completed) for p in c["parents"])
            nodes = _tree_payload(c, completed, rows, unsealed=unsealed,
                                  insight_costs=CONF_INSIGHT, aether_costs=CONF_AETHER)
            done = sum(1 for n in nodes if n["status"] == "complete")
            confluences.append({
                "id": c["id"], "name": c["name"], "sigil": c["sigil"], "flavor": c["flavor"],
                "parents": c["parents"], "unsealed": unsealed,
                "nodes": nodes, "tiers_done": done, "mastered": done == len(nodes),
            })

        active = next((nid for nid, r in rows.items() if r["status"] == "studying"), None)
        return {
            "built": True, "level": fac["level"],
            "insight_rate": rate, "scholars": scholars,
            "aether": base["aether"] or 0,
            "active_node": active,
            "disciplines": disciplines,
            "confluences": confluences,
        }


def get_research_bonuses(conn=None):
    """Sums the effect dicts of every completed node. Safe to call before
    the facility exists — returns {}."""
    def _sum(c):
        try:
            completed = _completed_ids(c)
        except Exception:
            return {}
        total = {}
        for nid in completed:
            info = NODE_INDEX.get(nid)
            if not info:
                continue
            for k, v in info["node"]["effects"].items():
                total[k] = total.get(k, 0) + v
        return total

    if conn is not None:
        return _sum(conn)
    try:
        with db() as c:
            return _sum(c)
    except Exception:
        return {}
