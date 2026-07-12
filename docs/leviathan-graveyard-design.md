# Leviathan's Graveyard — sea-themed area design

> **STATUS (2026-07-12): SHIPPED** (2026-07-10, zone rework) — sea band live with shell_armor mechanic; tower is 10 band-pure zones. Historical design record.

A pitch-black ocean floor littered with the massive glowing-white bones of ancient
sea gods and the wreckage of doomed ships. Plays perfectly to the art style
(glowing bio-luminescence on a void-black background is already our aesthetic).

## Placement — recommended: replace the **mythic** tier (floors 61–70)

`ENEMY_TYPES` in `combat_service.py` groups floors into 10 tiers
(beginner→ancient). Re-theming one tier's roster = re-theming that "area."

**Recommend the `mythic` band (61–70)** because:
- It already contains **Naga** + **Abyssal Lurker** (aquatic) — half sea already.
- Power scale fits: "reanimated colossal sea god" reads as a floors-61–70 threat.
- Its current lineup (Chimera / Naga / Abyssal Lurker / Frost Wight / Shrouded
  Reaper) is the least thematically cohesive band — cleanest to re-theme.

**Displaced enemies (relocate, don't delete their art):**
- **Chimera** → `mighty` (41–50) alongside Manticore/Wyvern (fits the beast band).
- **Frost Wight** → keep as a `mythic`/`ascendant` bonus extra, or move to `apex`.
- **Naga / Abyssal Lurker** → stay (they're already sea-appropriate, fold into the new roster).
- **Shrouded Reaper** → keep as a cross-tier extra.

Alt placement if we want the sea lower/earlier: `advanced` (31–40, the crypt/undead
band). But mythic is the better fit.

## Roster → engine mapping

Tuple format: `(name, atk_mult, def_mult, spd_mult, archetype, tier)`.
HP scales off def_mult, evasion off spd_mult.

### Regulars (ENEMY_TYPES)
| Enemy | Concept | atk | def | spd | archetype |
|---|---|---|---|---|---|
| Drowned Deckhand | balanced cannon fodder | 1.0 | 1.0 | 1.0 | normal |
| Bone-Crab Scavenger | heavily armored, slow | 0.9 | 1.7 | 0.5 | normal |
| Coral-Grown Husk | huge HP damage-soak | 0.8 | 1.8 | 0.5 | normal |
| Abyssal Lamprey | glass cannon | 1.4 | 0.6 | 1.7 | pack |
| Marrow-Worm | evasive, annoying | 0.9 | 0.8 | 1.6 | swarm |
| Sunken Wisp | squishy caster | 1.1 | 0.6 | 1.5 | pack |

### Elites (ENEMY_TYPES + ENEMY_ABILITY_OVERRIDES)
| Enemy | Role | atk | def | spd | ability |
|---|---|---|---|---|---|
| Galleon Captain | buffer/tank | 1.1 | 1.4 | 0.8 | `team_buff_aura` |
| Trench Stalker | burst assassin | 1.6 | 0.8 | 1.9 | `cleave` |
| Bone-Grafted Goliath | bruiser | 1.7 | 1.4 | 0.7 | `crushing_blow` |

### Miniboss (floor 65) & Boss (floor 70) — enemy_families.py
- **Captain Iron-Lung** (miniboss, floor 65): `["cleave", "team_buff_aura", "last_stand"]`, high ATK/SPD.
- **The Calcified Horror** (alt miniboss / floor 65 variant): `["crushing_blow", "self_regen"]` (+ proposed `shell_armor`), massive DEF/HP, very low SPD.
- **Thalassor, the Undead Leviathan** (boss, floor 70): `["cleave", "summon_add", "enrage", "crushing_blow"]`, high ATK/HP/DEF. `ENEMY_SPAWN_TEMPLATE["Thalassor"] = "Marrow-Worm"`.

## Optional NEW mechanic (fits the theme)
**`shell_armor`** — takes greatly reduced physical damage until the shell cracks
(after N hits or a cumulative-damage threshold), then reverts to normal. Sea-
perfect for Bone-Crab Scavenger + The Calcified Horror ("takes almost no physical
damage until its shell is cracked"). Small addition to the damage step in
`combat_service.py`; reusable by any future armored enemy.

(Stretch) **Rising-tide zone modifier** — a per-round env effect on 61–70 that
slows non-aquatic units. Bigger lift; defer.

## Art references (dropped in controlnet_refs/monsters/)
- `leviathan.jpg` → **Thalassor** — PERFECT (serpentine sea-dragon, tentacles, teal bio-luminescence). Use as-is.
- Sea creatures (vet at gen time): `giant_Crab`/`hermit_crab` → Bone-Crab Scavenger + Calcified Horror; `shark` → Trench Stalker; `abyssal_eel` → Abyssal Lamprey; `giant_leech` → Marrow-Worm; `sea_monster`/`giant_serpent` → extras.
- Humanoid enemies (NO ControlNet — plain LoRA gen): Drowned Deckhand, Galleon Captain, Captain Iron-Lung, Bone-Grafted Goliath, Coral-Grown Husk, Sunken Wisp.

## Implementation checklist (all data/logic — no art needed to wire)
1. `combat_service.py` ENEMY_TYPES: swap the `mythic` rows for the 6 sea regulars + 3 elites (tier stays `"mythic"`).
2. ENEMY_ABILITY_OVERRIDES: Galleon Captain / Trench Stalker / Bone-Grafted Goliath.
3. ENEMY_SPAWN_TEMPLATE: `"Thalassor": "Marrow-Worm"`.
4. ENEMY_WAVE: assign the new names to wave 7 (the mythic art-review folder).
5. `enemy_families.py`: Captain Iron-Lung (floor 65 miniboss), Thalassor (floor 70 boss); relocate the old mythic family entries.
6. `portrait_cache.py` ENEMY_PORTRAIT_HINTS: add void-bg tag prompts for each.
7. Relocate Chimera → mighty; keep Naga/Abyssal Lurker; handle Frost Wight/Reaper.
8. (Optional) `shell_armor` mechanic + `generate_zone_theme` bias toward sea flavor on 61–70.
