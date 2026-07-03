# Asset Layout & Conventions

One rule decides where art lives: **does the backend need the file?**

- **Backend needs it** (generates it, composites it server-side, or serves it
  to combat/facility endpoints) → `backend/static/…`, served at `/static/…`
- **Frontend-only display art** → `frontend/public/…`, served at the root

The Vite dev proxy forwards `/static` to the backend, and the packaged app
serves both from FastAPI, so URLs are identical in dev and shipped builds.

## backend/static/  (served at /static/)

| Folder | Contents | Notes |
|---|---|---|
| `portraits/` | Runtime-generated hero portraits + pre-generated pool | ComfyUI output, per-profile |
| `portraits/enemies/{normal,elite,miniboss,boss,raid_boss}/` | Enemy art by tier, `snake_case_name.png` | `waveN/` subfolders allowed |
| `card_templates/` | Server-composited hero card frames | `CARD_STYLE_VERSION` cache-busts |
| `icons/classes/` | Class icons the card medallion is composited from | server-side PIL paste |
| `facilities/` | Facility banners | see naming below |
| `logo/` | App/window branding | |

### Facility art naming (the convention)

`{slug}_tier{n}.png` — slug is the facility name lowercased, spaces →
underscores. Tiers 1–4 (art is CAPPED at tier 4; levels 45+ reuse tier 4).
Tier switches happen at facility levels **1 / 5 / 15 / 30**.

Current slugs: `wall`, `training_grounds`, `dining_hall`, `farm`, `market`,
`forge`, `infirmary`, `vault`, `alchemist_lab`, `tavern`, `skydock`,
`bastion`, `shrine`, `mage_tower`, `mirror_of_fate`, `bestiary`,
`reliquary`, `chronosphere`, `transcendence_core`.

A flat `{Facility Name}.png` (title case, spaces kept) is the final
fallback if no tier file exists. The lookup walks: exact tier → lower
tiers → flat file → hidden.

## frontend/public/  (served at /)

| Path | Contents |
|---|---|
| `icons/` | **The single home for all square UI/item icons.** `lowercase_underscores.png`. Item/material/consumable icons resolve by slugified item name (`Iron Ore (C)` → `iron_ore.png`) via `components/ItemIcon.jsx` — drop a correctly-named file and it just appears. |
| `icons/emblems/` | Banner emblems, background keyed to transparency |
| `icons/banners/` | Banner cloth templates `banner_tier{1-4}.png`, keyed to transparency |
| `images/battleships/` | Skydock ship art `ship_{1-5}.png` |
| `bgm.mp3`, `tower_limitless_wide.png` | Music, tower background |

### Late-facility minimum art tiers

Facilities that unlock deep in the climb never show low-tier art — the
base around them is already grand. `MIN_ART_TIER` in BasePage.jsx:
Bestiary/Reliquary start at **tier 2**, Chronosphere at **tier 3**,
Transcendence Core at **tier 4**. Art below those tiers intentionally
doesn't exist.

## Art still wanted (placeholders or fallbacks in place)

- `backend/static/facilities/bestiary_tier{2,3,4}.png` — still "ART
  PENDING" placeholders (the prompts need the interior-wall attachments)
- Vaelor, the Fallen Ascendant — AUTO-GENERATES on launch now, into
  `enemies/miniboss/vaelor__the_fallen_ascendant.png` (delete that file to
  re-roll his look)
- Real `Tavern.png` / `Wall.png` flat banners (placeholders) — tier art exists, so these barely show

## Adding new item icons

1. Name the file after the in-game item: lowercase, underscores, no tier
   suffix (`mandrake_root.png`, `high_health_potion.png`, `aether_crystal.png`).
2. Drop it in `frontend/public/icons/`.
3. If the in-game name doesn't slugify cleanly to the filename, add one line
   to `NAME_OVERRIDES` in `frontend/src/components/ItemIcon.jsx`.
