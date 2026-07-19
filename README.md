# Tower of Eternity

A roguelike tower-climbing gacha RPG. You are the manager. Heroes die permanently.

Summon heroes, send them up an endless Tower floor by floor, manage a home base
between climbs, and watch combat resolve as a deterministic simulation —
positioning, gear, class synergy, morale, and a hero's personality (their
"Ego") all matter, and a bad floor can permanently lose you a hero.

---

## 🎮 Playtest — Send This to Friends

**To play (no coding needed):**

1. Install **Python 3.11 or newer** from [python.org](https://www.python.org/downloads/) — during setup, **check "Add Python to PATH."**
2. Download this repo: green **`Code`** button above → **Download ZIP** → extract it anywhere.
3. Double-click **`PLAY.bat`**. The first run installs things for a few minutes, then the game opens in your browser at `http://localhost:8000`.
4. At the title screen, **make an account** — please use a **throwaway password**, not one you use elsewhere. Multiplayer (PvP, leaderboards) connects automatically.

That's it — you play on the built-in art. Everyone shares the same world server for multiplayer.

**Optional — generate your own unique heroes (needs an NVIDIA GPU, ~12GB free disk):**

1. Double-click **`INSTALL_GENERATION.bat`** once — it downloads the AI art tools and models (~9GB, resume-safe if interrupted).
2. Launch with `PLAY.bat`, then enter **any API key** in the tutorial or **Settings → AI Generation**. Your summons will now roll brand-new heroes in the game's art style instead of the shared gallery.

No NVIDIA GPU? Skip this — the game plays fine on the built-in art.

---

## 🖥️ Hosting the Multiplayer Server (Liam)

The World server (accounts, PvP, raids) runs in Docker on the Oracle VM at
**`https://170.9.255.240.nip.io`**. The game client already points at it.
SSH key: `C:\Users\liamh\.ssh\oracle_toe.key` · admin key:
`C:\Users\liamh\.ssh\toe_arena_admin_key.txt` (both outside this repo).

```bash
# SSH in
ssh -i C:\Users\liamh\.ssh\oracle_toe.key ubuntu@170.9.255.240

# --- Check status ---
sudo docker ps                       # is world-server running?
sudo docker logs --tail 50 world-server
curl -s https://170.9.255.240.nip.io/   # should return a status JSON

# --- Stop the server (players can't reach multiplayer while down) ---
sudo docker stop world-server

# --- Start it back up ---
sudo docker start world-server

# --- Restart (e.g. after config change) ---
sudo docker restart world-server
```

It's set to `--restart unless-stopped`, so it comes back on its own after a
reboot or crash — you only ever run `stop`/`start` to deliberately take
multiplayer offline or bring it back.

**Redeploying after code changes** to `arena_server/` or `backend/` — from
the repo root on your PC:

```bash
# 1. bundle both dirs (arena imports the backend combat engine)
tar czf /tmp/toe_deploy.tgz --exclude=__pycache__ --exclude="*.db" \
    --exclude=backend/static --exclude=backend/venv --exclude=backend/saves \
    arena_server backend

# 2. ship + rebuild + relaunch (keeps the arena.db volume + admin key)
scp -i C:\Users\liamh\.ssh\oracle_toe.key /tmp/toe_deploy.tgz ubuntu@170.9.255.240:/home/ubuntu/
ssh -i C:\Users\liamh\.ssh\oracle_toe.key ubuntu@170.9.255.240 \
  "rm -rf arena_server backend && tar xzf toe_deploy.tgz && \
   sudo docker build -q -f arena_server/Dockerfile -t tower-world-server . && \
   sudo docker rm -f world-server; \
   sudo docker run -d --name world-server --restart unless-stopped \
     -p 127.0.0.1:8001:8001 -e ARENA_ADMIN_KEY=\$(cat ~/admin_key 2>/dev/null || echo changeme) \
     -v world_data:/app/data tower-world-server"
```

> The arena `Dockerfile` must be built from the **repo root** (`-f arena_server/Dockerfile .`),
> not from inside `arena_server/` — the image needs the sibling `backend/`
> package for the shared combat simulation.

**Wipe multiplayer data** (junk accounts, corruption — playtest data is
disposable): `sudo docker rm -f world-server && sudo docker volume rm world_data`,
then run the launch command above to start fresh.

---

## Running It (Development)

**To just play** (packaged flow), use `PLAY.bat` — see the Playtest section
above. `app_launcher.py` is the older one-step desktop launcher (backend +
ComfyUI + a native window via PyInstaller specs) and still works if you
prefer a windowed build:

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
   (premium — better odds, builds Sparks toward a guaranteed 5★). Pulls
   reveal as face-down tarot cards — rarity-tiered card backs, click to
   flip (10-pulls deal all ten in a 3-4-3 spread over a summoning array).
2. **Heroes** → review stats, classes, aptitudes, Egos, skills (5-tier
   class-specific active/passive kits), traits, and weapon/armor affinity;
   set your teams (5 per team), pin favorites (♥ tab), compare any two
   heroes side by side, and give **gifts** — every hero secretly loves
   some gifts and resents others; loved gifts permanently raise a stat
   and build affinity (a 0-100 loyalty track).
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
   the Wall, Training Grounds, and Dining Hall; everything else — Farm,
   Market, Forge, Infirmary, up through the floor-75 Transcendence Core —
   is built with gold, all core facilities unlocked by floor 25), cook
   Farm ingredients into consumables, refine Aether ship fuel, rest the
   roster, design your Team Banner, and read the Hero Chatter log / Lore
   Journal. The Wall is the foundation: no facility can be upgraded above
   its level. In the Base Hierarchy, every hero lives on a base
   floor (Floor 1 by default; a new floor unlocks every 10 Tower floors) —
   spreading them out trades a bigger stat bonus per hero against coverage.
