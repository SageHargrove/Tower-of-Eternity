/*
 * STRIKE THE STEEL — the Forge's timing minigame.
 *
 * A needle sweeps the bar; land each of three strikes inside the golden
 * zone. Difficulty shrinks the zone and speeds the needle. Score = mean
 * strike accuracy (1.0 = dead center), fed to MinigameShell's multiplier.
 */
import React, { useState, useRef, useEffect } from 'react'
import { playCraftClang, playClick } from '../../audio'

const TUNING = {
  novice:     { zone: 0.26,  speed: 0.9,  strikes: 3 },
  apprentice: { zone: 0.20,  speed: 1.15, strikes: 3 },
  adept:      { zone: 0.15,  speed: 1.45, strikes: 3 },
  expert:     { zone: 0.10,  speed: 1.9,  strikes: 4 },
  master:     { zone: 0.065, speed: 2.4,  strikes: 5 },
  legendary:  { zone: 0.035, speed: 3.1,  strikes: 6 },
}

export default function ForgeTiming({ difficulty, onDone }) {
  const t = TUNING[difficulty] || TUNING.adept
  const [strikes, setStrikes] = useState([])       // accuracy per strike, 0..1
  const [zoneCenter, setZoneCenter] = useState(0.5)
  const [pos, setPos] = useState(0)
  const dir = useRef(1)
  const raf = useRef(null)
  const posRef = useRef(0)

  useEffect(() => {
    let last = performance.now()
    const tick = (now) => {
      const dt = (now - last) / 1000
      last = now
      let p = posRef.current + dir.current * t.speed * dt
      if (p > 1) { p = 1; dir.current = -1 }
      if (p < 0) { p = 0; dir.current = 1 }
      posRef.current = p
      setPos(p)
      raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf.current)
  }, [t.speed])

  function strike() {
    const dist = Math.abs(posRef.current - zoneCenter)
    const half = t.zone / 2
    // inside the zone: accuracy scales center=1 → edge≈0.55; outside: 0.
    const acc = dist <= half ? 1 - (dist / half) * 0.45 : 0
    acc > 0 ? playCraftClang() : playClick()
    const next = [...strikes, acc]
    setStrikes(next)
    if (next.length >= t.strikes) {
      cancelAnimationFrame(raf.current)
      setTimeout(() => onDone(next.reduce((a, b) => a + b, 0) / next.length), 550)
    } else {
      // zone jumps somewhere new for the next strike
      setZoneCenter(0.15 + Math.random() * 0.7)
    }
  }

  return (
    <div style={{ marginTop: 22 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
        <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: 10, color: 'var(--muted)' }}>
          STRIKE {strikes.length + 1} OF {t.strikes}
        </span>
        <span style={{ display: 'flex', gap: 6 }}>
          {Array.from({ length: t.strikes }).map((_, i) => (
            <span key={i} style={{ width: 8, height: 8, transform: 'rotate(45deg)', display: 'inline-block',
              background: i < strikes.length ? (strikes[i] > 0.75 ? 'var(--gold-hi)' : strikes[i] > 0 ? 'var(--gold-dim)' : 'var(--red)') : 'transparent',
              border: i < strikes.length ? 'none' : '1px solid rgba(184,151,98,.4)' }} />
          ))}
        </span>
      </div>

      {/* the bar */}
      <div style={{ position: 'relative', height: 34, background: 'rgba(0,0,0,.55)', border: '1px solid rgba(184,151,98,.4)' }}>
        {/* golden zone */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${(zoneCenter - t.zone / 2) * 100}%`, width: `${t.zone * 100}%`, background: 'linear-gradient(90deg, rgba(216,187,132,.15), rgba(216,187,132,.5), rgba(216,187,132,.15))', borderLeft: '1px solid var(--gold)', borderRight: '1px solid var(--gold)' }} />
        {/* center line of zone */}
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${zoneCenter * 100}%`, width: 1, background: 'var(--gold-hi)' }} />
        {/* the needle */}
        <div style={{ position: 'absolute', top: -4, bottom: -4, left: `${pos * 100}%`, width: 2, background: 'var(--text-hi)', boxShadow: '0 0 8px rgba(240,235,220,.8)' }} />
      </div>

      <button className="btn btn-primary" style={{ width: '100%', marginTop: 16, padding: '13px 0', fontSize: '0.95rem', letterSpacing: '.3em' }}
        onClick={strike}>
        STRIKE
      </button>
      <div style={{ textAlign: 'center', fontStyle: 'italic', fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
        Land the hammer inside the golden band — dead center burns brightest.
      </div>
    </div>
  )
}
