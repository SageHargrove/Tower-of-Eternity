/*
 * Feature modals. Tournament Registration and Scout Report are LIVE against
 * the World/Arena server (arenaServerClient); both need an arena login.
 * Disconnected and Designate Runner remain static shells (the runner flow
 * belongs to retrieval floors, wired separately).
 */
import React, { useState, useEffect } from 'react'
import {
  arenaTournaments, arenaTournamentRegister,
  arenaRaidMap, arenaRaidScout, arenaRaidAttack, getArenaToken,
} from '../api/arenaServerClient'
import { getArenaSnapshot, getShip, raidPayScout, raidApplyAttackResult } from '../api/client'
import Pennant from './Pennant'
import StakesBanner from './StakesBanner'
import { emitToast } from '../toastBus'

function Scrim({ onClose, width = 520, children }) {
  return (
    <div className="ilm-modal-scrim" style={{ zIndex: 330 }} onClick={onClose}>
      <div className="ilm-featmodal" style={{ width, maxWidth: '94vw', maxHeight: '88vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
        <span className="ilm-corner" /><span className="ilm-corner ilm-corner-r" />
        <button className="ilm-close" style={{ position: 'absolute', top: 14, right: 14 }} onClick={onClose}>✕</button>
        {children}
      </div>
    </div>
  )
}

function NeedsLogin({ onClose, thing }) {
  return (
    <Scrim onClose={onClose} width={440}>
      <div className="ilm-micro" style={{ color: 'var(--red-hi)' }}>WORLD SERVER</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.5rem', color: 'var(--text-hi)', marginTop: 4 }}>NO THREAD TO THE WORLD</div>
      <div style={{ fontStyle: 'italic', color: '#c8b8dd', margin: '10px 0', lineHeight: 1.5 }}>
        {thing} lives on the World Server. Log in from the Arena screen first, then return here.
      </div>
    </Scrim>
  )
}

/* ── Tournament Registration ── */
const FMT_META = {
  duel: { size: '1 v 1', name: 'DUEL BRACKET', prize: '5 summon tickets + Duelist Crown' },
  pairs: { size: '2 v 2', name: 'PAIR BRACKET', prize: '5 summon tickets + Twin Banners' },
  warband: { size: '4 v 4', name: 'WARBAND BRACKET', prize: '5 summon tickets + Warband Standard' },
  royale: { size: 'FFA', name: 'BATTLE ROYALE', prize: '5 summon tickets + Last-One-Standing Cape' },
}
const PHASE_LABEL = {
  registration: 'REGISTRATION OPEN · BRACKETS FIGHT THURSDAY',
  battles: 'BATTLE PHASE — THE BRACKETS ARE FIGHTING',
  payouts: 'PAYOUT DAY — CHAMPIONS COLLECT AT THE MAILBOX',
}

function timeToLock() {
  // registration locks Thursday 00:00 UTC
  const now = new Date()
  const lock = new Date(now)
  lock.setUTCDate(now.getUTCDate() + ((4 - now.getUTCDay() + 7) % 7 || 7) - 1)
  lock.setUTCHours(24, 0, 0, 0)
  const s = Math.max(0, (lock - now) / 1000)
  return `${Math.floor(s / 86400)}D ${Math.floor((s % 86400) / 3600)}H`
}

export function TournamentRegistration({ onClose }) {
  const [status, setStatus] = useState(null)
  const [err, setErr] = useState(null)
  const [teamId, setTeamId] = useState(1)
  const [busy, setBusy] = useState(null)

  async function load() {
    try { setStatus(await arenaTournaments()); setErr(null) } catch (e) { setErr(e.message) }
  }
  useEffect(() => { load() }, [])

  if (!getArenaToken()) return <NeedsLogin onClose={onClose} thing="The Grand Tournament" />

  async function register(fmt, size) {
    setBusy(fmt)
    try {
      const snapshot = await getArenaSnapshot(teamId)
      const team = (snapshot.team || []).slice(0, size)
      if (team.length < size) throw new Error(`Team ${teamId} fields ${team.length} — this bracket needs ${size}.`)
      await arenaTournamentRegister(fmt, team)
      emitToast(`Registered for the ${FMT_META[fmt].name.toLowerCase()} — fights resolve Thursday.`, 'success')
      await load()
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  const phase = status?.phase
  return (
    <Scrim onClose={onClose} width={640}>
      <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>SERVER-WIDE{status ? ` · ${status.week}` : ''}</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.8rem', color: 'var(--text-hi)' }}>GRAND TOURNAMENT</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '8px 0 4px' }}>
        <span className="ilm-livedot" />
        <span className="ilm-micro" style={{ color: phase === 'registration' ? 'var(--red-hi)' : 'var(--gold-hi)' }}>
          {phase === 'registration' ? `REGISTRATION LOCKS IN ${timeToLock()}` : PHASE_LABEL[phase] || 'REACHING THE WORLD SERVER…'}
        </span>
      </div>
      <StakesBanner variant="echo" compact style={{ margin: '4px 0 10px' }} />
      {err && <div className="ilm-micro" style={{ color: 'var(--red-hi)', marginBottom: 10 }}>{err}</div>}

      {phase === 'registration' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span className="ilm-micro" style={{ color: 'var(--gold)' }}>ENTER WITH</span>
          {[1, 2, 3].map(t => (
            <button key={t} className={`ilm-btn ${teamId === t ? 'ilm-btn-gold' : 'ilm-btn-ghost'}`} style={{ padding: '4px 14px' }} onClick={() => setTeamId(t)}>
              TEAM {'I'.repeat(t)}
            </button>
          ))}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {Object.entries(FMT_META).map(([fmt, meta]) => {
          const f = status?.formats?.[fmt]
          return (
            <div key={fmt} className="ilm-feat-bracket">
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
                <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.1rem', color: 'var(--gold-hi)' }}>{meta.size}</span>
                <span className="ilm-micro">{meta.name}</span>
              </div>
              <div className="text-dim" style={{ fontSize: '0.82rem', margin: '6px 0' }}>
                {f ? `${f.entrants} entrant${f.entrants === 1 ? '' : 's'}` : '…'}
                {f?.resolved && f?.my_placement != null && <span style={{ color: 'var(--gold-hi)' }}> · placed #{f.my_placement} ({f.my_points} pts)</span>}
              </div>
              <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>PRIZE · {meta.prize}</div>
              {f?.registered
                ? <button className="ilm-btn ilm-btn-ghost ilm-btn-block" style={{ marginTop: 10 }} disabled>{phase === 'registration' ? 'REGISTERED · RE-ENTER TO SWAP' : 'ENTERED'}</button>
                : <button className="ilm-btn ilm-btn-gold ilm-btn-block" style={{ marginTop: 10 }} disabled={phase !== 'registration' || busy === fmt}
                    onClick={() => register(fmt, f?.team_size ?? { duel: 1, pairs: 2, warband: 4, royale: 5 }[fmt])}>
                    {busy === fmt ? 'REGISTERING…' : phase === 'registration' ? 'REGISTER' : 'REGISTRATION CLOSED'}
                  </button>}
              {f?.registered && phase === 'registration' && (
                <button className="ilm-btn ilm-btn-ghost ilm-btn-block" style={{ marginTop: 6 }} disabled={busy === fmt}
                  onClick={() => register(fmt, f?.team_size)}>SWAP IN TEAM {'I'.repeat(teamId)}</button>
              )}
            </div>
          )
        })}
      </div>
    </Scrim>
  )
}

/* ── Disconnected ── */
export function DisconnectedModal({ onClose }) {
  return (
    <Scrim onClose={onClose} width={440}>
      <div className="ilm-micro" style={{ color: 'var(--red-hi)' }}>ARENA · MATCH PAUSED</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.6rem', color: 'var(--text-hi)', marginTop: 4 }}>CONNECTION SEVERED</div>
      <div style={{ fontStyle: 'italic', color: '#c8b8dd', margin: '10px 0', lineHeight: 1.5 }}>The thread to the World Server has frayed. Your heroes hold their ground where they stand.</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '4px 0 14px' }}>
        <span className="ilm-livedot" style={{ background: 'var(--ember)', boxShadow: '0 0 7px var(--ember)' }} />
        <span className="ilm-micro" style={{ color: 'var(--ember)' }}>RE-BINDING THE THREAD…</span>
      </div>
      <div className="text-dim" style={{ fontSize: '0.78rem', fontStyle: 'italic', marginBottom: 14 }}>Auto-forfeit if the thread stays severed for 90 seconds.</div>
      <div style={{ display: 'flex', gap: 10 }}>
        <button className="ilm-btn ilm-btn-gold ilm-btn-block" onClick={onClose}>RECONNECT NOW</button>
        <button className="ilm-btn ilm-btn-danger" onClick={onClose}>ABANDON</button>
      </div>
      <div className="text-dim" style={{ fontSize: '0.74rem', fontStyle: 'italic', marginTop: 10 }}>Abandoning an arena match counts as a loss. No hero truly dies here.</div>
    </Scrim>
  )
}

/* ── Designate Runner (raid retrieval) ── */
const RUNNERS = [
  { name: 'VESPER', agi: 615, tag: 'FASTEST' },
  { name: 'LYRA', agi: 410 },
  { name: 'KYRIOS', agi: 302 },
  { name: 'SABLE', agi: 288 },
]
export function DesignateRunner({ onClose }) {
  return (
    <Scrim onClose={onClose} width={500}>
      <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>RETRIEVAL MISSION · FLOOR 47</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.6rem', color: 'var(--text-hi)', marginTop: 4 }}>DESIGNATE A RUNNER</div>
      <div style={{ fontStyle: 'italic', color: '#c8b8dd', margin: '8px 0', lineHeight: 1.5 }}>One hero must carry the relic out alone while the others hold the line.</div>
      <div style={{ display: 'flex', gap: 9, fontSize: '0.82rem', color: 'var(--red-hi)', fontStyle: 'italic', marginBottom: 14 }}>
        <span style={{ fontStyle: 'normal' }}>⚠</span><span>If the runner falls, the relic is lost with them — permanently.</span>
      </div>
      <div className="ilm-micro" style={{ color: 'var(--gold)', marginBottom: 8 }}>CHOOSE FROM TEAM ECHO</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {RUNNERS.map((r, i) => (
          <button key={r.name} className={`ilm-feat-runner ${i === 0 ? 'best' : ''}`}>
            <span className="ilm-guild-badge">{r.name[0]}</span>
            <span style={{ flex: 1, textAlign: 'left', fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.82rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{r.name}</span>
            <span className="ilm-micro" style={{ color: i === 0 ? 'var(--green-hi)' : 'var(--text-dim)' }}>AGI {r.agi}{r.tag ? ` · ${r.tag}` : ''}</span>
          </button>
        ))}
      </div>
    </Scrim>
  )
}

/* ── Scout Report (raid recon) — live ── */
const TIER_COLORS = ['var(--red-hi)', 'var(--ember)', 'var(--ember)', 'var(--gold-hi)', 'var(--green-hi)']

export function ScoutReport({ onClose, target: initialTarget = null }) {
  const [map, setMap] = useState(null)
  const [mapErr, setMapErr] = useState(null)
  const [target, setTarget] = useState(initialTarget)
  const [report, setReport] = useState(null)
  const [busy, setBusy] = useState(null)

  useEffect(() => {
    if (!getArenaToken()) return
    arenaRaidMap().then(setMap).catch(e => setMapErr(e.message))
  }, [])

  if (!getArenaToken()) return <NeedsLogin onClose={onClose} thing="Raid scouting" />

  async function scout(name, currency = 'gold') {
    setBusy('scout')
    try {
      const paid = await raidPayScout(currency)   // local fee, returns recon rating
      const rep = await arenaRaidScout(name, paid.scout_power?.total ?? 0)
      setTarget(name)
      setReport(rep)
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  async function launchRaid() {
    setBusy('raid')
    try {
      const [snapshot, ship] = await Promise.all([getArenaSnapshot(1), getShip().catch(() => null)])
      const res = await arenaRaidAttack(target, snapshot.team, ship?.tier ?? 0)
      const won = !!res.attacker_won
      const spoils = res.spoils || {}
      await raidApplyAttackResult(won, spoils.gold || 0, spoils.ingredients || 0).catch(() => {})
      emitToast(won
        ? `The siege of ${target} succeeds — ${(spoils.gold || 0).toLocaleString()}g seized.`
        : `${target}'s defenders hold. The siege is repelled.`, won ? 'success' : 'error')
      onClose()
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  /* target picker */
  if (!report) {
    return (
      <Scrim onClose={onClose} width={520}>
        <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>RAID RECON</div>
        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.6rem', color: 'var(--text-hi)', marginTop: 4 }}>SHAPES ON THE HORIZON</div>
        <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', margin: '8px 0 14px', lineHeight: 1.5 }}>
          Bases within scouting range. Sending scouts costs gold — what they see depends on your recon against their wards.
        </div>
        {mapErr && <div className="ilm-micro" style={{ color: 'var(--red-hi)', marginBottom: 10 }}>{mapErr}</div>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {(map?.bases || []).filter(b => b.has_defense).map(b => (
            <div key={b.username} className="ilm-tavern-patron">
              {b.banner?.cloth
                ? <Pennant cloth={b.banner.cloth} cut={b.banner.cut || 'swallow'} frameTier={b.banner.frame_tier || 1} sigil={b.banner.sigil} emblem={b.banner.emblem} paint={b.banner.paint} width={16} />
                : <span className="ilm-guild-badge">{b.username[0].toUpperCase()}</span>}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.8rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{b.username.toUpperCase()}</div>
                <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.8rem' }}>floor {b.highest_floor ?? '?'} · elo {b.elo} · {b.distance} leagues out</div>
              </div>
              <button className="ilm-btn ilm-btn-gold" disabled={busy === 'scout'} onClick={() => scout(b.username)}>
                {busy === 'scout' ? 'SCOUTING…' : 'SEND SCOUTS'}
              </button>
            </div>
          ))}
          {map && (map.bases || []).filter(b => b.has_defense).length === 0 && (
            <div className="ilm-micro" style={{ color: 'var(--muted)' }}>NO RAIDABLE BASES IN RANGE — THE SKY IS QUIET</div>
          )}
        </div>
      </Scrim>
    )
  }

  /* the report */
  const tier = report.tier ?? 0
  const conf = `${(tier / 4) * 100}%`
  return (
    <Scrim onClose={onClose} width={500}>
      <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>SCOUT REPORT</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.6rem', color: 'var(--text-hi)', marginTop: 4 }}>{(report.target || target || '').toUpperCase()}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '8px 0' }}>
        <span className="ilm-micro" style={{ color: 'var(--ember)' }}>INTEL CONFIDENCE</span>
        <div className="ilm-guild-pledge-bar" style={{ width: 120 }}><div style={{ width: conf, background: 'linear-gradient(90deg,#7a4a16,#e8a34c)' }} /></div>
        <span className="ilm-micro" style={{ color: TIER_COLORS[tier] }}>{(report.tier_label || 'estimate').toUpperCase()}</span>
      </div>
      {report.counter_intel_detected && (
        <div className="ilm-micro" style={{ color: 'var(--red-hi)', marginBottom: 8 }}>⚠ THE SCOUTS WERE WATCHED — THEIR WARDS ARE STRONG</div>
      )}
      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginBottom: 14, lineHeight: 1.5 }}>
        {report.impression || (tier >= 3 ? 'The scouts returned with a full accounting.' : 'The scouts saw only shapes through the mist. Numbers are estimates — trust them at your peril.')}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 14 }}>
        <div className="ilm-guild-stat"><span className="ilm-micro">DEF POWER</span><b>{report.base_defense ? `≈ ${Math.round(report.base_defense.total_estimate ?? report.base_defense.total ?? 0).toLocaleString()}` : '???'}</b></div>
        <div className="ilm-guild-stat"><span className="ilm-micro">SHIP</span><b>{report.ship_tier != null ? `TIER ${report.ship_tier}` : '???'}</b></div>
        <div className="ilm-guild-stat"><span className="ilm-micro">DEFENDERS</span><b>{report.defender_count ?? '???'}</b></div>
      </div>
      {report.defenders?.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 4 }}>
          {report.defenders.map((d, i) => (
            <div key={i} className="ilm-feat-mist" style={{ padding: '8px 12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.78rem', letterSpacing: '.05em', color: 'var(--text-hi)' }}>{d.name || 'UNKNOWN SHAPE'}</span>
                <span className="ilm-micro" style={{ color: 'var(--lavender)' }}>{d.hero_class || '???'}{d.level ? ` · LV ${d.level}` : ''}</span>
              </div>
              {(d.max_health || d.skills) && (
                <div className="ilm-micro" style={{ color: 'var(--text-dim)', marginTop: 3 }}>
                  {d.max_health ? `HP ${d.max_health}` : ''}{d.strength ? ` · STR ${d.strength} · INT ${d.intelligence} · AGI ${d.agility} · END ${d.endurance}` : ''}
                  {d.skills?.length ? ` · ${d.skills.join(', ')}` : ''}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="ilm-feat-mist">
          <div className="ilm-micro" style={{ color: 'var(--lavender)' }}>SHAPES IN THE MIST</div>
          <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.84rem', marginTop: 4 }}>The wards held — nothing of the garrison could be seen.</div>
        </div>
      )}
      {report.lootable_estimate && (
        <div className="ilm-micro" style={{ color: 'var(--gold-hi)', marginTop: 10 }}>
          LOOTABLE · ≈{Math.round(report.lootable_estimate.gold).toLocaleString()} GOLD · ≈{Math.round(report.lootable_estimate.ingredients).toLocaleString()} INGREDIENTS
        </div>
      )}
      <StakesBanner variant="capture" compact style={{ marginTop: 12 }} />
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <button className="ilm-btn ilm-btn-danger ilm-btn-block" disabled={busy === 'raid'} onClick={launchRaid}>{busy === 'raid' ? 'THE SIEGE BEGINS…' : 'LAUNCH RAID'}</button>
        <button className="ilm-btn ilm-btn-ghost" disabled={busy === 'scout'} onClick={() => scout(report.target || target)}>{busy === 'scout' ? '…' : 'SCOUT AGAIN'}</button>
      </div>
      <button className="ilm-btn ilm-btn-ghost ilm-btn-block" style={{ marginTop: 8 }} onClick={() => setReport(null)}>BACK TO THE HORIZON</button>
    </Scrim>
  )
}
