"""
Generic Skill Engine
====================
A composable, data-driven resolver for active-skill effects, so the combat
engine can support wildly varied skills without a bespoke if/elif branch per
skill. An LLM (see scripts/generate_class_skills.py) emits skills in this
schema and they Just Work.

Active-skill schema (lives under skill["effect"]):

    "effect": {
        "mana_cost": 40,          # optional, else DEFAULT_SKILL_MANA_COST
        "cooldown": 4,            # optional, else 3
        "target": "lowest_hp_enemy",   # targeting mode (see resolve_targets)
        "target_count": 1,             # for the random_* / *_count modes
        "actions": [                   # ordered list applied to the targets
            {"kind": "damage", "power": 2.5, "stat": "auto",
             "ignore_def": 0.5, "crit_bonus": 0.3, "lifesteal": 0.3},
            {"kind": "execute", "threshold": 0.25},
            {"kind": "status", "status": "bleed", "duration": 3}
        ],
        "self_actions": [               # optional, applied to the caster
            {"kind": "buff", "stat": "agility", "pct": 0.5, "duration": 2}
        ]
    }

Presence of effect["actions"] (or "self_actions") routes a skill through this
engine; anything else falls back to the legacy dispatcher in combat_service.

Passive-skill triggers (lives under skill["effect"]["triggers"]) — a list of
{event, actions}. Events: on_hit_taken (counter), on_dodge, on_kill,
on_ally_death, on_low_hp. Resolved by combat_service at the matching moment.

All combat primitives (calc_damage, apply_status_effect, apply_heal) are
imported lazily inside functions to avoid a circular import with
combat_service.
"""
import random

# Which stats a buff/debuff/stat_mod may touch (numeric CombatUnit fields).
_BUFFABLE_STATS = {"strength", "intelligence", "agility", "endurance",
                   "willpower", "defense", "crit_chance", "dodge_chance", "armor_pen"}

# Statuses that lock a unit out of acting — kept in sync with
# combat_service.is_action_locked.
LOCK_STATUSES = {"stun", "freeze"}

# Every status the engine knows how to apply. Combat checks (blind miss,
# silence, evasion, invuln, shield absorb, stat_mod revert) live in
# combat_service; this set just validates what a skill is allowed to request.
KNOWN_STATUSES = {
    "bleed", "poison", "burn", "stun", "freeze", "taunting", "dmg_shield",
    "blind", "silence", "disarm", "evasion", "invuln", "shield", "stat_mod",
    "regen",
}


# ─── Targeting ──────────────────────────────────────────────────────────

def resolve_targets(caster, mode, allies, enemies, count=1):
    """Return the list of units a skill's actions apply to. allies/enemies are
    the caster's own living allies and living enemies respectively (already
    filtered to alive). Front/back ordering is preserved by the caller's
    lists so 'frontline'/'backline'/'column' work off list index."""
    alive_en = [u for u in enemies if u.alive]
    alive_al = [u for u in allies if u.alive]

    if mode in ("self",):
        return [caster]
    if mode == "one_enemy":
        return alive_en[:1]
    if mode == "all_enemies":
        return alive_en
    if mode == "random_enemies":
        return random.sample(alive_en, min(count, len(alive_en))) if alive_en else []
    if mode == "lowest_hp_enemy":
        return [min(alive_en, key=lambda u: u.health / max(1, u.max_health))] if alive_en else []
    if mode == "highest_hp_enemy":
        return [max(alive_en, key=lambda u: u.health)] if alive_en else []
    if mode == "strongest_enemy":
        return [max(alive_en, key=lambda u: max(u.strength, u.intelligence))] if alive_en else []
    if mode == "weakest_enemy":
        return [min(alive_en, key=lambda u: max(u.strength, u.intelligence))] if alive_en else []
    if mode == "frontline_enemies":
        front = alive_en[:2]
        return front or alive_en[:1]
    if mode == "backline_enemies":
        back = alive_en[2:]
        return back or alive_en
    if mode == "enemy_column":
        # A vertical slice: a front unit and the back unit "behind" it.
        if not alive_en:
            return []
        anchor = alive_en[0]
        idx = enemies.index(anchor)
        col = idx % 2
        return [u for i, u in enumerate(enemies) if u.alive and (i % 2) == col] or [anchor]

    if mode in ("all_allies", "team"):
        return alive_al
    if mode == "self_and_allies":
        return alive_al
    if mode == "lowest_hp_ally":
        return [min(alive_al, key=lambda u: u.health / max(1, u.max_health))] if alive_al else []
    if mode == "random_allies":
        return random.sample(alive_al, min(count, len(alive_al))) if alive_al else []
    if mode == "wounded_allies":
        return [u for u in alive_al if u.health < u.max_health] or alive_al
    if mode == "dead_ally":
        dead = [u for u in allies if not u.alive and not getattr(u, "is_npc", False)]
        return dead[:1]

    # Fallback: single front enemy.
    return alive_en[:1]


