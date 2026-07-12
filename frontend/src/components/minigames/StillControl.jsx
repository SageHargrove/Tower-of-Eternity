/*
 * THE STILL — the Alchemist Lab's temperature-control minigame.
 *
 * The condenser's heat drifts on its own (and jerks unpredictably); hold it
 * inside the amber band by feeding (LEFT) or venting (RIGHT). Score = the
 * fraction of the run spent in-band. Difficulty narrows the band, quickens
 * the drift, and lengthens the run.
 */
import React, { useState, useEffect, useRef } from 'react'

const TUNING = {
  novice:     { band: 0.30, drift: 0.10, jerk: 0.05, secs: 8 },
  apprentice: { band: 0.24, drift: 0.14, jerk: 0.08, secs: 9 },
  adept:      { band: 0.19, drift: 0.18, jerk: 0.12, secs: 10 },
  expert:     { band: 0.14, drift: 0.24, jerk: 0.17, secs: 11 },
  master:     { band: 0.10, drift: 0.30, jerk: 0.24, secs: 12 },
  legendary:  { band: 0.065, drift: 0.38, jerk: 0.33, secs: 14 },
}
const PUSH = 0.45  // heat change per second while holding a valve

export default function StillControl({ difficulty, onDone }) {
  const t = TUNING[difficulty] || TUNING.novice
  const [heat, setHeat] = useState(0.5)
  const [left, setLeft] = useState(t.secs)
  const [inBand, setInBand] = useState(true)
  const hold = useRef(0)        // -1 vent, +1 feed, 0 none
  const state = useRef({ heat: 0.5, drift: 1, good: 0, total: 0, t: t.secs })

  useEffect(() => {
    let last = performance.now()
    let raf
    const tick = (now) => {
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      const s = state.current
      // random walk drift + occasional jerk
      if (Math.random() < t.jerk * dt * 10) s.drift = (Math.random() * 2 - 1) * 2
      s.heat += s.drift * t.drift * dt + hold.current * PUSH * dt
      s.heat = Math.max(0, Math.min(1, s.heat))
      const ok = Math.abs(s.heat - 0.5) <= t.band / 2
      s.good += ok ? dt : 0
      s.total += dt
      s.t -= dt
      setHeat(s.heat); setInBand(ok); setLeft(Math.max(0, s.t))
      if (s.t <= 0) {
        onDone(s.total > 0 ? s.good / s.total : 0)
        return
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  const bandLo = (0.5 - t.band / 2) * 100
  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: 10, color: inBand ? '#8fbf9f' : 'var(--red-hi)' }}>
          {inBand ? 'THE DISTILLATE HOLDS' : 'THE HEAT SLIPS'}
        </span>
        <span style={{ fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.14em', color: 'var(--muted)' }}>{left.toFixed(1)}s</span>
      </div>

      {/* the gauge */}
      <div style={{ position: 'relative', height: 40, background: 'linear-gradient(90deg, rgba(70,110,160,.25), rgba(12,7,24,.6) 35%, rgba(12,7,24,.6) 65%, rgba(192,80,64,.3))', border: '1px solid rgba(184,151,98,.4)' }}>
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${bandLo}%`, width: `${t.band * 100}%`, background: 'rgba(216,187,132,.22)', borderLeft: '1px solid var(--gold)', borderRight: '1px solid var(--gold)' }} />
        <div style={{ position: 'absolute', top: -5, bottom: -5, left: `${heat * 100}%`, width: 3, background: inBand ? 'var(--gold-hi)' : 'var(--red-hi)', boxShadow: `0 0 10px ${inBand ? 'rgba(216,187,132,.9)' : 'rgba(224,80,80,.9)'}` }} />
      </div>

      <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
        {[['FEED THE FLAME', 1], ['VENT THE HEAT', -1]].map(([label, dir]) => (
          <button key={label}
            onMouseDown={() => { hold.current = dir }} onMouseUp={() => { hold.current = 0 }} onMouseLeave={() => { hold.current = 0 }}
            onTouchStart={(e) => { e.preventDefault(); hold.current = dir }} onTouchEnd={() => { hold.current = 0 }}
            style={{ flex: 1, padding: '13px 0', cursor: 'pointer', fontFamily: "'Cinzel',serif", letterSpacing: '.16em', fontSize: 11, color: 'var(--text-hi)', background: 'rgba(12,7,24,.6)', border: '1px solid rgba(184,151,98,.4)' }}>
            {label}
          </button>
        ))}
      </div>
      <div style={{ textAlign: 'center', fontStyle: 'italic', fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
        Hold the needle inside the amber band — feeding pushes right, venting pulls left.
      </div>
    </div>
  )
}
