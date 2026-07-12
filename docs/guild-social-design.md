# Guild + Social — design (SIGNED OFF 2026-07-06, with Liam's decisions)

> **STATUS (2026-07-12): SHIPPED.** Fully implemented — arena_server/guilds.py (founding/registry/applications/check-in/daily boss/shop/perks/allies/weekly war) + frontend GuildHall (4 tabs incl. live guild chat). This doc is the historical design record.

*Terminology: **GUILD** everywhere in the UI. The mockups' "Lodge"/"kin"
flavor text is replaced on the frontend — backend names use `guild_*`.*

Mockup sources: `public/screenshots/Guild Hall - {Daily Boss,Guild Chat,Shop}.png`,
`Squad Overview - All Heroes.png`, `World - Friends Leaderboard.png`, plus
`public/html/Guild Hall - Illuminated.dc.html`. (Older notes: "Herald -
Illuminated" in mockups/ is the Guild War season screen, "Guild War -
Illuminated" is the Registry/founding screen.)

## Decisions (Liam, 2026-07-06)
1. **Size cap**: base 20 members, upgradeable to 50 (guild-coin or renown-gated upgrades).
2. **Founding fee**: 50,000 gold (paid locally, like scout fees).
3. **Hero loans / Hero Exchange: SCRAPPED.** Allies list stays; no lending mechanic.
4. **Guild War cadence**: weekly banks, 4-week season.

## Where it lives
All arena-server (world) data — same auth/patterns as raids/tournaments.
Local backend only caches perk blobs and pays local-economy fees.

## Guild Hall (4 tabs: ROSTER · GUILD SHOP · DAILY BOSS · GUILD CHAT)
Header: guild banner + name, rank badge, KIN n/cap, ONLINE count,
TREASURY (guild coin), GUILD WAR button, **CHECK IN** (daily: contributes
pledge + small guild-coin drip).

- **Roster**: members, ranks (MASTER > OFFICER > MEMBER), deepest floor,
  weekly pledge. Officers accept applications, start wars.
- **Daily Guild Boss** (screenshot): a shared-HP boss ("rises each dawn"),
  every member may strike **3×/day** (strike = auto-resolved combat sim with
  your submitted team, damage banked against shared HP). Tribute leaderboard
  by damage %. If felled before reset: guild coin ~120 for all, top damage
  gets a bonus seal. Resets daily UTC.
- **Guild Shop** (screenshot): bought with **guild coin** (earned by pledge,
  check-in, and hunt). Weekly-limited stock, restocks on a timer:
  Rare Seal Cache 800 (guaranteed 5★ class seal, 1/wk) · Aether Bundle 450
  (+50 aether, 3/wk) · Emberleaf Ration 120 (5/wk) · Skydock Refit Voucher
  300 (2/wk) · rank-gated cosmetics (Guild Banner Dye, Crest Sigil Frame).
  Purchases apply locally via the client (same economy split as scouting).
- **Guild Chat**: existing chat system with a guild channel.
- **Perks**: passive buffs bought from pooled treasury; applied locally via
  a cached `guild_perks` blob synced to the local backend.

## Guild War (seasonal ladder)
Each member's tower floors cleared during the season pledge points to the
guild ("FLOORS PLEDGED" — data already reported via arenaUpdateFloor).
Weekly the ladder banks renown (4 banks per season); rival-guild pairing
shows a head-to-head bar. No real-time combat — a pledge race.

## Social — "Allies"
Tables: `allies` (username_a, username_b, status pending/accepted, since).
- Invite by name, accept/decline, presence line (last-known screen via
  lightweight heartbeat), Direct Message = private chat channel.
- **Friends Leaderboard** (World screenshot): allies ranked by deepest floor.
- Hero Exchange rail from the mockup: dropped (decision 3).

## Server tables
`guilds` (id, name, banner_json, motto, founder, renown, treasury, member_cap),
`guild_members` (guild_id, username, rank, joined_at, weekly_pledge, guild_coin,
last_checkin), `guild_applications`, `guild_boss` (guild_id, date, boss_key,
max_hp, hp, strikes_json), `guild_shop_purchases` (weekly limits), `allies`.

## Client
- GuildHub with the 4 tabs, launched from the TopBar guild-crest icon;
  Registry/founding + Apply modal for the guildless state.
- Social.jsx static shell → wire allies + friends leaderboard.
