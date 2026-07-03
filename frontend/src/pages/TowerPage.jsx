import React, { useState, useEffect } from 'react'
import { getAllTeams, getBase, enterFloor, resolveEvent, resolveExplore, previewFloor, getNarrative } from '../api/client'
import { arenaUpdateFloor, getArenaToken } from '../api/arenaServerClient'
import { emitToast } from '../toastBus'
import CombatArena from '../components/CombatArena'
import FairyGuide from '../components/FairyGuide'
import { CardFrame } from '../components/HeroCard'
import { EquipmentTypeIcon } from '../components/EquipmentTypeIcon'
import GameIcon from '../components/GameIcon'

// Time-skip combat persistence — see resumeTurnIndex below. Discard
// anything older than this even if found; a fight left "in progress" for
// an hour+ is more likely a stale/abandoned tab than one worth resuming.
const ACTIVE_COMBAT_KEY = 'tower_active_combat'
const ACTIVE_COMBAT_MAX_AGE_MS = 20 * 60 * 1000
const TURN_DELAY_MS = 800

function saveActiveCombat(result, resolvedFloor) {
  try {
    sessionStorage.setItem(ACTIVE_COMBAT_KEY, JSON.stringify({
      result, resolvedFloor, deployedAt: Date.now(),
    }))
  } catch {}
}

function clearActiveCombat() {
  try { sessionStorage.removeItem(ACTIVE_COMBAT_KEY) } catch {}
}

function loadActiveCombat() {
  try {
    const raw = sessionStorage.getItem(ACTIVE_COMBAT_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed?.deployedAt || Date.now() - parsed.deployedAt > ACTIVE_COMBAT_MAX_AGE_MS) {
      clearActiveCombat()
      return null
    }
    return parsed
  } catch {
    return null
  }
}

// The 10 biomes, one per 10-floor zone — derived from enemy_families.py's
// spawn tables. Art lives in /images/floors/<slug>.png; the zone tile grid
// uses it as a background so each stretch of the climb reads distinctly.
const ZONES = [
  { name: 'Overgrown Caverns', slug: 'overgrown_caverns', blurb: 'Root-choked tunnels where goblins, spiders, and wolves den.' },
  { name: 'Savage Badlands', slug: 'savage_badlands', blurb: 'Sun-cracked wastes ruled by orcs, trolls, and dire wolf packs.' },
  { name: 'Sunken Swamp', slug: 'sunken_swamp', blurb: 'Fetid mire crawling with hobgoblins and lizardmen.' },
  { name: 'Profane Catacombs', slug: 'profane_catacombs', blurb: 'Desecrated halls of rotting ghouls and rampaging minotaurs.' },
  { name: 'Ashen Depths', slug: 'ashen_depths', blurb: 'Smouldering caverns where the Ashen Colossus stirs.' },
  { name: 'Crystalline Labyrinth', slug: 'crystalline_depths', blurb: 'A maze of living stone — sentinels and golems keep the walls.' },
  { name: 'Blood Lake', slug: 'blood_lake', blurb: 'Crimson waters prowled by vampire spawn and nagas.' },
  { name: 'Dread Peaks', slug: 'dread_peaks', blurb: 'Storm-lashed summits of death knights, hydras, and manticores.' },
  { name: 'Abyssal Rift', slug: 'abyssal_rift', blurb: 'A wound in reality leaking imps and masked horrors.' },
  { name: "Dragon's Boneyard", slug: 'dragons_boneyard', blurb: 'The final ascent — liches, dragons, and dracoliches guard the peak.' },
]

// Zones above the built-out 100-floor table just repeat the final boneyard
// biome rather than breaking — nothing past floor 100 is designed yet.
function zoneFor(zoneIndex) {
  return ZONES[Math.min(zoneIndex, ZONES.length - 1)]
}

const FLOOR_ICONS = {
  field_combat: 'class_rogue',
  miniboss: 'boss_skull',
  miniboss_survival: 'element_water',
  miniboss_behemoth: 'element_earth',
  miniboss_assassin: 'thief_knife',
  miniboss_twins: 'class_twins',
  boss: 'boss_demon',
  resource: 'gem',
  event: 'mystery_encounter',
  survival: 'class_defender',
  defend: 'tower',
  explore: 'map',
  escort: 'creature_horse',
  conquest: 'element_fire',
  war: 'class_warrior',
  retrieve: 'coin_pouch',
  ambush: 'element_dark',
  blitz: 'element_lightning',
  cursed_ground: 'element_ritual',
}

// FLOOR_TYPE_INFO colors are 3-digit hex shorthand (#a44) — appending an
// alpha suffix directly (`${color}22`) produces an invalid 5-digit hex
// string that browsers silently drop, falling back to a plain white/gray
// <button> background (confirmed bug: floor tiles went blank-white).
// Expands to 6-digit hex first so the alpha suffix actually forms valid
// 8-digit #RRGGBBAA.
function hexWithAlpha(hex, alpha) {
  const expanded = hex.length === 4
    ? '#' + [...hex.slice(1)].map(c => c + c).join('')
    : hex
  return `${expanded}${alpha}`
}

const FLOOR_TYPE_INFO = {
  field_combat: { color: '#b65', label: 'Field Combat', blurb: 'A looser skirmish, open ground.' },
  miniboss: { color: '#c63', label: 'Miniboss', blurb: 'A tougher single enemy.' },
  miniboss_survival: { color: '#368', label: 'Miniboss: Survival', blurb: 'Endurance check — outlast a real wave.' },
  miniboss_behemoth: { color: '#765', label: 'Miniboss: Behemoth', blurb: 'DPS check — huge HP/DEF, tiny attack.' },
  miniboss_assassin: { color: '#a13', label: 'Miniboss: Assassin', blurb: 'Tank check — blinding speed, brutal burst.' },
  miniboss_twins: { color: '#759', label: 'Miniboss: Twins', blurb: 'Comp check — one resists physical, one resists magic.' },
  // miniboss_mirror retired — no counterplay; existing cached floors are
  // re-rolled by a DB migration, so nothing renders this type anymore.
  boss: { color: '#e33', label: 'Boss', blurb: 'The floor\'s guardian.' },
  event: { color: '#86c', label: 'Event', blurb: 'A choice encounter.' },
  survival: { color: '#c44', label: 'Survival', blurb: 'A fight against a larger enemy wave.' },
  defend: { color: '#64a', label: 'Defend', blurb: 'A fight to hold a chokepoint.' },
  explore: { color: '#4a6', label: 'Explore', blurb: 'A risk/reward discovery.' },
  escort: { color: '#c93', label: 'Escort', blurb: 'Protect an NPC — a win lifts the team\'s morale.' },
  conquest: { color: '#933', label: 'Conquest', blurb: 'A larger enemy wave — clear it by force.' },
  war: { color: '#722', label: 'War', blurb: 'The hardest non-boss fight on this floor.' },
  retrieve: { color: '#a82', label: 'Retrieve', blurb: 'Something valuable is guarded here.' },
  ambush: { color: '#414', label: 'Ambush', blurb: 'Enemies get a guaranteed first strike.' },
  blitz: { color: '#dd4', label: 'Blitz', blurb: 'Enemies grow stronger every round — burst them down fast.' },
  cursed_ground: { color: '#5a3', label: 'Cursed Ground', blurb: 'Your team starts the fight already debuffed.' },
}

