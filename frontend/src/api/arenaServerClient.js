// Talks to the separately-hosted World/Arena server (arena_server/), not
// the player's local backend. Players never configure this — the game
// auto-connects to DEFAULT_ARENA_SERVER_URL. Change that constant to your
// hosted server's address before shipping a build. A localStorage override
// (arenaServerUrl) still wins if present, for dev/testing against a
// different host — settable from the console:
//   localStorage.setItem('arenaServerUrl', 'http://other-host:8001')
// Production arena on the Oracle VM (Caddy TLS in front of the container).
// localStorage 'arenaServerUrl' still overrides for local dev.
export const DEFAULT_ARENA_SERVER_URL = 'https://170.9.255.240.nip.io'

const URL_KEY = 'arenaServerUrl'
const TOKEN_KEY = 'arenaServerToken'
const USERNAME_KEY = 'arenaServerUsername'

export function getArenaServerUrl() {
  return localStorage.getItem(URL_KEY) || DEFAULT_ARENA_SERVER_URL
}

export function setArenaServerUrl(url) {
  localStorage.setItem(URL_KEY, url.replace(/\/+$/, ''))
}

export function getArenaToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function getArenaUsername() {
  return localStorage.getItem(USERNAME_KEY) || ''
}

export function clearArenaSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USERNAME_KEY)
}

async function arenaRequest(path, options = {}, auth = false) {
  const base = getArenaServerUrl()
  if (!base) throw new Error('Set the Arena server address first.')
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getArenaToken()
    if (!token) throw new Error('Log in to the Arena server first.')
    headers['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(base + path, { headers, ...options })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Arena request failed')
  }
  return res.json()
}

export const arenaRegister = (username, password) =>
  arenaRequest('/arena/register', { method: 'POST', body: JSON.stringify({ username, password }) })

export async function arenaLogin(username, password) {
  const data = await arenaRequest('/arena/login', { method: 'POST', body: JSON.stringify({ username, password }) })
  localStorage.setItem(TOKEN_KEY, data.token)
  localStorage.setItem(USERNAME_KEY, data.username)
  return data
}

export const arenaSubmitTeam = (team) =>
  arenaRequest('/arena/submit_team', { method: 'POST', body: JSON.stringify({ team }) }, true)

export const arenaSetBanner = (banner) =>
  arenaRequest('/arena/banner', { method: 'POST', body: JSON.stringify({ banner }) }, true)

/* ── Guilds v1 (design: docs/guild-social-design.md) ── */
export const guildMine = () => arenaRequest('/guild/mine', {}, true)
export const guildRegistry = () => arenaRequest('/guild/registry', {}, true)
export const guildFound = (name, motto = '', banner = {}) =>
  arenaRequest('/guild/found', { method: 'POST', body: JSON.stringify({ name, motto, banner }) }, true)
export const guildApply = (guildId, message = '') =>
  arenaRequest('/guild/apply', { method: 'POST', body: JSON.stringify({ guild_id: guildId, message }) }, true)
export const guildDecide = (appId, accept) =>
  arenaRequest('/guild/applications/decide', { method: 'POST', body: JSON.stringify({ app_id: appId, accept }) }, true)
export const guildLeave = () => arenaRequest('/guild/leave', { method: 'POST' }, true)
export const guildCheckin = () => arenaRequest('/guild/checkin', { method: 'POST' }, true)
export const guildBossStrike = () => arenaRequest('/guild/boss/strike', { method: 'POST' }, true)
export const guildShop = () => arenaRequest('/guild/shop', {}, true)
export const guildShopBuy = (itemId) =>
  arenaRequest('/guild/shop/buy', { method: 'POST', body: JSON.stringify({ item_id: itemId }) }, true)

/* ── Social: allies ── */
export const socialAllies = () => arenaRequest('/social/allies', {}, true)
export const socialInvite = (username) =>
  arenaRequest('/social/invite', { method: 'POST', body: JSON.stringify({ username }) }, true)
export const socialDecide = (username, accept) =>
  arenaRequest('/social/decide', { method: 'POST', body: JSON.stringify({ username, accept }) }, true)
export const socialRemove = (username) =>
  arenaRequest('/social/remove', { method: 'POST', body: JSON.stringify({ username }) }, true)

export const arenaChallenge = (opponent) =>
  arenaRequest('/arena/challenge', { method: 'POST', body: JSON.stringify({ opponent }) }, true)

export const arenaMatchmake = () =>
  arenaRequest('/arena/matchmake', { method: 'POST' }, true)

export const arenaUpdateFloor = (highest_floor) =>
  arenaRequest('/arena/update_floor', { method: 'POST', body: JSON.stringify({ highest_floor }) }, true)

export const arenaLeaderboard = (limit = 20) =>
  arenaRequest(`/arena/leaderboard?limit=${limit}`)

export const arenaMyRewards = () =>
  arenaRequest('/arena/my_rewards', {}, true)

export const arenaClaimReward = (reward_id) =>
  arenaRequest('/arena/claim_reward', { method: 'POST', body: JSON.stringify({ reward_id }) }, true)

