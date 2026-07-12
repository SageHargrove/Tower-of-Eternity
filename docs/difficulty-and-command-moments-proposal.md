# Proposals — Difficulty Rebalance + Command Moments (2026-07-11)

> **STATUS (2026-07-12):** Proposal 1 (Tower Awakens) SHIPPED with knobs A+C+D+E (compound curve past 40, elite density/double-affix, severe conditions past 60, boss walls 50/70/90). Proposal 2 (Command Moments) REJECTED as designed — violates the no-floor-escape law; needs a fresh concept keeping heroes' agency.

---

## 1. Difficulty rebalance — "The Tower Awakens"

**Goal:** floor 100 should be a near-mythical achievement (manhwa reference:
~floor 80 after years). The support revamp just handed players up to ~+35%
stats, +30% HP, barriers, death-saves, regen — the curve must answer.

**Current enemy scaling is LINEAR** (`scale = 1 + floor × 0.12`) while player
power compounds (levels × stars × gear × boons × research × trophies). Linear
vs compound means the game gets EASIER late. That's the actual bug.

### Proposed knobs (stack, all tunable)
| Knob | Numbers | Effect |
|---|---|---|
| **A. Awakening curve** | past floor 40: `scale ×= 1.01^(floor−40)` (compound) | floor 50 ≈ +10%, floor 70 ≈ +35%, floor 90 ≈ +64%, floor 100 ≈ +82% — the Tower starts *answering* deep climbers |
| **B. Attrition deepens** | fatigue/stress per floor +2%/floor past 50 | deep runs become marathons needing support infrastructure (plays INTO the support revamp) |
| **C. Elite density** | elite chance 15%→25% base past floor 50; TWO affixes possible past 80 | deep floors feel qualitatively meaner, not just fatter |
| **D. Condition severity** | past floor 60, conditions roll a "severe" variant (double magnitude, incl. hostile-only ones) | team-building pressure per floor |
| **E. Boss walls** | floors 50/70/90 bosses get a third phase at 15% HP + the Unimber pad doubled | named "walls" the community remembers, like the manhwa's floor-80 legend |

**Recommendation:** implement A + C + E first (pure combat, no economy touch),
watch real climb data, then decide on B/D. Deliberately NOT touching early
floors (1–40) — new-player experience stays as-is.

---

## 2. Command Moments — the Manager's hand

**Fantasy (from Pick Me Up):** the manager doesn't fight — but occasionally
the fight reaches a moment where their judgment is the difference. The heroes
have the agency; the manager has *one call*.

### Design sketch
- **Trigger, not button:** at most ONE moment per fight, and only when a
  dramatic condition fires — boss enters phase 3, a hero drops below 15% with
  no death-save left, swarm reaches round 5 with 2+ heroes panicking. Most
  fights have none.
- **The fight PAUSES** (auto-resolve halts) with an Illuminated interstitial:
  the situation in one sentence + **two calls**, e.g.:
  - Boss phase 3: **"CALL THE RETREAT"** (end fight, keep everyone alive, no
    loot, floor unclimbed) vs **"FINISH IT"** (+20% team damage, −10% team DR
    for the rest of the fight).
  - Hero at death's door: **"PULL THEM OUT"** (hero exits the fight alive —
    team fights on a body short) vs **"TRUST THEM"** (hero gains +crit and
    fear-immunity at death's door — but no safety net).
  - Swarm panic: **"STEADY THEM"** (clear all panic, −morale later) vs
    **"LET THE FEAR BITE"** (panicked heroes hit harder this fight, +stress after).
- **No resource, no cooldown farming** — the rarity IS the cost. Choices are
  tradeoffs, never strict upgrades, so there's no "correct" macro.
- **Auto-resolve setting:** players who never want to be interrupted can set
  a standing doctrine per trigger ("always trust them") in options.

**Scope:** ~1 backend pause/resume hook in the combat runner + 3 trigger
definitions + 1 modal. The pause is the only structural work — combat is
currently one synchronous resolve, so a Command Moment means splitting the
fight into "resolve until interrupt → await player call → resolve rest."