7. **World** → everything multiplayer: PvP arena against snapshot teams,
   PvP/PvE leaderboards, and a training market — with base raids and
   server-wide tournaments designed in as coming-soon sections. The game
   auto-connects to the World server (address:
   `DEFAULT_ARENA_SERVER_URL` in `frontend/src/api/arenaServerClient.js`).
8. **Achievements** → milestones across Tower/Summoning/Roster/Combat/
   Economy/Equipment/Arena, with a Claim All button. Rewards are gems and,
   for the hardest, star-tiered Summon Tickets — consumables (Items tab)
   that guarantee a 4★+/5★+/6★+/7★+ hero pull.

---

## Repository Layout

```
PLAY.bat                      # Player launcher — venv bootstrap + game at localhost:8000
INSTALL_GENERATION.bat        # Optional: local AI hero generation (NVIDIA GPU)
generation/loras/             # Hero style models (git LFS) pulled by the installer
app_launcher.py               # Older one-step desktop launcher (backend + ComfyUI + window)
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

arena_server/                 # The World server — separate FastAPI service you
                              #   host for PvP (accounts, ELO, matches, market).
                              #   Has its own Dockerfile:
                              #     docker build -t tower-world-server ./arena_server
                              #     docker run -d -p 8001:8001 \
                              #       -e ARENA_ADMIN_KEY=<long-random-string> \
                              #       -v world_data:/app/data tower-world-server
```

---

## Known Gaps

- **Arena PvP** — live on the Oracle VM (see Hosting above) and wired
  end-to-end. **One real gap:** arena_server can't report match results back to
  a local save, so the PvP-rating achievements stay at 0 progress until that
  round trip exists.
- **Personal generation key** — entering an API key switches on local hero
  generation (Option A, `INSTALL_GENERATION.bat`), but the key's *value* is not
  yet consumed by a hosted service; it's a local on/off switch for now.
- **Hydra family** — Hydra, Hydra Spawn, Wyvern Stormrider, and the Hydra
  Sovereign boss are cut from the roster pending a stronger monster art model;
  they'll return once `ToE_Monsters_v2` is trained.
- **Summon Tickets** — implemented (`/gacha/use-ticket`); currently only
  obtainable as Achievement rewards. Tier art (4★–7★) uses placeholders.
- **Enemy roster art** — floor waves are implemented; enemy art needs polish.
