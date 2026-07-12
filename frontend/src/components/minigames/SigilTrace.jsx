/*
 * TRACE THE SIGIL — the Shrine's precision minigame.
 *
 * The rite's nodes hang in the dark, joined by faint guide-lines; strike
 * them in order before the candle burns down. Wrong node breaks the
 * pattern. On the highest tiers the numerals fade after a breath — the
 * order must be held in the mind.
 */
import React, { useState, useEffect } from 'react'
import { playClick } from '../../audio'

const TUNING = {
  novice:     { nodes: 5,  secs: 10, fade: false },
  apprentice: { nodes: 6,  secs: 9,  fade: false },
  adept:      { nodes: 7,  secs: 9,  fade: false },
  expert:     { nodes: 8,  secs: 8,  fade: true, fadeAfter: 3.0 },
  master:     { nodes: 9,  secs: 8,  fade: true, fadeAfter: 2.2 },
  legendary:  { nodes: 11, secs: 8,  fade: true, fadeAfter: 1.6 },
}
const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']

function layoutNodes(n) {
  // ring layout with jitter — readable but organic
  return Array.from({ length: n }, (_, i) => {
    const a = (i / n) * Math.PI * 2 + Math.random() * 0.5
    const rad = 0.32 + Math.random() * 0.1
    return { x: 0.5 + Math.cos(a) * rad, y: 0.5 + Math.sin(a) * rad * 0.9 }
  })
}

export default function SigilTrace({ difficulty, onDone }) {
  const t = TUNING[difficulty] || TUNING.novice
  const [nodes] = useState(() => layoutNodes(t.nodes))
  const [order] = useState(() => {
    const idx = nodes ? null : null
    const arr = Array.from({ length: t.nodes }, (_, i) => i)
    for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]] }
    return arr  // order[k] = node index struck k-th
  })
  const [next, setNext] = useState(0)
  const [timeLeft, setTimeLeft] = useState(t.secs)
  const [age, setAge] = useState(0)
  const [over, setOver] = useState(null)

  useEffect(() => {
    const start = performance.now()
    const iv = setInterval(() => {
      const el = (performance.now() - start) / 1000
      setAge(el)
      const rem = t.secs - el
      setTimeLeft(Math.max(0, rem))
      if (rem <= 0) {
        clearInterval(iv)
        setOver('burned')
        onDone(nextRef.current / t.nodes * 0.7)
      }
    }, 100)
    return () => clearInterval(iv)
  }, [])
  const nextRef = React.useRef(0)

  function strike(i) {
    if (over) return
    if (order[next] === i) {
      playClick()
      const n = next + 1
      setNext(n); nextRef.current = n
      if (n >= t.nodes) {
        setOver('held')
        // finishing fast burns brightest
        const speedBonus = Math.max(0, Math.min(0.25, (timeLeft / t.secs) * 0.35))
        onDone(Math.min(1, 0.75 + speedBonus))
      }
    } else {
      setOver('broken')
      onDone(next / t.nodes * 0.6)
    }
  }

  const numeralsVisible = !t.fade || age < t.fadeAfter
  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: 10, color: over === 'held' ? 'var(--gold-hi)' : over ? 'var(--red-hi)' : 'var(--muted)' }}>
          {over === 'held' ? 'THE SIGIL HOLDS' : over === 'broken' ? 'THE PATTERN BREAKS' : over === 'burned' ? 'THE CANDLE DIES' : `STRIKE IN ORDER · ${next}/${t.nodes}`}
        </span>
        <span style={{ fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.14em', color: timeLeft < 3 ? 'var(--red-hi)' : 'var(--muted)' }}>{timeLeft.toFixed(1)}s</span>
      </div>

      <div style={{ position: 'relative', height: 230, background: 'radial-gradient(60% 60% at 50% 50%, rgba(42,22,80,.35), rgba(9,6,15,.95))', border: '1px solid rgba(184,151,98,.35)' }}>
        {/* guide lines between consecutive nodes */}
        <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
          {order.slice(0, -1).map((a, k) => {
            const b = order[k + 1]
            return <line key={k} x1={`${nodes[a].x * 100}%`} y1={`${nodes[a].y * 100}%`} x2={`${nodes[b].x * 100}%`} y2={`${nodes[b].y * 100}%`}
              stroke={k < next - 1 ? 'rgba(216,187,132,.7)' : 'rgba(150,110,230,.18)'} strokeWidth="1" />
          })}
        </svg>
        {nodes.map((p, i) => {
          const k = order.indexOf(i)          // when this node is struck
          const struck = k < next
          return (
            <button key={i} onClick={() => strike(i)}
              style={{ position: 'absolute', left: `${p.x * 100}%`, top: `${p.y * 100}%`, transform: 'translate(-50%,-50%) rotate(45deg)', width: 30, height: 30, cursor: over ? 'default' : 'pointer',
                background: struck ? 'linear-gradient(135deg, var(--gold-hi), var(--gold))' : 'rgba(12,7,24,.85)',
                border: `1px solid ${struck ? 'var(--gold-hi)' : 'rgba(150,110,230,.5)'}`,
                boxShadow: struck ? '0 0 12px rgba(216,187,132,.6)' : '0 0 8px rgba(150,110,230,.2)' }}>
              <span style={{ display: 'block', transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontSize: 10, color: struck ? '#0a0710' : numeralsVisible ? 'var(--lavender)' : 'transparent', transition: 'color .6s' }}>
                {ROMAN[k]}
              </span>
            </button>
          )
        })}
      </div>
      <div style={{ textAlign: 'center', fontStyle: 'italic', fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
        {t.fade ? 'The numerals fade after a breath — hold the order in your mind.' : 'Strike the nodes in numbered order before the candle dies.'}
      </div>
    </div>
  )
}