function FloorBadge({ type }) {
  const info = FLOOR_TYPE_INFO[type]
  return (
    <span style={{
      background: info?.color || '#555',
      padding: '0.15rem 0.4rem',
      borderRadius: 4,
      fontSize: '0.7rem',
      textTransform: 'uppercase',
      letterSpacing: '0.5px'
    }}>
      {info?.label || type}
    </span>
  )
}

// Survival Swarm is a random 35%-chance ALTERNATIVE rolled inside a
// miniboss floor's combat resolution (services/combat_service.py's
// SWARM_SURVIVAL_CHANCE) — not its own floor type, so the static
// "Miniboss: A tougher single enemy" blurb was actively wrong (and
// confusing — see the 30-50 enemy swarm) whenever that roll landed.
const SURVIVAL_SWARM_INFO = { color: '#c44', label: 'Survival Swarm', blurb: 'An overwhelming horde — outlast the clock, don\'t try to clear it.' }

function FloorTypeCallout({ type, isSurvivalSwarm }) {
  const info = isSurvivalSwarm ? SURVIVAL_SWARM_INFO : FLOOR_TYPE_INFO[type]
  if (!info) return null
  return (
    <div style={{
      maxWidth: '600px',
      margin: '0 auto 1.5rem auto',
      textAlign: 'center',
      padding: '0.6rem 1rem',
      background: `${info.color}22`,
      border: `1px solid ${info.color}`,
      borderRadius: 6,
    }}>
      <span style={{ fontFamily: 'Cinzel, serif', textTransform: 'uppercase', letterSpacing: '1px', color: info.color }}>
        {info.label} Floor
      </span>
      <span className="text-dim" style={{ marginLeft: '0.6rem', fontSize: '0.85rem' }}>
        {info.blurb}
      </span>
    </div>
  )
}

// Multi-team floors run as N parallel arenas (see team_results), each with
// its own initial_state — the post-combat summary screen still wants one
// combined roster, so merge them here instead of duplicating this in both
// call sites.
function mergedCombatEntities(result) {
  const teamResults = (result?.combat?.team_results || result?.team_results || []).filter(Boolean)
  if (teamResults.length > 0) {
    const heroes = teamResults.flatMap(tr => tr.initial_state?.heroes || [])
    const enemies = teamResults.flatMap(tr => tr.initial_state?.enemies || [])
    return { heroes, enemies }
  }
  return result?.initial_state || result?.combat?.initial_state || null
}

function heroCombatStatus(heroId, lastResult, combatEntities) {
  if (lastResult.combat?.dead_heroes?.includes(heroId)) return 'kia'
  const surv = lastResult.combat?.surviving_heroes?.find(s => s.id === heroId)
  if (!surv) return 'unknown'
  const entity = combatEntities?.heroes?.find(h => h.id === heroId)
  if (entity && surv.health < entity.max_health) return 'injured'
  return 'alive'
}

