import React, { useState, useEffect } from 'react'
import { getTrainingStatus, setTrainingRegimen, sparHeroes, runTrainingTournament } from '../api/client'

// The full Training Grounds management panel, rendered inside the facility
// card. Two halves:
//   1. Solo Drills — per assigned hero, pick a regimen (Focus/Conditioning/
//      Meditation/Weapon Drills) + intensity. Ticks over time server-side.
//   2. Sparring — pick two heroes; the backend auto-detects Peer vs
//      Mentorship from the level gap.

const STAT_LABELS = {
  strength: 'Strength', intelligence: 'Intelligence', agility: 'Agility',
  endurance: 'Endurance', willpower: 'Willpower', luck: 'Luck',
}
const INTENSITY_ORDER = ['light', 'moderate', 'intense']
const INTENSITY_HINT = {
  light: 'Half gains, no fatigue.',
  moderate: 'Standard gains, mild fatigue & stress.',
  intense: 'Double gains — heavy fatigue & stress. Rest them after.',
}
const MENTOR_GAP = 8

function panelBox(children, key) {
  return <div key={key} style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: 6 }}>{children}</div>
}

export default function TrainingGroundsPanel({ onChanged }) {
  const [data, setData] = useState(null)
  const [busyHero, setBusyHero] = useState(null)
  const [msg, setMsg] = useState(null)

  // Sparring state
  const [aId, setAId] = useState('')
  const [bId, setBId] = useState('')
  const [sparBusy, setSparBusy] = useState(false)
  const [sparMsg, setSparMsg] = useState(null)

  // Tournament state
  const [tourBusy, setTourBusy] = useState(false)
  const [tourResult, setTourResult] = useState(null)
  const [tourMsg, setTourMsg] = useState(null)

  async function refresh() {
    try { setData(await getTrainingStatus()) } catch (e) { setMsg({ text: e.message, err: true }) }
  }
  useEffect(() => { refresh() }, [])

  async function applyRegimen(hero, patch) {
    const regimen = patch.regimen ?? hero.training_regimen ?? 'focus'
    let focus = patch.focus ?? hero.training_focus ?? null
    const intensity = patch.intensity ?? hero.training_intensity ?? 'moderate'
    // Default a sensible focus when switching INTO a regimen that needs one.
    if (regimen === 'conditioning' && !focus) focus = 'strength'
    if (regimen === 'weapon_drill' && !focus) focus = hero.skills?.[0]?.id || null
    setBusyHero(hero.id)
    setMsg(null)
    try {
      await setTrainingRegimen(hero.id, regimen, focus, intensity)
      await refresh()
      if (onChanged) onChanged()
    } catch (e) {
      setMsg({ text: e.message, err: true })
    } finally {
      setBusyHero(null)
    }
  }

  async function handleTournament() {
    setTourBusy(true)
    setTourMsg(null)
    try {
      const res = await runTrainingTournament()
      setTourResult(res)
      await refresh()
      if (onChanged) onChanged()
    } catch (e) {
      setTourMsg(e.message)
    } finally {
      setTourBusy(false)
    }
  }

  async function handleSpar() {
    if (!aId || !bId) return
    setSparBusy(true)
    setSparMsg(null)
    try {
      const res = await sparHeroes(Number(aId), Number(bId))
      setSparMsg({ lines: res.messages || [], err: false })
      await refresh()
      if (onChanged) onChanged()
    } catch (e) {
      setSparMsg({ lines: [e.message], err: true })
    } finally {
      setSparBusy(false)
    }
  }

  if (!data) return null
  const heroes = data.heroes || []

  const a = heroes.find(h => String(h.id) === aId)
  const b = heroes.find(h => String(h.id) === bId)
  const gap = a && b ? Math.abs((a.level || 1) - (b.level || 1)) : null
  const predictedMode = gap == null ? null : gap >= MENTOR_GAP ? 'Mentorship' : gap <= 5 ? 'Peer Sparring' : 'mismatch'

  return (
    <>
      {/* ── Solo Drills ── */}
      {panelBox(
        <>
          <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif', marginBottom: '0.3rem' }}>🏋 Solo Drills</div>
          <div className="text-dim text-sm" style={{ marginBottom: '0.6rem' }}>
            Each hero here trains over time. Conditioning permanently raises a stat (cap +{data.conditioning_cap} at this Training Grounds level); Meditation sharpens Mental aptitude and can reveal hidden ones; Weapon Drills grind a chosen skill. Intensity trades faster gains for fatigue & stress.
          </div>
          {heroes.length === 0 && <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>Assign heroes to the Training Grounds to start drilling.</div>}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {heroes.map(h => {
              const regimen = h.training_regimen || 'focus'
              const intensity = h.training_intensity || 'moderate'
              const gains = h.training_gains || {}
              return (
                <div key={h.id} className="card" style={{ padding: '0.6rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.4rem' }}>
                    <div style={{ fontWeight: 'bold', color: 'var(--text-hi)' }}>
                      {h.name} <span className="text-dim" style={{ fontSize: '0.78rem' }}>Lv.{h.level} {h.hero_class}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.72rem' }}>
                      <span title="Fatigue — 10 locks them out of the Tower until rested" style={{ color: h.fatigue >= 8 ? 'var(--red)' : 'var(--text-dim)' }}>😪 {h.fatigue}/10</span>
                      <span title="Stress" style={{ color: h.stress >= 70 ? '#f0a848' : 'var(--text-dim)' }}>😰 {h.stress}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.5rem', alignItems: 'center' }}>
                    <select className="input" value={regimen} disabled={busyHero === h.id}
                      onChange={e => applyRegimen(h, { regimen: e.target.value })}
                      style={{ fontSize: '0.8rem', padding: '0.25rem' }}>
                      {Object.entries(data.regimens).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                    </select>

                    {regimen === 'conditioning' && (
                      <select className="input" value={h.training_focus || 'strength'} disabled={busyHero === h.id}
                        onChange={e => applyRegimen(h, { regimen: 'conditioning', focus: e.target.value })}
                        style={{ fontSize: '0.8rem', padding: '0.25rem' }}>
                        {data.stat_keys.map(s => {
                          const at = gains[s] || 0
                          return <option key={s} value={s}>{STAT_LABELS[s]} ({at}/{data.conditioning_cap})</option>
                        })}
                      </select>
                    )}
                    {regimen === 'weapon_drill' && (
                      <select className="input" value={h.training_focus || (h.skills?.[0]?.id ?? '')} disabled={busyHero === h.id || !h.skills?.length}
                        onChange={e => applyRegimen(h, { regimen: 'weapon_drill', focus: e.target.value })}
                        style={{ fontSize: '0.8rem', padding: '0.25rem' }}>
                        {(h.skills || []).map(s => <option key={s.id} value={s.id}>{s.name} (Lv.{s.level || 1})</option>)}
                        {!h.skills?.length && <option value="">No skills to drill</option>}
                      </select>
                    )}
                    {regimen === 'meditation' && (
                      <span className="text-dim text-sm">Mental {h.apt_mental ?? 50} · {h.aptitudes_revealed || 0}/6 revealed</span>
                    )}

                    <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.2rem' }}>
                      {INTENSITY_ORDER.map(int => (
                        <button key={int} disabled={busyHero === h.id} title={INTENSITY_HINT[int]}
                          onClick={() => applyRegimen(h, { intensity: int })}
                          className={`btn ${intensity === int ? 'btn-gold' : ''}`}
                          style={{ fontSize: '0.68rem', padding: '0.15rem 0.4rem', textTransform: 'capitalize' }}>
                          {int}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
          {msg && <div style={{ color: msg.err ? '#f87' : '#8e8', fontSize: '0.82rem', marginTop: '0.5rem' }}>{msg.text}</div>}
        </>,
        'drills'
      )}

      {/* ── Sparring ── */}
      {panelBox(
        heroes.length < 2 ? (
          <>
            <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif', marginBottom: '0.3rem' }}>⚔ Sparring</div>
            <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>Assign at least two heroes to spar them together.</div>
          </>
        ) : (
          <>
            <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif', marginBottom: '0.4rem' }}>⚔ Sparring</div>
            <div className="text-dim text-sm" style={{ marginBottom: '0.5rem' }}>
              Similar levels → <b>Peer Sparring</b> (both gain XP + likely a skill level). An {MENTOR_GAP}+ level gap → <b>Mentorship</b> (the veteran pours XP into the student, may teach one of their own skills, and both grow a combat bond).
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <select className="input" value={aId} onChange={e => setAId(e.target.value)} style={{ flex: 1, minWidth: 130, fontSize: '0.85rem' }}>
                <option value="">First hero…</option>
                {heroes.map(h => <option key={h.id} value={h.id} disabled={String(h.id) === bId}>{h.name} (Lv.{h.level})</option>)}
              </select>
              <span className="text-dim">vs</span>
              <select className="input" value={bId} onChange={e => setBId(e.target.value)} style={{ flex: 1, minWidth: 130, fontSize: '0.85rem' }}>
                <option value="">Second hero…</option>
                {heroes.map(h => <option key={h.id} value={h.id} disabled={String(h.id) === aId}>{h.name} (Lv.{h.level})</option>)}
              </select>
            </div>
            {predictedMode && predictedMode !== 'mismatch' && (
              <div className="text-dim text-sm" style={{ marginTop: '0.4rem' }}>Level gap {gap} → <span style={{ color: 'var(--gold)' }}>{predictedMode}</span></div>
            )}
            {predictedMode === 'mismatch' && (
              <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', color: '#f0a848' }}>
                Gap {gap} is too wide for peers but not wide enough to mentor (needs {MENTOR_GAP}+). Pick a closer or further-apart pair.
              </div>
            )}
            <button className="btn btn-gold" disabled={sparBusy || !a || !b || predictedMode === 'mismatch'} onClick={handleSpar}
              style={{ marginTop: '0.6rem', fontSize: '0.85rem' }}>
              {sparBusy ? 'Sparring…' : 'Begin Sparring'}
            </button>
            {sparMsg && (
              <div style={{ marginTop: '0.6rem', fontSize: '0.85rem', color: sparMsg.err ? '#f87' : '#8e8', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {sparMsg.lines.map((l, i) => <div key={i}>{l}</div>)}
              </div>
            )}
          </>
        ),
        'sparring'
      )}

      {/* ── Internal Tournament ── */}
      {panelBox(
        <>
          <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif', marginBottom: '0.4rem' }}>🏆 Sparring Tournament</div>
          <div className="text-dim text-sm" style={{ marginBottom: '0.5rem' }}>
            A round-robin among every hero here (min {data.tournament?.min_entrants ?? 3}). Everyone who competes gets a morale lift; the champion earns big XP, a permanent stat, and glory. Once per day.
          </div>
          {(() => {
            const t = data.tournament || {}
            const hrs = Math.floor((t.cooldown_remaining || 0) / 3600)
            const mins = Math.floor(((t.cooldown_remaining || 0) % 3600) / 60)
            return (
              <button className="btn btn-gold" disabled={tourBusy || !t.ready} onClick={handleTournament} style={{ fontSize: '0.85rem' }}>
                {tourBusy ? 'Holding tournament…'
                  : t.cooldown_remaining > 0 ? `Next tournament in ${hrs}h ${mins}m`
                  : t.entrants < (t.min_entrants ?? 3) ? `Need ${t.min_entrants ?? 3}+ heroes assigned (${t.entrants} now)`
                  : `Hold Tournament (${t.entrants} entrants)`}
              </button>
            )
          })()}
          {tourMsg && <div style={{ color: '#f87', fontSize: '0.82rem', marginTop: '0.5rem' }}>{tourMsg}</div>}
          {tourResult && (
            <div style={{ marginTop: '0.6rem', fontSize: '0.85rem' }}>
              <div style={{ color: '#8e8', display: 'flex', flexDirection: 'column', gap: '0.15rem', marginBottom: '0.4rem' }}>
                {(tourResult.log || []).map((l, i) => <div key={i}>{l}</div>)}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
                {(tourResult.standings || []).map((s, i) => (
                  <div key={i} className="text-dim" style={{ fontSize: '0.8rem' }}>
                    {i + 1}. {s.name} <span style={{ opacity: 0.6 }}>— {s.wins} win{s.wins === 1 ? '' : 's'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>,
        'tournament'
      )}
    </>
  )
}