# ─── Status helpers the combat loop also consults ───────────────────────

def status_magnitude(unit, eff_type):
    total = 0.0
    for e in unit.status_effects:
        if e["type"] == eff_type and e["rounds"] > 0:
            total += e.get("magnitude", 0.0)
    return total


def has_status(unit, eff_type):
    return any(e["type"] == eff_type and e["rounds"] > 0 for e in unit.status_effects)


def absorb_with_shield(unit, dmg):
    """Flat absorb-shield pool eats damage before HP. Returns the damage that
    gets through after shields are consumed."""
    remaining = dmg
    for e in unit.status_effects:
        if remaining <= 0:
            break
        if e["type"] == "shield" and e["rounds"] > 0 and e.get("magnitude", 0) > 0:
            absorbed = min(e["magnitude"], remaining)
            e["magnitude"] -= absorbed
            remaining -= absorbed
    return remaining


def apply_timed_stat_mod(unit, stat, mult, rounds):
    """Multiplicative timed buff/debuff that reverts on expiry. Stores the
    exact delta applied so tick_status_effects can undo precisely."""
    if stat not in _BUFFABLE_STATS:
        return 0
    cur = getattr(unit, stat, 0)
    new = cur * mult
    delta = new - cur
    if stat in ("crit_chance", "dodge_chance", "armor_pen"):
        setattr(unit, stat, cur + delta)
    else:
        setattr(unit, stat, int(new))
        delta = int(new) - cur
    unit.status_effects.append({"type": "stat_mod", "stat": stat, "delta": delta,
                                "rounds": rounds, "magnitude": 0.0})
    return delta


# ─── Effect application ─────────────────────────────────────────────────

def _power_stat(caster, stat):
    if stat == "strength":
        return caster.strength
    if stat == "intelligence":
        return caster.intelligence
    # "auto" — use the caster's own attack stat
    return caster.intelligence if caster.power_stat == "intelligence" else caster.strength


