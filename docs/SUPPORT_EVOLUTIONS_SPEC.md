# Support-Class Evolution Mechanics — Design Spec

> **STATUS (2026-07-12): IMPLEMENTED.** All branches + Lv.60 capstones are live
> in `support_service.py` / `combat_service.py` (economy hooks in time/crafting/
> market/sanctum/athenaeum/endgame services). Deviations from this spec:
> Scout was reworked (NO floor reveal — Trail-sense/Master of the Hunt/Predator's
> Mark/Sabotage); the Farmer Beast Tamer COMBAT PET was dropped (Menagerie
> defense mult only); 2-capstone branches (Merchant/Farmer) are merged kickers.

**Framework:** Mastery scales the *magnitude*; the evolution *branch* selects the *mechanic*.
- **Unevolved** support → a weak *generic* version of the facility boon.
- **Lv.30 branch** → that branch's *signature mechanic* (mastery-scaled, 0–9).
- **Lv.60 capstone** → the branch mechanic at full power + one twist.

Mastery = star + evolution stage (Lv.30 +1, Lv.60 +2), capped 9. See `support_service.py`.

Each class picks ONE branch via its assigned hero's evolved class name. Best-mastery
assignee for a facility sets both the mastery and the active branch.

---

## Base (unevolved) generics
An unevolved support gives a WEAK baseline version of its facility's role — a hint
of what it does before you commit to a branch. Deliberately small and does NOT ride
the branch ladder (see "generic ladder" note at the bottom).