function PostCombatScreen({ lastResult, combatEntities, onReturn, onRerun, busy }) {
  if (!lastResult) return null;

  const metrics = lastResult.combat?.combat_metrics || {};
  const maxDmg = Math.max(1, ...Object.values(metrics));
  const mvpId = Object.entries(metrics).sort((a, b) => b[1] - a[1])[0]?.[0]
  const wasVictory = !lastResult.run_over && lastResult.combat?.winner !== 'enemies';
  const continueLabel = wasVictory ? 'Continue' : 'Retreat'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginTop: '2rem' }}>

      {lastResult.narrative && (
        <div className="card" style={{ fontStyle: 'italic', color: 'var(--text-dim)', lineHeight: 1.6 }}>
          {lastResult.narrative}
        </div>
      )}

      {lastResult.chatter_line && (
        <div className="card" style={{ textAlign: 'center', borderColor: wasVictory ? 'var(--green)' : 'var(--red)' }}>
          <div style={{ fontStyle: 'italic', fontSize: '1.05rem' }}>"{lastResult.chatter_line.line}"</div>
          <div className="text-dim" style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>— {lastResult.chatter_line.name}</div>
        </div>
      )}

      {/* Team Status */}
      <div className="card">
        <div className="section-header">Team Status</div>
        <div style={{ display: 'flex', gap: '1.2rem', flexWrap: 'wrap' }}>
          {combatEntities?.heroes?.map(h => {
            const status = heroCombatStatus(h.id, lastResult, combatEntities)
            const STATUS_LABEL = { injured: 'Injured', kia: 'Killed In Action' }
            const isMvp = (metrics[h.id] || 0) > 0 && String(h.id) === String(mvpId)
            return (
              <div key={h.id} style={{ width: 96, textAlign: 'center', position: 'relative' }}>
                {isMvp && (
                  <div title="MVP" style={{ position: 'absolute', top: -18, left: '50%', transform: 'translateX(-50%)', zIndex: 10, filter: 'drop-shadow(0 0 4px var(--star5))' }}>
                    <GameIcon name="trophy" size={28} />
                  </div>
                )}
                <CardFrame birthStar={h.hero_star} status={status === 'alive' ? null : status} style={isMvp ? { boxShadow: '0 0 12px var(--star5)', border: '2px solid var(--star5)' } : undefined}>
                  {h.portrait_path ? (
                    <img
                      src={`/heroes/${h.id}/card-image?mini=true`}
                      draggable={false}
                      style={{ width: '100%', aspectRatio: '2 / 3', height: 'auto', objectFit: 'cover', objectPosition: 'center top', borderRadius: 4 }}
                      // Two-step fallback: try the composited card, then the
                      // raw portrait, then a dim silhouette — the portrait
                      // may still be generating in the background (combat
                      // never waits on ComfyUI), so a broken-image icon
                      // should never show.
                      onError={(e) => {
                        if (e.target.dataset.stage === 'raw') {
                          e.target.onerror = null
                          e.target.src = '/icons/mystery_encounter.png'
                          e.target.style.opacity = '0.35'
                          e.target.style.filter = 'grayscale(1)'
                          e.target.style.objectFit = 'contain'
                        } else {
                          e.target.dataset.stage = 'raw'
                          e.target.src = `/${h.portrait_path}`
                        }
                      }}
                    />
                  ) : (
                    // Portrait still generating in the background — a
                    // silhouette placeholder instead of a blank box, so
                    // combat never has to wait on ComfyUI to display.
                    <div style={{
                      width: '100%', aspectRatio: '2 / 3', borderRadius: 4, background: 'var(--bg-panel)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden',
                    }}>
                      <img src="/icons/mystery_encounter.png" alt="" draggable={false}
                        style={{ width: '55%', height: '55%', objectFit: 'contain', opacity: 0.35, filter: 'grayscale(1)' }} />
                    </div>
                  )}
                </CardFrame>
                <div style={{ fontSize: '0.72rem', marginTop: '0.3rem', color: isMvp ? 'var(--star5)' : undefined }}>{h.name}</div>
                {status !== 'alive' && status !== 'unknown' && (
                  <div className={status === 'injured' ? 'text-red' : 'text-dim'} style={{ fontSize: '0.62rem' }}>{STATUS_LABEL[status]}</div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>

        {/* Combat Metrics */}
        <div className="card">
          <div className="section-header">Combat Metrics</div>
          <div className="text-dim text-sm" style={{ marginBottom: '1rem' }}>Damage Dealt</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {combatEntities?.heroes?.map(h => {
              const dmg = metrics[h.id] || 0;
              const pct = (dmg / maxDmg) * 100;
              const isMvp = dmg > 0 && String(h.id) === String(mvpId)
              return (
                <div key={h.id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                    <span>{isMvp && '🏆 '}{h.name}{isMvp && <span className="text-gold" style={{ fontSize: '0.7rem', marginLeft: '0.4rem' }}>MVP</span>}</span>
                    <span className="text-gold">{dmg.toLocaleString()}</span>
                  </div>
                  <div style={{ height: '8px', background: '#222', borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: isMvp ? 'var(--star5)' : 'var(--gold)', transition: 'width 1s ease-out', boxShadow: isMvp ? '0 0 8px var(--star5)' : 'none' }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Loot and Rewards */}
        <div className="card">
          <div className="section-header">Loot & Rewards</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

            {lastResult.gold_gained > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: 6 }}>
                <span>Gold Found</span>
                <span className="text-gold" style={{ fontFamily: 'Cinzel, serif' }}>+{lastResult.gold_gained.toLocaleString()}g</span>
              </div>
            )}

            {lastResult.gems_gained > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: 'rgba(0,255,255,0.08)', border: '1px solid rgba(0,255,255,0.3)', borderRadius: 6 }}>
                <span>New Floor Record!</span>
                <span style={{ color: '#00ffff', fontFamily: 'Cinzel, serif', textShadow: '0 0 5px rgba(0,255,255,0.5)' }}>+{lastResult.gems_gained.toLocaleString()} <GameIcon name="gem" size={16} /></span>
              </div>
            )}

            {lastResult.ingredients_gained > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: 6 }}>
                <span>Ingredients Foraged</span>
                <span style={{ color: 'var(--text-hi)', fontFamily: 'Cinzel, serif' }}>+{lastResult.ingredients_gained.toLocaleString()}</span>
              </div>
            )}
            
            {lastResult.materials_gained && Object.keys(lastResult.materials_gained).length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', padding: '0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: 6 }}>
                <span>Materials Found</span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                  {Object.entries(lastResult.materials_gained).map(([mat, qty]) => (
                    <div key={mat} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                      <span className="text-dim">{mat}</span>
                      <span style={{ color: 'var(--text-hi)', fontFamily: 'Cinzel, serif' }}>+{qty}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {lastResult.equipment_drop && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', background: 'rgba(74,154,106,0.1)', border: '1px solid var(--green)', borderRadius: 6 }}>
                <span style={{ color: 'var(--green)' }}>Equipment Dropped</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <EquipmentTypeIcon item={lastResult.equipment_drop} fontSize="1.4rem" glow="var(--green)" />
                  {lastResult.equipment_drop.name} ({lastResult.equipment_drop.rarity})
                </span>
              </div>
            )}

            {lastResult.blueprint_found && (
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: 'rgba(201,168,76,0.1)', border: '1px solid var(--gold)', borderRadius: 6 }}>
                <span className="text-gold"><GameIcon name="scroll" size={16} /> Blueprint Found</span>
                <span>{lastResult.blueprint_found}</span>
              </div>
            )}

            {lastResult.combat?.skill_upgrades && Object.entries(lastResult.combat.skill_upgrades).map(([hid, ups]) => (
              ups.map((u, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: 'rgba(157,78,221,0.1)', border: '1px solid #9d4edd', borderRadius: 6 }}>
                  <span style={{ color: '#e0aaff' }}>Skill Ascended</span>
                  <span>{u.skill_name} ➔ {u.new_tier}</span>
                </div>
              ))
            ))}

            {lastResult.level_ups && lastResult.level_ups.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', padding: '0.75rem', background: 'rgba(201,168,76,0.1)', border: '1px solid var(--gold)', borderRadius: 6 }}>
                <span className="text-gold" style={{ fontFamily: 'Cinzel, serif' }}>⬆ Level Up</span>
                {lastResult.level_ups.map((msg, i) => (
                  <div key={i} style={{ fontSize: '0.85rem', color: msg.startsWith('  ') ? 'var(--star5)' : 'var(--text-hi)' }}>{msg}</div>
                ))}
              </div>
            )}

            {(!lastResult.gold_gained && !lastResult.gems_gained && !lastResult.equipment_drop && !lastResult.blueprint_found && !lastResult.combat?.skill_upgrades && !lastResult.ingredients_gained && !(lastResult.level_ups && lastResult.level_ups.length > 0) && !(lastResult.materials_gained && Object.keys(lastResult.materials_gained).length > 0)) && (
               <div className="text-dim text-center" style={{ padding: '2rem' }}>No loot found.</div>
            )}

          </div>
        </div>
      </div>
      
      {/* Victory / Defeat / Continue Block */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}>
         <div style={{
           padding: '1rem', width: '100%', borderRadius: 6,
           background: wasVictory ? 'rgba(201,168,76,0.1)' : 'rgba(192,64,64,0.1)',
           border: `1px solid ${wasVictory ? 'var(--gold)' : '#c44'}`
         }}>
           <div style={{
             fontSize: '1.5rem', fontFamily: 'Cinzel, serif', textAlign: 'center', letterSpacing: '2px',
             color: wasVictory ? 'var(--gold)' : '#e66'
           }}>
             {wasVictory ? 'Victory!' : 'Defeat...'}
           </div>
         </div>
         <div style={{ display: 'flex', gap: '1rem', width: '100%' }}>
           <button className="btn" onClick={onRerun} disabled={busy} style={{ flex: 1, padding: '1rem', fontSize: '1.1rem', letterSpacing: '1px' }}>
             Rerun Floor
           </button>
           <button className="btn btn-primary" onClick={onReturn} disabled={busy} style={{ flex: 1, padding: '1rem', fontSize: '1.1rem', letterSpacing: '1px' }}>
             {continueLabel}
           </button>
         </div>
      </div>

    </div>
  )
}