def apply_actions(caster, actions, targets, ctx, on_self=False):
    """Apply a list of action dicts to the resolved targets. ctx carries the
    combat callbacks/state: {log, turns, round_num, all_units, morale_changes,
    kill_counts, damage_stats, fire_death}. Returns a short list of log lines
    already appended (also mutates ctx). Kept intentionally forgiving — an
    unknown action kind is skipped, never raised."""
    from services.combat_service import (
        calc_damage, apply_status_effect, apply_heal,
    )
    log = ctx["log"]

    for act in actions:
        kind = act.get("kind")

        if kind == "damage":
            _do_damage(caster, act, targets, ctx)

        elif kind == "execute":
            threshold = act.get("threshold", 0.2)
            for t in list(targets):
                if t.alive and t.health / max(1, t.max_health) <= threshold:
                    t.health = 0
                    ctx["fire_death"](caster, t, execution=True)

        elif kind == "heal":
            for t in targets:
                if not t.alive:
                    continue
                if "pct" in act:
                    amt = int(t.max_health * act["pct"])
                else:
                    amt = int(_power_stat(caster, act.get("stat", "auto")) * act.get("heal_power", 1.0))
                healed = apply_heal(t, amt)
                if healed:
                    log.append(f"  ✚ {caster.log_name} heals {t.log_name} for {healed} [{t.health}/{t.max_health}]")

        elif kind == "status":
            status = act.get("status")
            if status not in KNOWN_STATUSES:
                continue
            dur = act.get("duration", 2)
            mag = act.get("magnitude", 0.0)
            for t in targets:
                if not t.alive:
                    continue
                if status == "shield":
                    # magnitude = flat HP pool (as pct of caster max HP if <=1)
                    pool = int(caster.max_health * mag) if 0 < mag <= 1 else int(mag or caster.max_health * 0.15)
                    t.status_effects.append({"type": "shield", "rounds": dur, "magnitude": pool})
                    log.append(f"  🛡 {t.log_name} gains a {pool}-point shield ({dur}t).")
                else:
                    apply_status_effect(t, status, dur, magnitude=mag, source_id=caster.id)
                    _emoji = {"stun": "⚡", "freeze": "❄", "blind": "🌫", "silence": "🤐",
                              "bleed": "🩸", "poison": "☠", "burn": "🔥", "disarm": "⛓",
                              "evasion": "💨", "invuln": "✨", "taunting": "🎯", "regen": "✚"}.get(status, "✦")
                    log.append(f"  {_emoji} {caster.log_name}'s {ctx.get('skill_name','skill')} — {t.log_name} is {status} ({dur}t).")

        elif kind in ("buff", "debuff"):
            stat = act.get("stat", "strength")
            pct = act.get("pct", 0.2)
            mult = (1 + pct) if kind == "buff" else (1 - pct)
            dur = act.get("duration", 2)
            for t in targets:
                if not t.alive:
                    continue
                apply_timed_stat_mod(t, stat, mult, dur)
            verb = "surges" if kind == "buff" else "buckles"
            log.append(f"  📯 {caster.log_name}'s {ctx.get('skill_name','skill')} — {stat} {verb} {int(abs(pct)*100)}% ({dur}t).")

        elif kind == "cleanse":
            n = act.get("count", 99)
            debuffs = {"bleed", "poison", "burn", "stun", "freeze", "blind", "silence", "disarm"}
            for t in targets:
                removed = [e for e in t.status_effects if e["type"] in debuffs][:n]
                for e in removed:
                    t.status_effects.remove(e)
                if removed:
                    log.append(f"  ✨ {t.log_name} is cleansed of {len(removed)} affliction(s).")

        elif kind == "dispel":
            n = act.get("count", 1)
            buffs = {"stat_mod", "dmg_shield", "shield", "evasion", "invuln", "regen"}
            for t in targets:
                removed = [e for e in t.status_effects if e["type"] in buffs][:n]
                for e in removed:
                    if e["type"] == "stat_mod":
                        setattr(t, e["stat"], getattr(t, e["stat"]) - e.get("delta", 0))
                    t.status_effects.remove(e)
                if removed:
                    log.append(f"  ✂ {t.log_name} is stripped of {len(removed)} boon(s).")

        elif kind == "restore_mana":
            for t in targets:
                t.mana = min(t.max_mana, t.mana + int(act.get("amount", 20)))
        elif kind == "drain_mana":
            for t in targets:
                t.mana = max(0, t.mana - int(act.get("amount", 20)))

        elif kind == "revive":
            for t in targets:
                if not t.alive:
                    t.alive = True
                    t.health = int(t.max_health * act.get("pct", 0.3))
                    log.append(f"  ✟ {caster.log_name} revives {t.log_name}! [{t.health}/{t.max_health}]")


