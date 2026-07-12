/*
 * THE HELM — the Skydock's steering minigame (plays at dispatch).
 *
 * Your hull sails a scrolling course; hold PORT/STARBOARD to steer through
 * the waypoint gates while crosswinds shove you. Score = gates cleanly
 * passed. Difficulty narrows gates, strengthens gusts, adds gates.
 */
import React, { useState, useEffect, useRef } from 'react'
import { playClick } from '../../audio'

const TUNING = {
  novice:     { gates: 5,  gap: 0.34, wind: 0.10, speed: 0.9 },
  apprentice: { gates: 6,  gap: 0.28, wind: 0.14, speed: 1.0 },
  adept:      { gates: 7,  gap: 0.23, wind: 0.19, speed: 1.15 },
  expert:     { gates: 8,  gap: 0.18, wind: 0.25, speed: 1.3 },
  master:     { gates: 10, gap: 0.14, wind: 0.32, speed: 1.5 },
  legendary:  { gates: 12, gap: 0.10, wind: 0.42, speed: 1.7 },
}
const STEER = 0.55
const GATE_EVERY = 1.6 // seconds of sailing between gates

export default function HelmGates({ difficulty, onDone }) {
  const t = TUNING[difficulty] || TUNING.novice
  const [x, setX] = useState(0.5)
  const [gates, setGates] = useState([]) // {y 0..1 (approach), cx, passed|null}
  const [done, setDone] = useState(0)
  const [hits, setHits] = useState(0)
  const hold = useRef(0)
  const st = useRef({ x: 0.5, wind: 0, next: 1.0, queue: [], done: 0, hits: 0, spawned: 0 })

  useEffect(() => {
    let last = performance.now(), raf
    const tick = (now) => {
      const dt = Math.min(0.05, (now - last) / 1000); last = now
      const s = st.current
      // wind: slow random walk with gusts
      if (Math.random() < 0.9 * dt) s.wind = (Math.random() * 2 - 1)
      s.x = Math.max(0.04, Math.min(0.96, s.x + (s.wind * t.wind + hold.current * STEER) * dt))
      // spawn gates on a clock until the quota's out
      s.next -= dt * t.speed
      if (s.next <= 0 && s.spawned < t.gates) {
        s.spawned += 1
        s.queue.push({ cx: 0.12 + Math.random() * 0.76, y: 0, passed: null })
        s.next = GATE_EVERY
      }
      // advance gates toward the hull (y: 0 top → 1 hull line)
      for (const g of s.queue) {
        g.y += dt * 0.62 * t.speed
        if (g.y >= 1 && g.passed === null) {
          g.passed = Math.abs(s.x - g.cx) <= t.gap / 2
          s.done += 1
          if (g.passed) { s.hits += 1; playClick() }
        }
      }
      s.queue = s.queue.filter(g => g.y < 1.15)
      setX(s.x); setGates([...s.queue]); setDone(s.done); setHits(s.hits)
      if (s.done >= t.gates) {
        setTimeout(() => onDone(s.hits / t.gates), 500)
        return
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: 10, color: 'var(--muted)' }}>WAYPOINTS · {hits}/{done} OF {t.gates}</span>
        <span style={{ fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.14em', color: 'var(--lavender)' }}>CROSSWINDS LIVE</span>
      </div>

      {/* the sky course */}
      <div style={{ position: 'relative', height: 170, background: 'linear-gradient(180deg, rgba(20,12,38,.9), rgba(9,6,15,.95))', border: '1px solid rgba(184,151,98,.35)', overflow: 'hidden' }}>
        {gates.map((g, i) => (
          <div key={i} style={{ position: 'absolute', top: `${g.y * 88}%`, left: 0, right: 0, height: 2, opacity: g.passed === null ? 1 : 0.35 }}>
            <div style={{ position: 'absolute', left: 0, width: `${(g.cx - t.gap / 2) * 100}%`, height: 2, background: g.passed === false ? 'var(--red)' : 'rgba(150,110,230,.55)' }} />
            <div style={{ position: 'absolute', left: `${(g.cx + t.gap / 2) * 100}%`, right: 0, height: 2, background: g.passed === false ? 'var(--red)' : 'rgba(150,110,230,.55)' }} />
            {g.passed === true && <div style={{ position: 'absolute', left: `${g.cx * 100}%`, transform: 'translateX(-50%)', top: -7, color: 'var(--gold-hi)', fontSize: 11 }}>✦</div>}
          </div>
        ))}
        {/* the hull */}
        <div style={{ position: 'absolute', bottom: 8, left: `${x * 100}%`, transform: 'translateX(-50%) rotate(45deg)', width: 15, height: 15, background: 'linear-gradient(135deg, var(--gold-hi), var(--gold))', boxShadow: '0 0 14px rgba(216,187,132,.6)' }} />
      </div>

      <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
        {[['PORT', -1], ['STARBOARD', 1]].map(([label, dir]) => (
          <button key={label}
            onMouseDown={() => { hold.current = dir }} onMouseUp={() => { hold.current = 0 }} onMouseLeave={() => { hold.current = 0 }}
            onTouchStart={(e) => { e.preventDefault(); hold.current = dir }} onTouchEnd={() => { hold.current = 0 }}
            style={{ flex: 1, padding: '13px 0', cursor: 'pointer', fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: 11, color: 'var(--text-hi)', background: 'rgba(12,7,24,.6)', border: '1px solid rgba(184,151,98,.4)' }}>
            {label}
          </button>
        ))}
      </div>
      <div style={{ textAlign: 'center', fontStyle: 'italic', fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
        Steer the hull through each gate's gap — the winds have their own opinions.
      </div>
    </div>
  )
}
