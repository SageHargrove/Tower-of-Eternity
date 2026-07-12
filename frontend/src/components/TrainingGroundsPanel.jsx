import React, { useState, useEffect } from 'react'
import { getTrainingStatus, setTrainingRegimen, sparHeroes, runTrainingTournament, listHeroes, managerSpar } from '../api/client'
import MinigameShell, { AUTO_RESOLVE_MULT } from './minigames/MinigameShell'
import StrategyDuel from './minigames/StrategyDuel'
import StakesBanner from './StakesBanner'

/*
 * THE TRAINING GROUNDS — facility screen (mock "Training Grounds"):
 * left DRILLMASTERS console, center THE YARD session board (each assigned
 * hero's drill as a row; click to change regimen/focus/intensity), right
 * MENTORSHIP · MASTER & PUPIL panel + the daily tournament. All the old
 * mechanics survive — drills tick server-side, sparring auto-detects Peer
 * vs Mentorship from the level gap.
 */

const STAT_LABELS = {
  strength: 'Strength', intelligence: 'Intelligence', agility: 'Agility',
  endurance: 'Endurance', willpower: 'Willpower', luck: 'Luck',
}
const INTENSITY_ORDER = ['light', 'moderate', 'intense']
const INTENSITY_ROMAN = { light: 'I', moderate: 'II', intense: 'III' }
const INTENSITY_HINT = {
  light: 'Half gains, no fatigue.',
  moderate: 'Standard gains, mild fatigue & stress.',
  intense: 'Double gains — heavy fatigue & stress. Rest them after.',
}
const MENTOR_GAP = 8

const micro = { fontFamily: "'Cinzel',serif", letterSpacing: '.16em', fontSize: 9 }