def _do_damage(caster, act, targets, ctx):
    from services.combat_service import calc_damage, apply_heal
    log = ctx["log"]
    power = act.get("power", 1.0)
    stat = act.get("stat", "auto")
    total_lifestolen = 0

    # Optional chaining: after hitting the primary target(s), bounce to N
    # additional random enemies at falling power.
    chain = act.get("chain", 0)
    chain_falloff = act.get("chain_falloff", 0.7)

    hit_list = list(targets)
    if chain and targets:
        pool = [u for u in ctx["all_units"]
                if u.alive and (u.is_hero != caster.is_hero) and u not in hit_list]
        random.shuffle(pool)
        hit_list = hit_list + pool[:chain]

    cur_power = power
    for i, t in enumerate(hit_list):
        if not t.alive:
            continue
        if has_status(t, "invuln"):
            log.append(f"  ✨ {t.log_name} is invulnerable — no damage.")
            continue
        base, is_crit = calc_damage(caster, t, force_strength=(stat == "strength"))
        # Recompute from the chosen stat when not "auto".
        if stat in ("strength", "intelligence"):
            raw = _power_stat(caster, stat)
            base = max(1, int(base * (raw / max(1, caster.strength if stat == "strength" else max(1, caster.intelligence)))))
        dmg = int(base * cur_power)
        if act.get("true_damage"):
            dmg = int(_power_stat(caster, stat) * cur_power)  # ignores all mitigation
        elif act.get("ignore_def"):
            # Re-add a fraction of the mitigated amount to simulate armor pen.
            raw = int(_power_stat(caster, stat) * cur_power)
            dmg = int(dmg + (raw - dmg) * min(1.0, act["ignore_def"]))
        if act.get("guaranteed_crit") or (act.get("crit_bonus") and random.random() < caster.crit_chance + act["crit_bonus"]):
            dmg = int(dmg * 1.5)
            is_crit = True
        # Execute rider baked into a damage action.
        if "execute_threshold" in act and t.health / max(1, t.max_health) <= act["execute_threshold"]:
            dmg = int(dmg * (1 + act.get("execute_bonus", 0.5)))

        dmg = _absorb(t, dmg)
        t.health -= dmg
        ctx["damage_stats"][caster.id] = ctx["damage_stats"].get(caster.id, 0) + dmg
        if act.get("lifesteal"):
            total_lifestolen += int(dmg * act["lifesteal"])
        crit_text = " CRIT!" if is_crit else ""
        chain_tag = "  ↳" if i >= len(targets) else "  ✦"
        log_msg = f"{chain_tag} {caster.log_name}'s {ctx.get('skill_name','skill')} hits {t.log_name} for {dmg}{crit_text} [{max(0,t.health)}/{t.max_health}]"
        log.append(log_msg)
        ctx["turns"].append({"round": ctx["round_num"], "attacker_id": caster.id, "target_id": t.id,
                             "damage": dmg, "is_crit": is_crit, "target_hp": max(0, t.health),
                             "log": log_msg, "attacker_mana": caster.mana, "target_mana": t.mana,
                             "skill_name": ctx.get("skill_name")})
        if t.health <= 0 and t.alive:
            ctx["fire_death"](caster, t)
        cur_power *= chain_falloff

    if total_lifestolen > 0:
        healed = apply_heal(caster, total_lifestolen)
        if healed:
            log.append(f"    🩸 {caster.log_name} drains {healed} Health.")


def _absorb(unit, dmg):
    return absorb_with_shield(unit, dmg)


# ─── Top-level entry: execute one generic active skill ──────────────────

def is_generic_skill(skill):
    eff = skill.get("effect", {})
    return isinstance(eff.get("actions"), list) or isinstance(eff.get("self_actions"), list)


def execute_generic_skill(caster, skill, allies, enemies, ctx):
    """Resolve one generic active skill. Mana/cooldown are handled by the
    caller (combat_service). Returns True (always fires)."""
    eff = skill.get("effect", {})
    ctx = dict(ctx)
    ctx["skill_name"] = skill.get("name", "skill")

    mode = eff.get("target", "one_enemy")
    count = eff.get("target_count", 1)
    targets = resolve_targets(caster, mode, allies, enemies, count)

    ctx["log"].append(f"  ★ {caster.log_name} uses {skill['name']}!")

    if eff.get("actions"):
        if targets:
            apply_actions(caster, eff["actions"], targets, ctx)
        else:
            ctx["log"].append(f"    …but there's no valid target.")
    if eff.get("self_actions"):
        apply_actions(caster, eff["self_actions"], [caster], ctx, on_self=True)
    return True
