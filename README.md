# Tower of Eternity

A roguelike tower-climbing gacha RPG. You are the manager. Heroes die permanently.

Summon heroes, send them up an endless Tower floor by floor, manage a home base
between climbs, and watch combat resolve as a deterministic simulation —
positioning, gear, class synergy, morale, and a hero's personality (their
"Ego") all matter, and a bad floor can permanently lose you a hero.

---

## Running It

**To just play the game:** run `app_launcher.py` (or the packaged desktop
build, if you've built one with PyInstaller — see `app_launcher.spec` /
`InfiniteGacha.spec`). It boots the backend, boots ComfyUI (for portrait
generation), and opens a desktop window pointed at the game — one step,
no manual terminals.

```
python app_launcher.py
```

The backend serves the frontend's built `dist/` directly, so if you've
changed any frontend code, rebuild it first:

```
cd frontend
npm run build
```

**For active frontend development** (live reload instead of rebuilding
every change), run the Vite dev server separately instead of relying on
the built `dist/`:

```
# Terminal 1 — Backend
cd backend
venv\Scripts\activate
python -m uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend (hot reload)
cd frontend
npm run dev
```

ComfyUI is only needed for generating new hero/enemy portraits — the game
runs fine without it, portraits just won't regenerate.

Save data lives in `backend/saves/<profile>.db` (git-ignored — one SQLite
file per profile). DB schema migrations run automatically at startup.

---

## How to Play

1. **Summon** → pull heroes and equipment with gold (standard) or gems
   (premium — better odds, builds Sparks toward a guaranteed 5★).
2. **Heroes** → review stats, classes, aptitudes, Egos, skills (5-tier
   class-specific active/passive kits), traits, and weapon/armor affinity;
   set your teams (5 per team), pin favorites (♥ tab), and compare any two
   heroes side by side.
3. **Synthesis Chamber** → sacrifice up to 3 heroes to feed another XP
   (doubled on matching-class Ego Resonance, with a chance to inherit
   skills/traits). The whole living roster witnesses the rite — trauma,
   stress, and morale loss compound with every additional soul consumed.
4. **Tower** → advance floor by floor — combat, events (narrative choices,
   sometimes turning into real fights), explore, escort, survival, ambush,
   blitz, and more. Every 5th floor is a miniboss comp-check (survival /
   behemoth / assassin / twins), every 10th a boss. Combat resolves
   automatically; deaths are permanent and leave a Legacy bonus. Floor
   type stays hidden (?) until you've visited it once.
5. **Items (Vault)** → equipment (weapons — Sword/Spear/Tome/Bow/Dagger;
   armor — Robe/Light/Brigandine/Heavy; accessories — Ring/Amulet/Charm,
   with **two** accessory slots per hero), each type with its own stat
   identity and class-restricted equip. Storage is capped — build/upgrade
   the Vault facility to expand it. Consumables (potions, scrolls, summon
   tickets) are used from here.
6. **Base** → between climbs: assign heroes to Facilities (you start with
   the Training Grounds and Restaurant; build the Forge, Infirmary, Market,
   and more), rest the roster, buy Base Upgrades, and read the Hero Chatter
   log / Lore Journal. In the Base Hierarchy, every hero lives on a base
   floor (Floor 1 by default; a new floor unlocks every 10 Tower floors) —
   spreading them out trades a bigger stat bonus per hero against coverage.
7. **Arena** → PvP against another player's snapshot team (see Known Gaps).
8. **Achievements** → milestones across Tower/Summoning/Roster/Combat/
   Economy/Equipment/Arena, with a Claim All button. Rewards are gems and,
   for the hardest, star-tiered Summon Tickets — consumables (Items tab)
   that guarantee a 4★+/5★+/6★+/7★+ hero pull.

---

## Repository Layout

```
app_launcher.py               # One-step desktop launcher (backend + ComfyUI + window)
Dockerfile                    # Container build for the backend
docs/                         # Design/plan documents
openspec/                     # Feature specs (openspec workflow)

backend/
  main.py                     # FastAPI app, CORS, serves frontend dist/ + static assets
  database.py                 # SQLite schema + startup migrations, per-profile saves
  services/                   # Game logic — combat, gacha, classes, egos, legacies,
                              #   equipment (weapon/armor/accessory type identities),
                              #   facilities, materials, level/ascension, skills,
                              #   morale, events, LLM flavor text, portrait generation
  routers/                    # API endpoints — heroes, gacha, tower, base, runs,
                              #   equipment, relics, crafting, arena, profiles, chat
  scripts/                    # One-off/maintenance scripts (icon generation,
                              #   card regeneration, db patches)
  tests/                      # Test scripts
  static/icons/               # Equipment art (weapons/armor, rarity-tiered)
  static/facilities/          # Facility banner art
  static/portraits/           # Hero/enemy/boss art (git-ignored, locally generated)
  saves/                      # Per-profile save DBs (git-ignored)

frontend/src/
  App.jsx                     # Tab layout, onboarding tour, resource header
  api/client.js               # All API calls (+ arenaServerClient.js for PvP)
  components/                 # HeroCard, SynthesisChamber, CompareModal, DialogHost,
                              #   GameIcon, EquipmentTypeIcon, CombatArena, overlays...
  pages/                      # Summon, Heroes, Tower, Base, Arena, Achievements,
                              #   Inventory (Vault), Log
frontend/public/icons/        # UI icon art (currencies, classes, floors, accessories)

arena_server/                 # Separate small FastAPI service for Arena match
                              #   resolution — not the main game backend
```

---

## Known Gaps

- **Arena PvP** — fully wired end-to-end (ArenaPage.jsx → arenaServerClient.js
  → arena_server/, with the main backend exporting team snapshots). Matchmaking
  and leaderboards are implemented in arena_server/. Not currently running as a
  live service — game balance is still moving too fast for hosted PvP. **One
  real gap:** arena_server can't report match results back to a local save, so
  the PvP-rating achievements stay at 0 progress until that round trip exists.
- **Summon Tickets** — implemented (`/gacha/use-ticket`); currently only
  obtainable as Achievement rewards. Tier art (4★–7★) uses placeholders.
- **Enemy roster art** — floor waves are implemented; enemy art needs polish.
