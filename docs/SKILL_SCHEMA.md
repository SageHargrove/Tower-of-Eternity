# Skill Schema — the Combat Engine's toolbox

The combat engine (`backend/services/combat_service.py` +
`backend/services/skill_engine.py`) resolves skills from a **composable,
data-driven schema**. You can author a skill entirely as data — no engine
code changes — and it Just Works. This is the vocabulary.

A skill is `{id, name, type, desc, effect}`. `type` is `"active"` or
`"passive"`. Everything mechanical lives in `effect`.

---

## Active skills (the composable engine)

```jsonc
"effect": {
  "mana_cost": 30,          // 15-60; the engine deducts this to cast
  "cooldown": 3,            // rounds before it can fire again
  "target": "lowest_hp_enemy",
  "target_count": 2,        // only used by random_enemies / random_allies
  "actions": [ ... ],       // applied to the resolved target(s)
  "self_actions": [ ... ]   // optional; applied to the caster
}
```

The presence of `actions` (or `self_actions`) routes the skill through the
generic engine. Without them, the skill falls back to the **legacy
dispatcher** (the old flat keys like `dmg_pct`, `taunt_duration`,
`team_buff_pct` — still supported, so existing skills keep working).

### Target modes

| Category | Modes |
|---|---|
| Enemies | `one_enemy`, `all_enemies`, `random_enemies`, `lowest_hp_enemy`, `highest_hp_enemy`, `strongest_enemy`, `weakest_enemy`, `frontline_enemies`, `backline_enemies`, `enemy_column` |
| Allies | `self`, `all_allies`, `lowest_hp_ally`, `random_allies`, `wounded_allies`, `dead_ally` |

`enemy_column` hits a front unit and the back unit "behind" it (positional
splash). Front line = list indices 0–1, back line = 2+.

### Action kinds

```jsonc
// Damage — the workhorse. power is a multiplier on the caster's attack.
{"kind":"damage","power":2.5,"stat":"auto",   // stat: auto|strength|intelligence
 "ignore_def":0.5,        // 0-1 fraction of the target's defense ignored
 "true_damage":true,      // ignores ALL mitigation (armor, shields via calc)
 "crit_bonus":0.3,        // extra crit chance for this hit
 "guaranteed_crit":true,
 "execute_threshold":0.3,"execute_bonus":0.5,  // +50% dmg vs target below 30% HP
 "lifesteal":0.3,         // heal caster for 30% of damage dealt
 "chain":2,"chain_falloff":0.6}   // bounce to 2 more foes at 60% falling power

{"kind":"execute","threshold":0.25}   // instantly kill a target below 25% HP
{"kind":"heal","pct":0.3}                        // heal 30% of target max HP
{"kind":"heal","heal_power":1.5,"stat":"intelligence"}  // heal by caster power
{"kind":"status","status":"bleed","duration":3,"magnitude":0.4}
{"kind":"buff","stat":"strength","pct":0.5,"duration":2}   // timed, auto-reverts
{"kind":"debuff","stat":"agility","pct":0.4,"duration":2}
{"kind":"shield","status":"shield","duration":2,"magnitude":0.2}  // absorb 20% max HP
{"kind":"cleanse","count":2}   // remove up to 2 debuffs (use on allies)
{"kind":"dispel","count":1}    // strip up to 1 buff (use on enemies)
{"kind":"restore_mana","amount":30}
{"kind":"drain_mana","amount":25}
{"kind":"revive","pct":0.4}    // target mode must be dead_ally
```

### Status types (for `{"kind":"status"}`)

| Status | Effect | `magnitude` meaning |
|---|---|---|
| `stun`, `freeze` | Skip their turn | — |
| `blind` | 60% chance to miss basic attacks | — |
| `silence` | Cannot cast active skills | — |
| `disarm` | (reserved) | — |
| `taunting` | Forces enemies to target them | — |
| `bleed` | DoT, 4%/round of max HP | — |
| `burn` | DoT, 5%/round + halves healing | — |
| `poison` | DoT, flat per tick | dmg per tick |
| `evasion` | Added dodge chance while active | dodge chance (0.5 = +50%) |
| `invuln` | Immune to all damage | — |
| `regen` | Heals per turn | % max HP per turn |
| `dmg_shield` | Flat % damage reduction | reduction fraction |
| `shield` | Flat absorb pool | % of caster max HP (≤1) or flat |

---

## Passive skills

Flat modifiers (any combination):
`str_pct`, `int_pct`, `agi_pct`, `hlt_pct`, `all_pct`, `crit_pct`,
`dodge_pct`, `armor_pen`, `regen_pct`, `dmg_reduction_pct`,
`physical_resist_pct`, `magic_resist_pct`, `fear_immune`, `death_save`.

### Conditional triggers (reactive passives)

```jsonc
"effect": {"triggers": [
  {"event":"on_hit_taken","chance":0.4,"name":"Riposte",
   "target":"<target mode, or omit to hit whoever caused the event>",
   "actions":[ {"kind":"damage","power":1.0,"stat":"strength"} ]}
]}
```

Events: `on_hit_taken` (counter-attack), `on_dodge`, `on_kill`,
`on_ally_death`, `on_low_hp`. A trigger's `actions` use the exact same
action vocabulary as active skills, so a trigger can heal, buff, apply
status — anything.

A passive can carry both flat modifiers **and** triggers in the same
`effect`.

---

## Authoring tips

- Combine actions for combos: `damage` + `debuff`, or `damage` + `status`.
- Balance: single-target `power` 1.5–3.0; `all_enemies` 0.8–1.5; execute
  thresholds 0.2–0.35. Stronger effects → higher `mana_cost` / `cooldown`.
- Lean into class fantasy — an Assassin executes and bleeds; a Cleric
  shields/cleanses/revives; a Warden taunts and regens; a Sniper hits
  `backline_enemies` with `ignore_def`.
- `backend/scripts/generate_class_skills.py` has this whole vocabulary in
  its LLM prompt — regenerate class kits with your own `GEMINI_API_KEY`
  (or hand-author into `skills_service.py`'s `SKILL_POOL`).
```
