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
- ~~"Find and retrieve"~~ — DONE (Retrieval floors: designated Runner
  channels the objective; their death fails the floor). Still open: "war"
  and other archetypes beyond the current survival/defend/escort/explore/
  retrieval/ambush/blitz/cursed set.
- ~~Lore readout / unlockable lore page~~ — DONE twice over: the Lore
  Journal (floor-unlocked pages) AND the discovery Codex (2026-07-11,
  see-it-to-learn-it entries with a "N of M pages recovered" counter).

## Skills Content
- ~~Bespoke skill kits per class~~ — DONE (audited 2026-07-11): every one
  of the 148 classes now has a full 30-skill kit (8-12 actives each);
  2nd-tier pinnacle evolutions inherit their lineage's kit by design.
  Long-term "thousands of skills" ambition remains open-ended.

## Systems / Text Quality
- **LLM model for narrative text**: currently Gemini-based
  (services/llm_service.py). Investigate Haiku (or another model) for
  better text quality if Gemini Pro doesn't work out — user is
  independently testing this.
- **Secure coding / anti-cheat audit** — PARTIALLY reviewed 2026-07-11:
  arena server has real bearer-token auth + hashed passwords; single-player
  save is client-authoritative by design (acceptable offline). CRITICAL
  before ANY publish: rotate the ANTHROPIC_API_KEY and move LLM calls
  behind an owned proxy (the packaged exe ships backend/.env otherwise);
  PvP payloads are client-relayed (spoofable) — server-side validation
  needed before ranked play matters.

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
