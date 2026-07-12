/*
 * THE HUNT — the Bestiary's deduction minigame.
 *
 * A beast hides somewhere in the brush. Each probe reads the trail's warmth
 * (distance to the quarry). Corner it before your probes run out — fewer
 * probes spent = a cleaner takedown. Difficulty cuts the probe budget.
 */
import React, { useState } from 'react'
import { playClick } from '../../audio'

const N = 5
const TUNING = {
  novice:     { probes: 9 },
  apprentice: { probes: 7 },
  adept:      { probes: 6 },
  expert:     { probes: 5 },
  master:     { probes: 4 },
  legendary:  { probes: 3 },
}
const WARMTH = [
  { max: 0, label: 'THE QUARRY', color: 'var(--gold-hi)' },
  { max: 1, label: 'FRESH', color: '#e08585' },
  { max: 2, label: 'WARM', color: '#e8a34c' },
  { max: 3, label: 'FAINT', color: '#8fbf9f' },
  { max: 99, label: 'COLD', color: '#6f628c' },
]

export default function HuntGrid({ difficulty, onDone }) {
  const t = TUNING[difficulty] || TUNING.novice
  const [beast] = useState(() => ({ r: Math.floor(Math.random() * N), c: Math.floor(Math.random() * N) }))
  const [probes, setProbes] = useState({})   // "r,c" -> distance
  const [left, setLeft] = useState(t.probes)
  const [over, setOver] = useState(null)     // 'caught' | 'lost'

  function probe(r, c) {
    if (over || probes[`${r},${c}`] !== undefined) return
    playClick()
    const dist = Math.abs(r - beast.r) + Math.abs(c - beast.c)
    const next = { ...probes, [`${r},${c}`]: dist }
    setProbes(next)
    const remaining = left - 1
    setLeft(remaining)
    if (dist === 0) {
      setOver('caught')
      // cleaner catches (more probes to spare) score higher; even a last-probe
      // catch is a solid 0.55.
      const score = 0.55 + 0.45 * (remaining / Math.max(1, t.probes - 1))
      setTimeout(() => onDone(score), 900)
    } else if (remaining <= 0) {
      setOver('lost')
      // never found it — credit only for how close the best probe got
      const best = Math.min(...Object.values(next))
      setTimeout(() => onDone(Math.max(0, 0.3 - best * 0.06)), 900)
    }
  }

  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: 10, color: over === 'caught' ? 'var(--gold-hi)' : over === 'lost' ? 'var(--red-hi)' : 'var(--muted)' }}>
          {over === 'caught' ? 'THE SNARE SINGS' : over === 'lost' ? 'THE TRAIL DIES' : 'READ THE BRUSH'}
        </span>
        <span style={{ fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.14em', color: left <= 1 ? 'var(--red-hi)' : 'var(--muted)' }}>{left} PROBE{left === 1 ? '' : 'S'} LEFT</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${N}, 1fr)`, gap: 4, maxWidth: 330, margin: '0 auto' }}>
        {Array.from({ length: N * N }).map((_, i) => {
          const r = Math.floor(i / N), c = i % N
          const d = probes[`${r},${c}`]
          const isBeast = over && r === beast.r && c === beast.c
          const w = d !== undefined ? WARMTH.find(x => d <= x.max) : null
          return (
            <button key={i} onClick={() => probe(r, c)}
              style={{ aspectRatio: '1', cursor: over || d !== undefined ? 'default' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
                background: isBeast ? 'rgba(216,187,132,.2)' : d !== undefined ? 'rgba(12,7,24,.85)' : 'rgba(24,14,42,.7)',
                border: `1px solid ${isBeast ? 'var(--gold)' : d !== undefined ? 'rgba(150,110,230,.35)' : 'rgba(184,151,98,.2)'}` }}>
              {isBeast
                ? <span style={{ width: 14, height: 14, transform: 'rotate(45deg)', background: 'linear-gradient(135deg, var(--gold-hi), var(--gold))', display: 'inline-block' }} />
                : w && <span style={{ fontFamily: "'Cinzel',serif", fontSize: 7.5, letterSpacing: '.1em', color: w.color }}>{w.label}</span>}
            </button>
          )
        })}
      </div>
      <div style={{ textAlign: 'center', fontStyle: 'italic', fontSize: 12, color: 'var(--muted)', marginTop: 10 }}>
        Each probe reads the trail — FRESH runs a step away, WARM two, FAINT three. Corner it.
      </div>
    </div>
  )
}