export const arenaMarketList = (hero_name, hero_class, hero_stats, hero_skills, gem_cost) =>
  arenaRequest('/arena/market/list', { method: 'POST', body: JSON.stringify({ hero_name, hero_class, hero_stats, hero_skills, gem_cost }) }, true)

export const arenaMarketGet = () =>
  arenaRequest('/arena/market', {}, true)

export const arenaMarketHire = (listing_id) =>
  arenaRequest('/arena/market/hire', { method: 'POST', body: JSON.stringify({ listing_id }) }, true)

/* ============================================================
   Base Raids — asymmetric PvP against other managers' bases.
   Defense snapshots come from the local backend (see client.js
   raidDefenseSnapshot); these talk to the World/Arena server.
   ============================================================ */
export const arenaRaidOptIn = (enable) =>
  arenaRequest('/arena/raid/opt_in', { method: 'POST', body: JSON.stringify({ enable }) }, true)

export const arenaRaidSubmitDefense = (defenders, base_defense, ship_tier = 0, lootable = {}, counter_intel = {}) =>
  arenaRequest('/arena/raid/submit_defense', { method: 'POST', body: JSON.stringify({ defenders, base_defense, ship_tier, lootable, counter_intel }) }, true)

export const arenaRaidMap = (radius) =>
  arenaRequest(`/arena/raid/map${radius ? `?radius=${radius}` : ''}`, {}, true)

export const arenaRaidScout = (target, scout_power = 0) =>
  arenaRequest('/arena/raid/scout', { method: 'POST', body: JSON.stringify({ target, scout_power }) }, true)

export const arenaRaidAttack = (target, team, ship_tier = 0) =>
  arenaRequest('/arena/raid/attack', { method: 'POST', body: JSON.stringify({ target, team, ship_tier }) }, true)

export const arenaRaidClaimPrisoner = (raid_id, hero_id) =>
  arenaRequest('/arena/raid/claim_prisoner', { method: 'POST', body: JSON.stringify({ raid_id, hero_id }) }, true)

export const arenaRaidEvents = () =>
  arenaRequest('/arena/raid/events', {}, true)

/* ============================================================
   Grand Tournament — server-wide 1v1 / 2v2 / 4v4 brackets.
   ============================================================ */
export const arenaTournaments = () =>
  arenaRequest('/arena/tournaments', {}, true)

export const arenaTournamentRegister = (format, team) =>
  arenaRequest('/arena/tournament/register', { method: 'POST', body: JSON.stringify({ format, team }) }, true)

export const arenaTournamentStandings = (format, week) =>
  arenaRequest(`/arena/tournament/standings?format=${encodeURIComponent(format)}${week ? `&week=${encodeURIComponent(week)}` : ''}`, {}, true)

// ─── The Herald's Wire (chat) ────────────────────────────────────────
export const chatSend = (channel, text, to = null) =>
  arenaRequest('/chat/send', { method: 'POST', body: JSON.stringify({ channel, text, to }) }, true)
export const chatFetch = (channel, since = 0) =>
  arenaRequest(`/chat/fetch?channel=${encodeURIComponent(channel)}&since=${since}`, {}, true)
export const chatWhispers = () => arenaRequest('/chat/whispers', {}, true)
export const chatWhisperThread = (other, since = 0) =>
  arenaRequest(`/chat/whisper/${encodeURIComponent(other)}?since=${since}`, {}, true)

// ─── Guild Perks ─────────────────────────────────────────────────────
export const guildPerks = () => arenaRequest('/guild/perks', {}, true)
export const guildPerkBuy = (perkId) =>
  arenaRequest('/guild/perks/buy', { method: 'POST', body: JSON.stringify({ perk_id: perkId }) }, true)

// ─── Lodge War + match history ───────────────────────────────────────
export const guildWar = () => arenaRequest('/guild/war', {}, true)
export const arenaMyMatches = (limit = 10) => arenaRequest(`/arena/my_matches?limit=${limit}`, {}, true)

// ── Account auth (startup login screen) ─────────────────────────────────────
// New /auth endpoints: email-based accounts. Same token storage as the
// legacy arena login, so every existing world feature keeps working.
export const EMAIL_KEY = 'arenaServerEmail'

export async function authRegister(email, username, password) {
  const data = await arenaRequest('/auth/register', { method: 'POST', body: JSON.stringify({ email, username, password }) })
  localStorage.setItem(TOKEN_KEY, data.token)
  localStorage.setItem(USERNAME_KEY, data.username)
  localStorage.setItem(EMAIL_KEY, data.email)
  return data
}

export async function authLogin(identifier, password) {
  const data = await arenaRequest('/auth/login', { method: 'POST', body: JSON.stringify({ identifier, password }) })
  localStorage.setItem(TOKEN_KEY, data.token)
  localStorage.setItem(USERNAME_KEY, data.username)
  if (data.email) localStorage.setItem(EMAIL_KEY, data.email)
  return data
}

export const authMe = () => arenaRequest('/auth/me', {}, true)

export async function authDiscord() {
  return arenaRequest('/auth/discord', { method: 'POST' })
}

export async function authGoogle() {
  // Scaffold: server returns 501 until GOOGLE_CLIENT_ID is configured there.
  return arenaRequest('/auth/google', { method: 'POST' })
}