export default function TowerPage({ onGoldChange }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [team, setTeam] = useState({})
  const [base, setBase] = useState(null)
  const [highestFloor, setHighestFloor] = useState(0)

  // GUI State
  const [selectedZone, setSelectedZone] = useState(0)
  const [selectedFloor, setSelectedFloor] = useState(1)
  const [resolvedFloor, setResolvedFloor] = useState(null)
  const [deployTeamIds, setDeployTeamIds] = useState([1, 2, 3, 4, 5])

  // Combat/Event State
  const [advancing, setAdvancing] = useState(false)
  const [lastResult, setLastResult] = useState(null)
  const [pendingEvent, setPendingEvent] = useState(null)
  const [resolving, setResolving] = useState(false)
  const [eventResolution, setEventResolution] = useState(null)
  const [pendingExplore, setPendingExplore] = useState(null)
  const [exploreResolution, setExploreResolution] = useState(null)

  // The manager's standing tactical directive — applies to every regular
  // combat floor automatically (Boss/Miniboss ignore it, see backend). The
  // one persistent lever the player gets since they can't dictate the fight
  // itself once the team's deployed.
  const [stance, setStance] = useState(localStorage.getItem('tower_stance') || 'balanced')
  function changeStance(s) {
    setStance(s)
    localStorage.setItem('tower_stance', s)
  }
  
  const [combatEntities, setCombatEntities] = useState(null)
  const [postCombatPhase, setPostCombatPhase] = useState(false)
  const [arenasFinished, setArenasFinished] = useState(0)
  // When a real fight starts animating, we stash it here so leaving the
  // Tower tab (which unmounts this whole page — the app renders exactly
  // one tab's component at a time) and coming back doesn't just lose the
  // fight. On remount we restore it and fast-forward the animation by
  // exactly how long the player was gone, instead of replaying from turn 1.
  const [resumeTurnIndex, setResumeTurnIndex] = useState(-1)
  // Indexed by team/arena position — one AI-narrated line per turn, swapped
  // in for the raw damage-number log line once it arrives (see pollTurnNarrative).
  const [turnNarrations, setTurnNarrations] = useState({})
  const [floorPreview, setFloorPreview] = useState(null)
  const [zoneFloorTypes, setZoneFloorTypes] = useState({})

  useEffect(() => {
    refresh()
    // Resume an in-progress fight left running when this tab was last torn
    // down (see saveActiveCombat). Compute how many turns "should have
    // played" from real elapsed time and fast-forward CombatArena to it.
    const active = loadActiveCombat()
    if (active) {
      const speedMult = localStorage.getItem('combatSpeed2x') === '1' ? 2 : 1
      const elapsedTurns = Math.floor((Date.now() - active.deployedAt) / (TURN_DELAY_MS / speedMult))
      setLastResult(active.result)
      setResolvedFloor(active.resolvedFloor)
      setCombatEntities(mergedCombatEntities(active.result))
      setResumeTurnIndex(elapsedTurns)
    }
  }, [])

  useEffect(() => {
    if (lastResult) return
    if (selectedFloor <= highestFloor) {
      setFloorPreview(null)
      return
    }
    let cancelled = false
    previewFloor(selectedFloor).then(p => { if (!cancelled) setFloorPreview(p) }).catch(() => {})
    return () => { cancelled = true }
  }, [selectedFloor, highestFloor, lastResult])

  // Floor type is deterministic/cached server-side per floor number, so
  // previewing the whole zone's grid up front (not just the one selected
  // floor) is safe — it never changes the outcome, just lets the grid
  // show each tile's real type instead of being blank/generic. Extracted
  // into a callable so it can also be re-run the instant a fight finishes
  // (a just-cleared floor's tile flips from "?" to its revealed type
  // without waiting for the player to switch zones and back).
  async function refreshZoneFloorTypes(zoneIndex = selectedZone) {
    const start = zoneIndex * 10 + 1
    const floors = Array.from({ length: 10 }, (_, i) => start + i)
    const results = await Promise.all(
      floors.map(f => previewFloor(f).then(p => [f, p]).catch(() => [f, null]))
    )
    setZoneFloorTypes(prev => {
      const next = { ...prev }
      for (const [f, p] of results) if (p) next[f] = p
      return next
    })
  }

  useEffect(() => {
    let cancelled = false
    refreshZoneFloorTypes(selectedZone).catch(() => {})
    return () => { cancelled = true }
  }, [selectedZone])

  useEffect(() => {
    // Silently sync highest_floor to the Arena server if logged in
    if (highestFloor > 0 && getArenaToken()) {
      arenaUpdateFloor(highestFloor).catch(() => {})
    }
  }, [highestFloor])

  async function refresh() {
    setLoading(true)
    try {
      const [teamsData, baseData] = await Promise.all([getAllTeams(), getBase()]);
      setHighestFloor(baseData.highest_floor || 0);
      setTeam(teamsData)
      setBase(baseData)
      
      if (!lastResult && baseData.highest_floor > 0) {
        const nextFloor = baseData.highest_floor + 1
        setSelectedFloor(nextFloor)
        setSelectedZone(Math.floor((nextFloor - 1) / 10))
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  function pollNarrative(narrativeId, attemptsLeft = 4) {
    if (!narrativeId || attemptsLeft <= 0) return
    setTimeout(async () => {
      try {
        const res = await getNarrative(narrativeId)
        if (res.ready && res.narrative) {
          setLastResult(prev => prev ? { ...prev, narrative: res.narrative } : prev)
        } else {
          pollNarrative(narrativeId, attemptsLeft - 1)
        }
      } catch {
        // Flavor text only — silently give up on failure.
      }
    }, 2000)
  }

  // Polls more frequently/eagerly than pollNarrative — combat plays out at
  // 800ms/turn, so the per-turn narration array needs to land mid-fight to
  // be useful, not after the player's already watched the whole thing play
  // out with raw damage-number lines.
  function pollTurnNarrative(narrativeId, arenaIndex, attemptsLeft = 6) {
    if (narrativeId == null || attemptsLeft <= 0) return
    setTimeout(async () => {
      try {
        const res = await getNarrative(narrativeId)
        if (res.ready && Array.isArray(res.narrative)) {
          setTurnNarrations(prev => ({ ...prev, [arenaIndex]: res.narrative }))
        } else if (!res.ready) {
          pollTurnNarrative(narrativeId, arenaIndex, attemptsLeft - 1)
        }
      } catch {
        // Flavor text only — silently give up on failure.
      }
    }, 1000)
  }

  async function enterFloorFlow(floorNumber, { skipAnimation = false } = {}) {
    setAdvancing(true)
    setError(null)
    setEventResolution(null)
    setPendingEvent(null)
    setExploreResolution(null)
    setPendingExplore(null)
    setLastResult(null)
    setResolvedFloor(floorNumber)
    setCombatEntities(null)
    setPostCombatPhase(false)
    setArenasFinished(0)
    setTurnNarrations({})
    setResumeTurnIndex(-1)
    clearActiveCombat()

    try {
      const requiredTeams = (floorNumber - 1) === 0 ? 1 : Math.floor((floorNumber - 1) / 20) + 1
      const result = await enterFloor(floorNumber, deployTeamIds.slice(0, requiredTeams), stance)
      setLastResult(result)
      setCombatEntities(mergedCombatEntities(result))
      if (result.narrative_id) pollNarrative(result.narrative_id)
      const tnIds = result.turn_narrative_ids || (result.turn_narrative_id != null ? [result.turn_narrative_id] : [])
      tnIds.forEach((id, i) => pollTurnNarrative(id, i))

      if (result.awaiting_choice && result.event) {
        setPendingEvent(result)
      } else if (result.awaiting_choice && result.explore) {
        setPendingExplore(result)
      } else if (skipAnimation) {
        // Already seen this floor — jump straight to the resolution screen
        // instead of replaying the full combat animation.
        setPostCombatPhase(true)
      } else {
        // A real animation is about to play — save it so leaving and
        // returning to this tab can resume instead of losing it.
        saveActiveCombat(result, floorNumber)
      }

      await refresh()
      refreshZoneFloorTypes().catch(() => {})
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setError(e.message)
    } finally {
      setAdvancing(false)
    }
  }

  function handleEnterFloor() {
    return enterFloorFlow(selectedFloor)
  }

  function handleSkipFloor() {
    return enterFloorFlow(selectedFloor, { skipAnimation: true })
  }

  function handleRerun() {
    return enterFloorFlow(resolvedFloor || selectedFloor, { skipAnimation: true })
  }

  function handleExit() {
    clearActiveCombat()
    setLastResult(null)
    setEventResolution(null)
    setExploreResolution(null)
    setPendingEvent(null)
    setPendingExplore(null)
    setAllLogs([])
    setPostCombatPhase(false)
  }

  async function handleEventChoice(choiceId) {
    setResolving(true)
    setError(null)
    try {
      const result = await resolveEvent(resolvedFloor || selectedFloor, deployTeamIds[0], pendingEvent.event.template_id, choiceId, pendingEvent.theme)
      setPendingEvent(null)
      setEventResolution(result)

      if (result.combat) {
        // The choice turned hostile — route through the same animated
        // combat arena as a normal/Explore floor instead of jumping
        // straight to the static narrative-only result box.
        setLastResult(result)
        setArenasFinished(0)
        setTurnNarrations({})
        setResumeTurnIndex(-1)
        setCombatEntities(mergedCombatEntities(result))
        saveActiveCombat(result, resolvedFloor || selectedFloor)
        const tnIds = result.turn_narrative_ids || (result.turn_narrative_id != null ? [result.turn_narrative_id] : [])
        tnIds.forEach((id, i) => pollTurnNarrative(id, i))
      } else {
        setPostCombatPhase(true)
      }

      await refresh()
      refreshZoneFloorTypes().catch(() => {})
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setError(e.message)
    } finally {
      setResolving(false)
    }
  }

  async function handleExploreChoice(choiceId) {
    setResolving(true)
    setError(null)
    try {
      const result = await resolveExplore(resolvedFloor || selectedFloor, deployTeamIds[0], choiceId)
      // Explore always ends in a real fight now — route through the same
      // combat animation as a normal floor, instead of jumping straight to
      // a static result box.
      setExploreResolution(result)
      setLastResult(result)
      setArenasFinished(0)
      setTurnNarrations({})
      setResumeTurnIndex(-1)
      setCombatEntities(mergedCombatEntities(result))
      setPendingExplore(null)
      saveActiveCombat(result, resolvedFloor || selectedFloor)
      const tnIds = result.turn_narrative_ids || (result.turn_narrative_id != null ? [result.turn_narrative_id] : [])
      tnIds.forEach((id, i) => pollTurnNarrative(id, i))

      await refresh()
      refreshZoneFloorTypes().catch(() => {})
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setError(e.message)
    } finally {
      setResolving(false)
    }
  }

  if (loading) return <div className="page text-dim">Loading...</div>

  const maxZone = Math.floor(highestFloor / 10)
  const startFloorOfZone = selectedZone * 10 + 1

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div className="section-header" style={{ marginBottom: 0 }}>The Tower</div>
      </div>

      {lastResult ? (
        <div>
          {/* Centered Resolution Header */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div className="text-dim text-sm" style={{ letterSpacing: 2, textTransform: 'uppercase' }}>Resolution</div>
            <div style={{ fontFamily: 'Cinzel, serif', fontSize: '3rem', color: 'var(--gold)', textShadow: '0 2px 10px rgba(201,168,76,0.3)' }}>
              Floor {resolvedFloor}
            </div>
          </div>

          {lastResult && <FloorTypeCallout type={lastResult.floor_type} isSurvivalSwarm={
            (lastResult.combat?.team_results || lastResult.team_results || []).some(tr => tr?.initial_state?.is_survival_swarm)
            || lastResult.combat?.initial_state?.is_survival_swarm
            || lastResult.initial_state?.is_survival_swarm
          } />}

          {postCombatPhase && lastResult.run_over && (
            <div className="text-red" style={{ maxWidth: '600px', margin: '0 auto 2rem auto', textAlign: 'center', padding: '1rem', background: 'rgba(192,64,64,0.1)', border: '1px solid #c44', borderRadius: 6 }}>
              ✦ The team was defeated and forced to retreat.
            </div>
          )}

          {error && <div className="text-red text-center" style={{ marginBottom: '1rem' }}>{error}</div>}

          {/* Event UI (Interrupts combat flow if awaiting choice) */}
          {pendingEvent && !postCombatPhase && (
            <div className="card" style={{ maxWidth: '600px', margin: '0 auto 2rem auto', border: '1px solid var(--gold)' }}>
              <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', fontSize: '1.2rem', marginBottom: '1rem', textAlign: 'center' }}>
                Event
              </div>
              <div style={{ marginBottom: '1.5rem', lineHeight: 1.6, color: 'var(--text-hi)', fontSize: '1.05rem', textAlign: 'center' }}>
                {pendingEvent.event_narrative || pendingEvent.event.theme}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {pendingEvent.event.choices.map(choice => (
                  <button 
                    key={choice.id}
                    className="btn"
                    onClick={() => handleEventChoice(choice.id)}
                    disabled={resolving}
                    style={{
                      textAlign: 'center',
                      padding: '1rem',
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      fontSize: '1rem',
                      userSelect: 'none',
                      WebkitUserSelect: 'none',
                    }}
                    onMouseOver={e => {
                      if (!resolving) e.currentTarget.style.background = 'rgba(255,255,255,0.1)'
                    }}
                    onMouseOut={e => {
                      if (!resolving) e.currentTarget.style.background = 'rgba(0,0,0,0.3)'
                    }}
                  >
                    <div style={{ color: 'var(--text-hi)' }}>
                      {choice.label || choice.text || `Choice ${choice.id}`}
                    </div>
                    {choice.hint && (
                      <div className="text-dim" style={{ fontSize: '0.8rem', marginTop: '0.3rem', fontStyle: 'italic' }}>
                        {choice.hint}
                      </div>
                    )}
                  </button>
                ))}
              </div>

              {resolving && (
                <div className="text-dim text-center" style={{ marginTop: '1rem' }}>
                  Resolving...
                </div>
              )}
              <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                <button className="btn" onClick={handleExit} disabled={resolving} style={{ padding: '0.5rem 1.5rem', fontSize: '0.9rem' }}>
                  Exit
                </button>
              </div>
            </div>
          )}

          {/* Explore UI (Interrupts combat flow if awaiting choice) */}
          {pendingExplore && !postCombatPhase && (
            <div className="card" style={{ maxWidth: '600px', margin: '0 auto 2rem auto', border: '1px solid var(--green)' }}>
              <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--green)', fontSize: '1.2rem', marginBottom: '1rem', textAlign: 'center' }}>
                Explore
              </div>
              <div style={{ marginBottom: '1.5rem', lineHeight: 1.6, color: 'var(--text-hi)', fontSize: '1.05rem', textAlign: 'center' }}>
                {pendingExplore.explore.theme}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {pendingExplore.explore.choices.map(choice => (
                  <button
                    key={choice.id}
                    className="btn"
                    onClick={() => handleExploreChoice(choice.id)}
                    disabled={resolving}
                    style={{
                      textAlign: 'center',
                      padding: '1rem',
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      fontSize: '1rem',
                      userSelect: 'none',
                      WebkitUserSelect: 'none',
                    }}
                    onMouseOver={e => {
                      if (!resolving) e.currentTarget.style.background = 'rgba(255,255,255,0.1)'
                    }}
                    onMouseOut={e => {
                      if (!resolving) e.currentTarget.style.background = 'rgba(0,0,0,0.3)'
                    }}
                  >
                    <div style={{ color: 'var(--text-hi)' }}>
                      {choice.label}
                    </div>
                    {choice.hint && (
                      <div className="text-dim" style={{ fontSize: '0.8rem', marginTop: '0.3rem', fontStyle: 'italic' }}>
                        {choice.hint}
                      </div>
                    )}
                  </button>
                ))}
              </div>

              {resolving && (
                <div className="text-dim text-center" style={{ marginTop: '1rem' }}>
                  Resolving...
                </div>
              )}
              <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                <button className="btn" onClick={handleExit} disabled={resolving} style={{ padding: '0.5rem 1.5rem', fontSize: '0.9rem' }}>
                  Exit
                </button>
              </div>
            </div>
          )}

          {/* Battlefield UI */}
          {!postCombatPhase && !pendingEvent && !pendingExplore && (
            <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
              {lastResult && !lastResult.awaiting_choice && (() => {
                const teamResults = (lastResult?.combat?.team_results || lastResult?.team_results || []).filter(Boolean)
                if (teamResults.length > 1) {
                  const onArenaComplete = () => {
                    setArenasFinished(prev => {
                      const next = prev + 1
                      if (next >= teamResults.length) {
                        clearActiveCombat()
                        setPostCombatPhase(true)
                      }
                      return next
                    })
                  }
                  return (
                    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                      {teamResults.map((tr, i) => (
                        <div key={i} style={{ flex: '1 1 480px', minWidth: '420px' }}>
                          <div style={{ textAlign: 'center', color: 'var(--text-hi)', fontFamily: 'Cinzel, serif', marginBottom: '0.3rem' }}>
                            Team {i + 1}
                          </div>
                          <CombatArena combatData={tr} onComplete={onArenaComplete} turnNarrations={turnNarrations[i]} />
                        </div>
                      ))}
                    </div>
                  )
                }
                return (
                  <CombatArena
                    combatData={lastResult?.combat || lastResult}
                    onComplete={() => { clearActiveCombat(); setPostCombatPhase(true) }}
                    turnNarrations={turnNarrations[0]}
                    initialTurnIndex={resumeTurnIndex}
                  />
                )
              })()}
              <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                <button className="btn" onClick={handleExit} style={{ padding: '0.5rem 1.5rem', fontSize: '0.9rem' }}>
                  Exit
                </button>
              </div>
            </div>
          )}

          {/* Post Combat Screens */}
          {postCombatPhase && (
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
              <PostCombatScreen
                lastResult={lastResult}
                combatEntities={combatEntities}
                onReturn={handleExit}
                onRerun={handleRerun}
                busy={advancing}
              />

              {eventResolution && (
                <div className="card" style={{
                  marginTop: '2rem',
                  border: '1px solid var(--green)',
                  background: 'rgba(74,154,106,0.08)',
                  textAlign: 'center'
                }}>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--green)', marginBottom: '0.5rem' }}>
                    {eventResolution.choice_label || 'Event Resolved'}
                  </div>
                  <div style={{ lineHeight: 1.6, fontSize: '1.05rem' }}>
                    {eventResolution.event_narrative || eventResolution.narrative}
                  </div>
                  {eventResolution.effects?.trait && (
                    <div style={{ marginTop: '1rem', padding: '0.6rem 1rem', border: '1px solid var(--gold)', borderRadius: 6, background: 'rgba(201,168,76,0.08)', display: 'inline-block' }}>
                      <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', fontSize: '0.95rem' }}>
                        ✦ New Trait: {eventResolution.effects.trait.name}
                      </div>
                      <div className="text-dim" style={{ fontSize: '0.8rem', marginTop: '0.2rem' }}>
                        {eventResolution.effects.trait.desc}
                      </div>
                    </div>
                  )}
                  {eventResolution.effects?.gems > 0 && (
                    <div style={{ marginTop: '1rem', fontSize: '1.1rem', color: '#00ffff' }}>
                      +{eventResolution.effects.gems} <GameIcon name="gem" size={16} />
                    </div>
                  )}
                  {eventResolution.effects?.gold > 0 && (
                    <div className="text-gold" style={{ marginTop: '0.5rem', fontSize: '1.1rem' }}>
                      +{eventResolution.effects.gold}g
                    </div>
                  )}
                </div>
              )}

              {exploreResolution?.explore_loot && (
                <div className="card" style={{
                  marginTop: '2rem',
                  border: '1px solid var(--green)',
                  background: 'rgba(74,154,106,0.08)',
                  textAlign: 'center'
                }}>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--green)', marginBottom: '0.5rem' }}>
                    Exploration Bonus
                  </div>
                  <div style={{ lineHeight: 1.6, fontSize: '1.05rem' }}>
                    {exploreResolution.explore_loot.summary}
                  </div>
                  {exploreResolution.explore_loot.loot?.desc && (
                    <div className="text-gold" style={{ marginTop: '1rem', fontSize: '1.1rem' }}>
                      {exploreResolution.explore_loot.loot.desc}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '2rem', alignItems: 'start' }}>
          {/* Floor Grid — the tower itself looms faintly behind the floor map.
              Fills the remaining viewport height so the art reads at full
              size on big screens instead of leaving a black void below. */}
          <div className="card" style={{
            backgroundImage: `linear-gradient(rgba(12,12,16,0.82), rgba(10,10,12,0.94)), url(/images/floors/${zoneFor(selectedZone).slug}.png)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center 25%',
            minHeight: 'calc(100vh - 265px)',
            display: 'flex',
            flexDirection: 'column',
            transition: 'background-image 0.4s ease',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.2rem' }}>
              <div>
                <div style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.5rem', marginLeft: '-0.5rem' }}>
                  {Array.from({ length: maxZone + 1 }).map((_, z) => (
                    <button
                      key={z}
                      className={`btn ${selectedZone === z ? 'btn-gold' : ''}`}
                      onClick={() => setSelectedZone(z)}
                      style={{ minWidth: '70px', padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
                    >
                      Zone {z + 1}
                    </button>
                  ))}
                </div>
                <div style={{ marginTop: '0.35rem' }}>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.4rem', color: 'var(--gold)', textShadow: '0 2px 8px rgba(0,0,0,0.8)' }}>
                    {zoneFor(selectedZone).name}
                  </div>
                  <div className="text-dim" style={{ fontSize: '0.82rem', maxWidth: 520, textShadow: '0 1px 4px rgba(0,0,0,0.9)' }}>
                    {zoneFor(selectedZone).blurb}
                  </div>
                  <div className="text-dim" style={{ fontSize: '0.8rem', marginTop: '0.15rem' }}>
                    Highest floor reached: <span style={{ color: 'var(--text-hi)' }}>{highestFloor}</span>
                  </div>
                </div>
              </div>
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
              gap: '1rem'
            }}>
              {Array.from({ length: 10 }).map((_, i) => {
                const floorNum = startFloorOfZone + i
                const isLocked = floorNum > highestFloor + 1
                const isNext = floorNum === highestFloor + 1
                const isSelected = floorNum === selectedFloor
                const isBoss = floorNum % 10 === 0
                const preview = zoneFloorTypes[floorNum]
                // Only reveal floor type/colour once the player has actually entered it
                const visited = preview?.visited
                const typeInfo = visited ? FLOOR_TYPE_INFO[preview.floor_type] : null

                let bg = 'rgba(255,255,255,0.05)'
                let border = '1px solid rgba(255,255,255,0.12)'
                let color = 'var(--text-hi)'
                const extraClass = isNext ? ' floor-tile-next' : ''

                if (isLocked) {
                  bg = 'rgba(0,0,0,0.35)'
                  color = 'var(--text-dim)'
                }
                if (isNext) {
                  border = '1px solid var(--gold)'
                }
                if (isSelected) {
                  bg = 'rgba(201, 168, 76, 0.25)'
                  border = '2px solid var(--gold)'
                }
                if (isBoss) {
                  border = isSelected ? '2px solid var(--gold)' : '1px solid rgba(227,51,51,0.6)'
                }

                return (
                  <button
                    key={floorNum}
                    disabled={isLocked}
                    onClick={() => setSelectedFloor(floorNum)}
                    className={`floor-tile${extraClass}`}
                    title={typeInfo ? typeInfo.label : (isLocked ? 'Locked' : 'Unknown')}
                    style={{
                      background: bg,
                      border,
                      color,
                      cursor: isLocked ? 'not-allowed' : 'pointer',
                      opacity: isLocked ? 0.6 : 1,
                      padding: '1rem 0.5rem',
                      minHeight: '90px',
                    }}
                  >
                    {isBoss && <div className="floor-tile-boss-stripe" />}
                    <div className="floor-tile-num" style={{ fontSize: '3.2rem', fontWeight: 600 }}>{floorNum}</div>
                    {isNext && <span className="floor-tile-tag" style={{ background: 'rgba(201,168,76,0.3)', color: 'var(--gold)' }}>Next</span>}
                    {!isLocked && !isNext && <span className="floor-tile-tag" style={{ background: 'rgba(80,200,120,0.2)', color: 'var(--green)' }}>
                      ✓ {typeInfo ? typeInfo.label : 'Cleared'}
                    </span>}
                  </button>
                )
              })}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '1.5rem' }}>
              <button
                className="btn"
                disabled={selectedZone === 0}
                onClick={() => setSelectedZone(z => z - 1)}
              >
                ← Prev Zone
              </button>
              <button
                className="btn"
                disabled={selectedZone >= maxZone}
                onClick={() => setSelectedZone(z => z + 1)}
              >
                Next Zone →
              </button>
            </div>
          </div>

          {/* Deploy Panel */}
          <div className="card">
            <div className="text-gold" style={{ fontFamily: 'Cinzel, serif', marginBottom: '1rem', fontSize: '1.1rem' }}>
              Deploy
            </div>
            
            {Array.from({length: selectedFloor === 1 ? 1 : Math.floor((selectedFloor - 1) / 20) + 1}).map((_, idx) => (
              <div key={idx} style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                <label className="text-dim text-sm" style={{ display: 'block', marginBottom: '0.5rem' }}>Select Team {idx + 1}</label>
                <select 
                  value={deployTeamIds[idx]}
                  onChange={e => {
                    const newIds = [...deployTeamIds]
                    newIds[idx] = parseInt(e.target.value)
                    setDeployTeamIds(newIds)
                  }}
                  style={{ width: '100%', background: 'var(--bg)', color: '#fff', border: '1px solid var(--border)', padding: '0.6rem 0.8rem', borderRadius: 4, fontFamily: 'inherit', fontSize: '0.9rem', marginBottom: '0.5rem' }}
                >
                  {[1,2,3,4,5,6,7,8,9,10].map(id => {
                    const count = team[id.toString()] ? team[id.toString()].length : 0
                    return <option key={id} value={id}>Team {id} ({count}/5)</option>
                  })}
                </select>
                
                {team[deployTeamIds[idx].toString()] && team[deployTeamIds[idx].toString()].length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                    {team[deployTeamIds[idx].toString()].map(h => (
                      <div key={h.id} style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(0,0,0,0.2)', padding: '0.3rem', borderRadius: 4 }}>
                        <span style={{ fontFamily: 'Cinzel, serif', fontSize: '0.8rem' }}>{h.name}</span>
                        <span className="text-dim" style={{ fontSize: '0.7rem' }}>Lv.{h.level}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>
                    No heroes assigned to Team {deployTeamIds[idx]}.
                  </div>
                )}
              </div>
            ))}

            <div style={{ marginBottom: '1rem' }}>
              <label className="text-dim text-sm" style={{ display: 'block', marginBottom: '0.5rem' }}>Tactical Stance</label>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                {[
                  { id: 'cautious', label: 'Cautious', title: 'Safer fights, smaller rewards (-10% loot, -15% enemy difficulty)' },
                  { id: 'balanced', label: 'Balanced', title: 'No adjustment — the default.' },
                  { id: 'aggressive', label: 'Aggressive', title: 'Tougher enemies, bigger rewards (+20% loot, +15% enemy difficulty)' },
                ].map(opt => (
                  <button
                    key={opt.id}
                    className="btn"
                    title={opt.title}
                    onClick={() => changeStance(opt.id)}
                    style={{
                      flex: 1, fontSize: '0.75rem', padding: '0.4rem 0.3rem',
                      background: stance === opt.id ? 'rgba(201,168,76,0.25)' : 'rgba(0,0,0,0.3)',
                      borderColor: stance === opt.id ? 'var(--gold)' : 'var(--border)',
                      color: stance === opt.id ? 'var(--gold)' : '#ddd',
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              <div className="text-dim" style={{ fontSize: '0.65rem', marginTop: '0.3rem', fontStyle: 'italic' }}>
                Doesn't apply to Boss/Miniboss floors — those are a fixed gear check either way.
              </div>
            </div>

            {floorPreview?.blurb && (
              <div style={{
                marginBottom: '1rem',
                padding: '0.6rem 0.8rem',
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 6,
                fontSize: '0.85rem',
                fontStyle: 'italic',
                color: 'var(--text-hi)',
              }}>
                {floorPreview.blurb}
              </div>
            )}


            {error && <div className="text-red text-sm" style={{ marginBottom: '1rem' }}>{error}</div>}

            <div style={{ display: 'flex', gap: '0.6rem' }}>
              <button
                className="btn btn-primary"
                style={{ flex: 1, padding: '1rem', fontSize: '1.1rem' }}
                onClick={handleEnterFloor}
                disabled={advancing || deployTeamIds.slice(0, selectedFloor === 1 ? 1 : Math.floor((selectedFloor - 1) / 20) + 1).some(id => !team[id.toString()] || team[id.toString()].length === 0)}
              >
                {advancing ? 'Entering...' : `Enter Floor ${selectedFloor}`}
              </button>
              {selectedFloor <= highestFloor && (
                <button
                  className="btn"
                  style={{ padding: '1rem 1.2rem', fontSize: '1.1rem' }}
                  onClick={handleSkipFloor}
                  disabled={advancing || deployTeamIds.slice(0, selectedFloor === 1 ? 1 : Math.floor((selectedFloor - 1) / 20) + 1).some(id => !team[id.toString()] || team[id.toString()].length === 0)}
                  title="Re-run this already-cleared floor instantly for XP and gold, no animation"
                >
                  Rush
                </button>
              )}
            </div>
          </div>
        </div>
      )}
      <FairyGuide floor={resolvedFloor || selectedFloor} lastResult={lastResult} fairyGender={base.fairy_gender} highestFloor={highestFloor} />
    </div>
  )
}
