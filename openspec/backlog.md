# Backlog

Deferred items — confirmed real, not started, no timeline. Pulled from the
2026-06-26 to 2026-06-29 Discord feedback review. Pick items off this list
when ready; nothing here is scheduled.

## Art / Content
- **Enemy art audit**: go through every enemy's generated portrait, find
  which prompts produce broken/off-model art, fix the prompt or replace
  the enemy concept. Slime -> Shadow Wisp and Giant Rat -> Dungeon Imp
  (enemy-art-overhaul) were the only two addressed so far.
- **Dragon-tier higher-ranked enemies**: a normal "Young Dragon"/"Dracolich"
  exist; want elite/boss-ranked dragon variants.
- ~~Evil 7-star humanoid elite/boss~~ — DONE 2026-07-02: "Vaelor, the
  Fallen Ascendant" is the floor-35 miniboss (enemy_families.py). Still
  needs its art: static/portraits/enemies/miniboss/boss_fallen_ascendant.png.
- ~~Monster art pipeline / LoRA investigation~~ — ADDRESSED 2026-07-06:
  MONSTER_STYLE now leads with e621 anchor tags (`no humans, monster,
  feral`) — A/B verified this flips humanoid drift to actual creature
  shapes on NoobAI (it's danbooru+e621 trained). Regenerate enemy art to
  benefit; no LoRA needed for this specific failure.

## Floor Variety
- Floor types beyond combat are thin — survival/defend/escort/explore
  exist, but wanted: "war," "find and retrieve," and other distinct floor
  archetypes, not just combat dressed up differently.
- Lore readout before floor 10, or an unlockable lore page that grows as
  you climb.

## Skills Content
- **Bespoke skill kits per class**: only 6 classes (Warrior, Spearman,
  Thief, Archer, Mage, Magic Engineer) have a dedicated `SKILL_POOL` entry
  in `services/skills_service.py` — the other ~130 classes (Knight,
  Paladin, Necromancer, Acolyte, Cleric, etc.) all fall back to the shared
  `GENERIC_SKILLS` pool. Stopgapped for now (GENERIC_SKILLS bumped to 3
  actives + more passives, every 3★+ hero guaranteed at least one active),
  but the real ask is hundreds-to-thousands of unique skills long-term,
  weighted more passive than active, with passives leaning class-agnostic
  and actives leaning class-specific.

## Systems / Text Quality
- **LLM model for narrative text**: currently Gemini-based
  (services/llm_service.py). Investigate Haiku (or another model) for
  better text quality if Gemini Pro doesn't work out — user is
  independently testing this.
- **Secure coding / anti-cheat audit**: no review has been done on
  preventing save-file tampering, request forgery, or other client-side
  cheating vectors.

## Notes
- Each item above was independently confirmed missing (not just
  forgotten) via a code search before being added here — not guesses.

## From the 2026-07-02 Base Progression & Economy Overhaul
- ~~Raid system backend~~ — DONE (arena server raids + local scout/apply
  endpoints; Scout Report modal wired 2026-07-06 with full map→scout→raid
  flow). Still open: ships burning AETHER per raid (resource exists,
  consumption doesn't).
- ~~Tournaments backend~~ — DONE (weekly Swiss/royale brackets on the arena
  server; Tournament Registration modal wired 2026-07-06).
- ~~Banner sync to arena_server~~ — DONE 2026-07-06: POST /arena/banner
  (banner_json on arena_players), returned in /arena/leaderboard and
  /arena/raid/map; client pushes on arena login and renders opponents'
  pennants on the boards and raid target list.
- ~~Infirmary/Forge "base upgrade" tree has NO UI~~ — STALE: BasePage
  renders both via UpgradeTreePanel (BasePage.jsx ~line 656).
- **Bestiary raids tie-in**: captured beasts should be sendable alongside
  battleships on raids as cannon fodder (currently defense-only).
- **Events system** for summon tickets (tickets currently achievement-only).
- **Crafting flexibility review**: kept strict recipes for now (Forge slot
  recipes + discoverable blueprint recipes + LLM creative crafting already
  covers the "creative" niche); revisit if playtesters find it rigid.

## Universes (True Randomness)
- Instead of manual difficulty selection, each player's save file represents a random "Universe" with a hidden difficulty modifier. Higher difficulty universes could spawn stronger boss variants, but yield vastly higher rewards. Tied to the Manhwa concept.