| Class | Unevolved generic |
|---|---|
| Chef | small feast — tiny +% to all stats |
| Medic | small +% max HP + slight passive trauma healing |
| **Scout** | **Trail-sense — small % chance to negate an ambush (no reveal)** |
| Blacksmith | small crafting gold discount |
| Quartermaster | small opening damage barrier |
| Tactician | small opening mana (no guaranteed first strike — that's the Strategist branch) |
| Priest | slow passive roster loyalty gain (the base Shrine role) |
| Alchemist | small passive brew-rate bonus |
| Merchant | small passive gold |
| Farmer | small passive ingredients |

---

## Chef → Dining Hall  *(Batch 1 — approved)*
| Branch | Signature | Lv.60 capstone twist |
|---|---|---|
| Sous Chef → **Master Chef** | **Grand Feast** — biggest flat +% to all six stats for the deployed team | + round 1–3 regen (well-fed) |
| Forager → **Gourmet** | **Full Larder** — +% Farm ingredients & cooked consumables heal/buff more | consumables also clear stress/trauma |
| Butcher → **Iron Chef** | **War Rations** — feast skews to offense: big Strength + crit, little defense | team opens each fight with +morale (fearless) |

## Medic → Infirmary  *(Batch 1 — approved)*
| Branch | Signature | Lv.60 capstone twist |
|---|---|---|
| Surgeon → **CMO** | **Field Surgery** — biggest +% max HP + faster trauma recovery | once/fight, emergency stitch fully patches the most-hurt hero |
| Herbalist → **Miracle Worker** | **Regen Salves** — team regenerates % HP every combat round | regen also burns down bleed/poison/burn faster |
| Field Medic → **Plague Doctor** | **Toxin Kit** — deployed heroes gain poison-on-hit | enemies start fights weakened/afflicted |

## Scout → Bestiary
**NO floor reveal anywhere — floors stay fully unknown (user rule 2026-07-10).**
Base Scout (unevolved) generic: **Trail-sense** — small % chance to negate an ambush.
| Branch | Signature | Lv.60 capstone twist |
|---|---|---|
| Pathfinder → **Ranger** | **Master of the Hunt** — +% beast CAPTURE rate in the Tower + tamed Bestiary beasts add more base defense | track & capture RARE/elite beasts |
| Tracker → **Infiltrator** | **Predator's Mark** — first enemy the team hits each fight is marked for +% damage (mid-fight, no foreknowledge) | marked enemies can't dodge + armor-pen |
| Spy → **Spymaster** | **Sabotage** — enemies you face start weakened (stats/HP down) | enemies start poisoned/afflicted, or you skim gold off them |

## Blacksmith → Forge
| Branch | Signature | Lv.60 capstone twist |
|---|---|---|
| Weaponsmith → **Master Smith** | **Master Forge** — biggest craft gold discount + crafted weapons roll higher | chance to craft at +1 rarity |
| Armorer → **Forge Lord** | **Tempered Plate** — crafted armor rolls higher + base/Wall defense bonus | deployed team gains a small flat damage-reduction |
| Artificer → **Runesmith** | **Runework** — cheaper relic/rune costs + boosts Mage/Athenaeum research | chance for crafted gear to roll a bonus affix |

## Quartermaster → Vault
| Branch | Signature | Lv.60 capstone twist |
|---|---|---|
| Merchant → **Tycoon** | **War Chest** — Vault generates passive gold + expands equipment storage | a cut of gold from tower kills |
| Logistics Officer → **Guildmaster** | **Field Kits** — the emergency mid-fight heal pool (biggest here) | kits also restore mana / cleanse |
| Scavenger → **Hoarder** | **Deep Stores** — opening damage barrier + more consumables carried into the tower | +% loot/materials from floors |

## Tactician → Training Grounds
| Branch | Signature | Lv.60 capstone twist |
|---|---|---|
| Strategist → **Grand Strategist** | **Opening Gambit** — guaranteed first strike + big opening mana | extra team action / haste round 1 |
| Commander → **General** | **Battle Formation** — team gets +% all combat stats while ≥N heroes alive | buff scales UP as allies fall (last-stand) |
| Advisor → **Warlord** | **War Council** — team starts with rage/crit + bonus damage rounds 1–2 | kills grant a stacking attack buff (snowball) |

## Priest → Shrine
| Branch | Signature | Lv.60 capstone twist |
|---|---|---|
| Confessor → **High Confessor** | **Absolution** — fastest roster loyalty + reduces stress/trauma | captured-hero conversion boost |
| Oracle → **Prophet** | **Guardian Fate** — death-save charges (HARD-CAP 2, user rule) | once/fight, foresee a fatal blow → a hero dodges it entirely |
| Chaplain → **Saint** | **Blessing** — team gains +% resistance + bonus damage vs undead/dark | fight-start heal/shield blessing (holy aegis) |

## Alchemist → Alchemist Lab
| Branch | Signature | Lv.60 capstone twist |
|---|---|---|
| Apothecary → **Grand Alchemist** | **Master Brewer** — biggest passive brew rate + potions roll stronger | chance to brew a bonus / higher-tier potion |
| Transmuter → **Philosopher** | **Transmutation** — converts ingredients↔materials + passive aether/gold | daily "gold from lead" lump / material-dupe chance |
| Poisoner → **Brewmaster** | **Combat Draughts** — deployed heroes auto-carry a battle elixir into fights | enemies start poisoned / team gets a damage draught |

## Merchant → Market  *(2 branches, 2 capstones each)*
| Branch | Signature | Lv.60 capstones |
|---|---|---|
| **Trader** | **Bull Market** — biggest passive gold + better Market stock/discounts | Guild Master: flat passive-gold boost · Trade Prince: shop stocks rare materials |
| **Smuggler** | **Black Market** — rotating black-market shop (gems/rare mats for gold) + contraband gold | Black Market Baron: cheaper currency exchange · Shadow Broker: intel/relic deals |

## Farmer → Farm  *(2 branches, 2 capstones each)*
| Branch | Signature | Lv.60 capstones |
|---|---|---|
| **Master Farmer** | **Bountiful Harvest** — biggest passive ingredients + rare reagent chance | Harvest Lord: flat ingredient surplus · Nature's Chosen: passive healing herbs (roster trauma recovery) |
| **Beast Tamer** | **Menagerie** — tamed Bestiary beasts add more base defense + deploy a beast as a combat pet | Apex Predator: stronger pet · Wild Master: multiple beasts / beast team-buff |

---

### Implementation notes
- `get_support_tiers` must return **branch** alongside mastery. Add a `BRANCH_MAP`
  (class name → branch key) built from `CLASS_EVOLUTIONS` (each L30 name is a branch
  root; its L60 children inherit it).
- `get_support_effects` resolves the mechanic from (base, branch, mastery).
- Roll out in tested WAVES. Some mechanics reuse existing primitives (feast/stat %,
  dmg_shield, regen status, poison_on_hit, death_save, income mult, floor reveal);
  others need new hooks (combat pet, black-market shop, weakpoint damage, sabotage).
- Combat classes get their own unique-mechanic pass LATER (audit `skills_service`
  first to avoid duplicating existing unique skills).
