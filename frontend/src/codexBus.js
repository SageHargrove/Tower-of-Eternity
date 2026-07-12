/*
 * CODEX DISCOVERY BUS — see-it-to-learn-it.
 *
 * An entry unlocks the first time the player actually ENCOUNTERS the thing
 * (first boss phase seen unlocks BOSS PHASES, first deed unlocks DEEDS...).
 * Unlocks persist in localStorage per profile-agnostic install; a toast
 * announces each new page so discovery feels like a reward, not a wiki.
 */
import { emitToast } from './toastBus'
import { playDeedChime } from './audio'

const KEY = 'toe_codex_unlocked'

export function getUnlocked() {
  try { return new Set(JSON.parse(localStorage.getItem(KEY) || '[]')) } catch { return new Set() }
}

export function isUnlocked(id) {
  return getUnlocked().has(id)
}

export function unlockCodex(id, title) {
  const set = getUnlocked()
  if (set.has(id)) return false
  set.add(id)
  try { localStorage.setItem(KEY, JSON.stringify([...set])) } catch {}
  try { playDeedChime() } catch {}
  emitToast({
    title: 'CODEX — NEW ENTRY',
    lines: [{ label: '', value: title || id.replace(/_/g, ' ').toUpperCase() }],
    borderColor: 'var(--lavender)',
  })
  return true
}

// Scan a finished fight's log + result for first-encounter unlocks — one
// call from the tower result handler covers most of combat's discoveries.
const ELITE_PREFIXES = ['Armored ', 'Frenzied ', 'Colossal ', 'Deadly ', 'Regenerating ', 'Warded ']
export function scanCombatForDiscoveries(result) {
  try {
    const combat = result?.combat || result
    if (!combat) return
    const log = (combat.log || []).join('\n')
    if (log.includes('ENTERS A NEW PHASE')) unlockCodex('boss_phases', 'BOSS PHASES')
    if (log.includes('FLOOR CONDITION')) unlockCodex('floor_conditions', 'FLOOR CONDITIONS')
    if (log.includes("TOWER'S WALL")) unlockCodex('walls', 'THE WALLS')
    if (log.includes('Undying Will') || log.includes('foresaw this')) unlockCodex('death_saves', 'CHEATING DEATH')
    if (log.includes('SURVIVAL FLOOR')) unlockCodex('survival', 'THE SURVIVAL SWARM')
    const enemies = combat.initial_state?.enemies || []
    if (enemies.some(e => ELITE_PREFIXES.some(p => e.name?.startsWith(p)))) unlockCodex('elites', 'ELITE AFFIXES')
    if (result?.deeds_earned?.length) unlockCodex('deeds', 'DEEDS')
    if (result?.beast_captured) unlockCodex('bestiary', 'THE BESTIARY')
    if ((combat.dead_heroes || []).length) unlockCodex('death', 'DEATH IS PERMANENT')
  } catch {}
}