function HeroDiamond({ hero, size = 26, accent = 'var(--gold-hi)' }) {
  return (
    <span style={{ width: size, height: size, transform: 'rotate(45deg)', flex: 'none', border: `1px solid ${accent}`, background: '#140b22', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
      {hero?.portrait_path && !hero.portrait_path.includes('default_') ? (
        <img src={`/${hero.portrait_path}`} alt={hero.name} draggable={false}
          style={{ width: '142%', height: '142%', objectFit: 'cover', objectPosition: 'center 15%', transform: 'rotate(-45deg)', flex: 'none', pointerEvents: 'none' }} />
      ) : (
        <span style={{ transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontSize: Math.round(size * 0.36), color: accent }}>{hero?.name?.[0] || '?'}</span>
      )}
    </span>
  )
}

export default function TrainingGroundsPanel({ onChanged }) {
  const [data, setData] = useState(null)
  const [busyHero, setBusyHero] = useState(null)
  const [msg, setMsg] = useState(null)
  const [openLane, setOpenLane] = useState(null)   // hero id whose drill controls are expanded

  // Mentorship (right panel)
  const [mentorId, setMentorId] = useState('')
  const [pupilId, setPupilId] = useState('')
  const [sparBusy, setSparBusy] = useState(false)
  const [sparMsg, setSparMsg] = useState(null)

  // Peer sparring (center, behind SET UP SPARRING)
  const [sparOpen, setSparOpen] = useState(false)
  const [aId, setAId] = useState('')
  const [bId, setBId] = useState('')

  // Tournament
  const [tourBusy, setTourBusy] = useState(false)
  const [tourResult, setTourResult] = useState(null)

  // The Commander's Table (strategy duel minigame)
  const [duelRoster, setDuelRoster] = useState([])
  const [duelHeroId, setDuelHeroId] = useState('')
  const [showDuel, setShowDuel] = useState(false)
  const [duelMsg, setDuelMsg] = useState(null)

  async function refresh() {
    try { setData(await getTrainingStatus()) } catch (e) { setMsg({ text: e.message, err: true }) }
    listHeroes(true).then(hs => {
      const living = (hs || []).filter(h => h.is_alive === 1)
      setDuelRoster(living)
      // default the seat to the team leader — the manhwa moment
      const lead = living.find(h => h.is_team_leader === 1)
      if (lead) setDuelHeroId(prev => prev || String(lead.id))
    }).catch(() => {})
  }
  useEffect(() => { refresh() }, [])

  async function resolveDuel(mult) {
    setShowDuel(false)
    try {
      const res = await managerSpar(parseInt(duelHeroId), mult)
      setDuelMsg({ text: res.message + (res.xp ? ` (+${res.xp.toLocaleString()} XP${res.leadership_up ? ', leadership deepens' : ''}${res.leveled ? ` — LEVEL ${res.new_level}!` : ''})` : '') })
      if (onChanged) onChanged()
    } catch (e) {
      setDuelMsg({ text: e.message, err: true })
    }
  }

  async function applyRegimen(hero, patch) {
    const regimen = patch.regimen ?? hero.training_regimen ?? 'focus'
    let focus = patch.focus ?? hero.training_focus ?? null
    const intensity = patch.intensity ?? hero.training_intensity ?? 'moderate'
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

  async function runSpar(idA, idB, isMentor) {
    setSparBusy(true)
    setSparMsg(null)
    try {
      const res = await sparHeroes(Number(idA), Number(idB))
      setSparMsg({ lines: res.messages || [], err: false, mentor: isMentor })
      await refresh()
      if (onChanged) onChanged()
    } catch (e) {
      setSparMsg({ lines: [e.message], err: true })
    } finally {
      setSparBusy(false)
    }
  }

  async function handleTournament() {
    setTourBusy(true)
    try {
      const res = await runTrainingTournament()
      setTourResult(res)
      await refresh()
      if (onChanged) onChanged()
    } catch (e) {
      setSparMsg({ lines: [e.message], err: true })
    } finally {
      setTourBusy(false)
    }
  }

  if (!data) return null
  const heroes = data.heroes || []

  const mentor = heroes.find(h => String(h.id) === mentorId)
  const pupil = heroes.find(h => String(h.id) === pupilId)
  const mentorGap = mentor && pupil ? (mentor.level || 1) - (pupil.level || 1) : null
  const canMentor = mentorGap != null && mentorGap >= MENTOR_GAP

  const a = heroes.find(h => String(h.id) === aId)
  const b = heroes.find(h => String(h.id) === bId)
  const peerGap = a && b ? Math.abs((a.level || 1) - (b.level || 1)) : null
  const peerOk = peerGap != null && peerGap <= 5

  // Drillmasters — the sharpest tactical minds on the grounds hold the posts.
  const drillmasters = [...heroes].sort((x, y) => (y.apt_tactical ?? 0) - (x.apt_tactical ?? 0)).slice(0, 3)
  const t = data.tournament || {}

  const regimenLine = h => {
    const r = h.training_regimen || 'focus'
    const label = data.regimens?.[r]?.label || r
    if (r === 'conditioning') return `${label} · ${STAT_LABELS[h.training_focus] || 'Strength'} · cap ${data.conditioning_cap}`
    if (r === 'weapon_drill') {
      const sk = (h.skills || []).find(s => String(s.id) === String(h.training_focus))
      return `${label} · ${sk?.name || 'no skill chosen'}`
    }
    if (r === 'meditation') return `${label} · Mental ${h.apt_mental ?? 50} · ${h.aptitudes_revealed || 0}/6 revealed`
    return label
  }

  return (
    <div style={{ display: 'flex', gap: 18, marginTop: '1rem', alignItems: 'flex-start', flexWrap: 'wrap' }}>
      {/* ═══ LEFT — the console ═══ */}
      <div style={{ flex: '0 1 230px', minWidth: 210 }}>
        <div style={{ border: '1px solid rgba(150,110,230,.35)', background: 'rgba(12,7,24,.5)', padding: '14px 16px' }}>
          <div style={{ ...micro, letterSpacing: '.22em', color: 'var(--muted)' }}>DRILL INTENSITY</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginTop: 8 }}>
            <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 30, color: 'var(--text-hi)' }}>
              {INTENSITY_ROMAN[(heroes[0]?.training_intensity) || 'moderate']}
            </span>
            <span style={{ fontSize: 13, fontStyle: 'italic', color: 'var(--muted)' }}>of III · set per hero in the yard</span>
          </div>
        </div>

        <div style={{ ...micro, letterSpacing: '.2em', color: 'var(--muted)', margin: '16px 0 8px' }}>DRILLMASTERS · {Math.min(heroes.length, 3)} / 3</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {drillmasters.map(h => (
            <div key={h.id} style={{ display: 'flex', alignItems: 'center', gap: 10, border: '1px solid rgba(184,151,98,.3)', background: 'rgba(12,7,24,.4)', padding: '8px 12px' }}>
              <HeroDiamond hero={h} size={24} accent="var(--lavender)" />
              <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 11, letterSpacing: '.06em', color: 'var(--text-hi)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{h.name.toUpperCase()}</span>
              <span style={{ fontSize: 12, fontStyle: 'italic', color: 'var(--muted)', marginLeft: 'auto', whiteSpace: 'nowrap' }}>teaching {h.apt_tactical ?? 50}</span>
            </div>
          ))}
          {heroes.length < 3 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, border: '1px dashed rgba(150,110,230,.4)', background: 'rgba(12,7,24,.25)', padding: '8px 12px' }}>
              <span style={{ width: 24, height: 24, transform: 'rotate(45deg)', flex: 'none', border: '1px dashed rgba(200,169,245,.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ transform: 'rotate(-45deg)', color: 'var(--lavender)', fontSize: 11 }}>+</span>
              </span>
              <span style={{ ...micro, fontSize: 8, color: '#6f628c' }}>EMPTY POST · ASSIGN A HERO ABOVE</span>
            </div>
          )}
        </div>
        {msg && <div style={{ fontSize: 13, fontStyle: 'italic', color: msg.err ? '#d98a8a' : '#8fbf9f', marginTop: 10 }}>{msg.text}</div>}
      </div>

      {/* ═══ CENTER — the yard ═══ */}
      <div style={{ flex: '1.6 1 360px', minWidth: 340 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: 11, color: 'var(--gold)' }}>THE YARD · IN SESSION</span>
          <span style={{ height: 1, flex: 1, background: 'rgba(184,151,98,.2)' }} />
          <button onClick={() => setSparOpen(o => !o)}
            style={{ cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: 600, fontSize: 9, letterSpacing: '.16em', color: '#cdbfe4', background: 'none', border: '1px solid rgba(150,110,230,.45)', padding: '6px 14px', clipPath: 'polygon(6px 0,100% 0,calc(100% - 6px) 100%,0 100%)' }}>
            {sparOpen ? 'CLOSE SPARRING ▾' : '+ SET UP SPARRING'}
          </button>
        </div>

        {/* peer sparring form */}
        {sparOpen && (
          <div style={{ border: '1px solid rgba(150,110,230,.4)', background: 'linear-gradient(160deg,rgba(42,22,80,.24),rgba(12,7,24,.55))', padding: '12px 16px', marginBottom: 10 }}>
            <StakesBanner variant="echo" compact note="practice blades — nobody gets hurt here" style={{ marginBottom: 10 }} />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <select className="input" value={aId} onChange={e => setAId(e.target.value)} style={{ flex: 1, minWidth: 120, fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.06em' }}>
                <option value="">FIRST…</option>
                {heroes.map(h => <option key={h.id} value={h.id} disabled={String(h.id) === bId}>{h.name.toUpperCase()} · LV {h.level}</option>)}
              </select>
              <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, color: 'var(--muted)' }}>⚔</span>
              <select className="input" value={bId} onChange={e => setBId(e.target.value)} style={{ flex: 1, minWidth: 120, fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.06em' }}>
                <option value="">SECOND…</option>
                {heroes.map(h => <option key={h.id} value={h.id} disabled={String(h.id) === aId}>{h.name.toUpperCase()} · LV {h.level}</option>)}
              </select>
              <button className="ilm-btn ilm-btn-gold" disabled={sparBusy || !a || !b || !peerOk} onClick={() => runSpar(aId, bId, false)}>
                {sparBusy ? 'SPARRING…' : 'BEGIN'}
              </button>
            </div>
            {peerGap != null && !peerOk && (
              <div style={{ fontSize: 12.5, fontStyle: 'italic', color: '#e8a34c', marginTop: 6 }}>
                Gap of {peerGap} is too wide for peers — pair a mentor instead ({MENTOR_GAP}+ gap, right panel).
              </div>
            )}
          </div>
        )}

        {/* session rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {heroes.length === 0 && (
            <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 14, padding: '14px 2px' }}>
              The yard stands empty — assign heroes to the Training Grounds above.
            </div>
          )}
          {heroes.map(h => {
            const open = openLane === h.id
            const regimen = h.training_regimen || 'focus'
            const intensity = h.training_intensity || 'moderate'
            const gains = h.training_gains || {}
            return (
              <div key={h.id}>
                <button onClick={() => setOpenLane(open ? null : h.id)}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 14, padding: '11px 16px', cursor: 'pointer', textAlign: 'left',
                    border: open ? '1px solid rgba(255,216,138,.5)' : '1px solid rgba(184,151,98,.3)',
                    background: open ? 'linear-gradient(90deg,rgba(184,151,98,.1),rgba(12,7,24,.55))' : 'rgba(12,7,24,.5)' }}>
                  <HeroDiamond hero={h} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 13, letterSpacing: '.08em', color: 'var(--text-hi)' }}>
                      {(data.regimens?.[regimen]?.label || 'DRILL').toUpperCase()} — {h.name.toUpperCase()}
                    </div>
                    <div style={{ fontSize: 13, fontStyle: 'italic', color: 'var(--muted)', marginTop: 2 }}>{regimenLine(h)} · intensity {INTENSITY_ROMAN[intensity]}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, flex: 'none', alignItems: 'center' }}>
                    <span title="Fatigue — 10 locks them out of the Tower" style={{ ...micro, color: h.fatigue >= 8 ? '#d98a8a' : 'var(--muted)' }}>FTG {h.fatigue}/10</span>
                    <div style={{ width: 70, height: 5, background: 'rgba(0,0,0,.5)', border: '1px solid rgba(150,110,230,.3)' }}>
                      <div style={{ width: `${(INTENSITY_ORDER.indexOf(intensity) + 1) * 33}%`, height: '100%', background: 'linear-gradient(90deg,#8b46d6,#c8a9f5)' }} />
                    </div>
                  </div>
                </button>
                {open && (
                  <div style={{ border: '1px solid rgba(184,151,98,.2)', borderTop: 'none', background: 'rgba(8,6,14,.6)', padding: '12px 16px', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <select className="input" value={regimen} disabled={busyHero === h.id}
                      onChange={e => applyRegimen(h, { regimen: e.target.value })}
                      style={{ fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.06em' }}>
                      {Object.entries(data.regimens).map(([k, v]) => <option key={k} value={k}>{v.label.toUpperCase()}</option>)}
                    </select>
                    {regimen === 'conditioning' && (
                      <select className="input" value={h.training_focus || 'strength'} disabled={busyHero === h.id}
                        onChange={e => applyRegimen(h, { regimen: 'conditioning', focus: e.target.value })}
                        style={{ fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.06em' }}>
                        {data.stat_keys.map(s => <option key={s} value={s}>{STAT_LABELS[s].toUpperCase()} ({gains[s] || 0}/{data.conditioning_cap})</option>)}
                      </select>
                    )}
                    {regimen === 'weapon_drill' && (
                      <select className="input" value={h.training_focus || (h.skills?.[0]?.id ?? '')} disabled={busyHero === h.id || !h.skills?.length}
                        onChange={e => applyRegimen(h, { regimen: 'weapon_drill', focus: e.target.value })}
                        style={{ fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.06em' }}>
                        {(h.skills || []).map(s => <option key={s.id} value={s.id}>{s.name.toUpperCase()} (LV {s.level || 1})</option>)}
                        {!h.skills?.length && <option value="">NO SKILLS TO DRILL</option>}
                      </select>
                    )}
                    <span style={{ flex: 1 }} />
                    <span style={{ ...micro, color: 'var(--muted)' }}>INTENSITY</span>
                    {INTENSITY_ORDER.map(int => (
                      <button key={int} disabled={busyHero === h.id} title={INTENSITY_HINT[int]}
                        onClick={() => applyRegimen(h, { intensity: int })}
                        style={{ width: 30, height: 26, flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 11, cursor: 'pointer',
                          border: intensity === int ? '1px solid var(--gold-hi)' : '1px solid rgba(184,151,98,.28)',
                          background: intensity === int ? 'rgba(184,151,98,.14)' : 'rgba(12,7,24,.45)',
                          color: intensity === int ? 'var(--gold-hi)' : 'var(--muted)',
                          clipPath: 'polygon(5px 0,100% 0,calc(100% - 5px) 100%,0 100%)' }}>
                        {INTENSITY_ROMAN[int]}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* ═══ RIGHT — mentorship ═══ */}
      <div style={{ flex: '1 1 260px', minWidth: 250, position: 'relative', border: '1px solid rgba(184,151,98,.35)', background: 'rgba(12,7,24,.5)', padding: '16px 18px' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: 12, height: 12, borderLeft: '2px solid var(--gold-hi)', borderTop: '2px solid var(--gold-hi)' }} />
        <div style={{ ...micro, letterSpacing: '.24em', color: 'var(--muted)' }}>MENTORSHIP</div>
        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 19, color: 'var(--text-hi)', marginTop: 4 }}>MASTER & PUPIL</div>
        <div style={{ fontSize: 13.5, fontStyle: 'italic', color: 'var(--muted)', marginTop: 3 }}>Skill flows downhill from calloused hands.</div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '16px 0' }}>
          <select className="input" value={mentorId} onChange={e => setMentorId(e.target.value)} style={{ flex: 1, fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.06em' }}>
            <option value="">MASTER…</option>
            {heroes.map(h => <option key={h.id} value={h.id} disabled={String(h.id) === pupilId}>{h.name.toUpperCase()} · LV {h.level}</option>)}
          </select>
          <span style={{ fontFamily: "'Cinzel',serif", color: 'var(--gold-hi)' }}>→</span>
          <select className="input" value={pupilId} onChange={e => setPupilId(e.target.value)} style={{ flex: 1, fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.06em' }}>
            <option value="">PUPIL…</option>
            {heroes.map(h => <option key={h.id} value={h.id} disabled={String(h.id) === mentorId}>{h.name.toUpperCase()} · LV {h.level}</option>)}
          </select>
        </div>
        <div style={{ fontSize: 13, fontStyle: 'italic', color: mentorGap == null ? 'var(--muted)' : canMentor ? '#c8b8dd' : '#e8a34c', lineHeight: 1.5 }}>
          {mentorGap == null
            ? `A master must stand ${MENTOR_GAP}+ levels above the pupil — XP pours downhill, a skill may pass with it, and a bond forms.`
            : canMentor
              ? `${mentor.name} stands ${mentorGap} levels above ${pupil.name} — the lesson will take.`
              : `Only ${mentorGap} level${Math.abs(mentorGap) === 1 ? '' : 's'} apart — a master needs ${MENTOR_GAP}+ over the pupil.`}
        </div>
        {sparMsg && (
          <div style={{ marginTop: 10, border: '1px solid rgba(184,151,98,.3)', background: 'rgba(184,151,98,.06)', padding: '8px 12px', fontSize: 13, fontStyle: 'italic', color: sparMsg.err ? '#d98a8a' : '#c8b8dd', display: 'flex', flexDirection: 'column', gap: 3 }}>
            {sparMsg.lines.map((l, i) => <div key={i}>{l}</div>)}
          </div>
        )}
        <button disabled={sparBusy || !canMentor} onClick={() => runSpar(mentorId, pupilId, true)}
          style={{ width: '100%', marginTop: 14, textAlign: 'center', cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 12, color: '#0a0710', background: 'linear-gradient(120deg,#c8a9f5,#8b46d6)', border: 'none', padding: '11px 0', clipPath: 'polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)', boxShadow: '0 8px 24px rgba(124,58,214,.4)', opacity: sparBusy || !canMentor ? 0.5 : 1 }}>
          {sparBusy ? 'THE LESSON RUNS…' : 'PAIR A MENTOR'}
        </button>

        {/* tournament */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 18, borderTop: '1px solid rgba(184,151,98,.2)', paddingTop: 12 }}>
          <span style={{ fontSize: 15, fontStyle: 'italic', color: '#c8b8dd' }}>Tournament</span>
          <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.18em', fontSize: 11, color: 'var(--gold-hi)' }}>
            {t.cooldown_remaining > 0 ? `IN ${Math.floor(t.cooldown_remaining / 3600)}H ${Math.floor((t.cooldown_remaining % 3600) / 60)}M` : t.ready ? 'READY' : `NEEDS ${t.min_entrants ?? 3}+`}
          </span>
        </div>
        <button className="ilm-btn ilm-btn-ghost ilm-btn-block" style={{ marginTop: 8 }} disabled={tourBusy || !t.ready} onClick={handleTournament}>
          {tourBusy ? 'HOLDING…' : `HOLD TOURNAMENT · ${t.entrants ?? 0} ENTRANTS`}
        </button>
        {tourResult && (
          <div style={{ marginTop: 10, fontSize: 13 }}>
            {(tourResult.log || []).slice(0, 4).map((l, i) => <div key={i} style={{ fontStyle: 'italic', color: '#8fbf9f' }}>{l}</div>)}
            {(tourResult.standings || []).map((s, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'baseline', marginTop: 2 }}>
                <span style={{ ...micro, color: i === 0 ? '#ffd88a' : 'var(--muted)', width: 14 }}>{i + 1}</span>
                <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.06em', color: 'var(--text-hi)', flex: 1 }}>{s.name.toUpperCase()}</span>
                <span style={{ fontSize: 12, fontStyle: 'italic', color: 'var(--muted)' }}>{s.wins} win{s.wins === 1 ? '' : 's'}</span>
              </div>
            ))}
          </div>
        )}

        {/* THE COMMANDER'S TABLE — play a hero at stones; the game trains them.
            Backend gates it to once per day per hero. */}
        <div style={{ marginTop: 18, borderTop: '1px solid rgba(184,151,98,.25)', paddingTop: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontSize: 15, fontStyle: 'italic', color: '#c8b8dd' }}>The Commander's Table</span>
            <span style={{ ...micro, color: 'var(--muted)' }}>ONCE A DAY</span>
          </div>
          <div style={{ fontSize: 12.5, fontStyle: 'italic', color: 'var(--muted)', marginTop: 4 }}>
            Sit a hero across the board — win or lose, the game sharpens them. Higher stakes teach more.
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <select className="input" value={duelHeroId} onChange={e => setDuelHeroId(e.target.value)}
              style={{ flex: 1, background: 'rgba(0,0,0,.3)', border: '1px solid var(--border)', color: '#fff', padding: '0.4rem' }}>
              <option value="">Choose an opponent…</option>
              {duelRoster.map(h => (
                <option key={h.id} value={h.id}>{h.name}{h.is_team_leader ? ' — TEAM LEADER' : ''} (Lv.{h.level})</option>
              ))}
            </select>
            <button className="ilm-btn ilm-btn-gold" disabled={!duelHeroId} onClick={() => setShowDuel(true)}>SIT DOWN</button>
          </div>
          {duelMsg && <div style={{ fontSize: 12.5, fontStyle: 'italic', color: duelMsg.err ? '#d98a8a' : '#a8dfb8', marginTop: 6 }}>{duelMsg.text}</div>}
        </div>

        {showDuel && (() => {
          const opp = duelRoster.find(h => String(h.id) === String(duelHeroId))
          return (
            <MinigameShell
              title="THE COMMANDER'S TABLE"
              flavor={`${opp?.name || 'The hero'} sets the stones. Every game leaves them a little sharper — a hard one leaves them changed.`}
              onSkip={() => resolveDuel(AUTO_RESOLVE_MULT)}
              onResolve={(mult) => resolveDuel(mult)}
              game={(difficulty, onDone) => <StrategyDuel difficulty={difficulty} onDone={onDone} opponentName={opp?.name || 'the hero'} aptitude={opp?.apt_leadership ?? 50} />}
            />
          )
        })()}
      </div>
    </div>
  )
}
