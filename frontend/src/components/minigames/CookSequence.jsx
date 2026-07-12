/*
 * SEASON THE POT — the Dining Hall's memory minigame.
 *
 * The recipe flashes a sequence of seasoning glyphs; reproduce it in order.
 * Difficulty lengthens the sequence and quickens the flash. Score = correct
 * steps / total (one wrong tap ends the attempt — kitchens are unforgiving).
 */
import React, { useState, useEffect, useRef } from 'react'
import { playClick } from '../../audio'

const TUNING = {
  novice:     { len: 4,  flash: 700 },
  apprentice: { len: 5,  flash: 600 },
  adept:      { len: 6,  flash: 500 },
  expert:     { len: 8,  flash: 420 },
  master:     { len: 10, flash: 340 },
  legendary:  { len: 13, flash: 260 },
}
// The four "seasonings" — drawn glyphs, in-style.
const GLYPHS = [
  { key: 'salt',   label: 'SALT',   glyph: '◆', color: 'var(--gold-hi)' },
  { key: 'herb',   label: 'HERB',   glyph: '✦', color: '#8fbf9f' },
  { key: 'ember',  label: 'EMBER',  glyph: '▲', color: '#e8a34c' },
  { key: 'essence',label: 'ESSENCE',glyph: '●', color: 'var(--lavender)' },
]

export default function CookSequence({ difficulty, onDone }) {
  const t = TUNING[difficulty] || TUNING.novice
  const [seq] = useState(() => Array.from({ length: t.len }, () => GLYPHS[Math.floor(Math.random() * 4)].key))
  const [shown, setShown] = useState(-1)     // index currently flashing; -1 pre, seq.len = done showing
  const [inputIdx, setInputIdx] = useState(0)
  const [phase, setPhase] = useState('watch') // watch -> repeat -> over
  const failedAt = useRef(null)

  useEffect(() => {
    let i = 0
    setShown(0)
    const iv = setInterval(() => {
      i += 1
      if (i >= seq.length) {
        clearInterval(iv)
        setShown(-1)
        setPhase('repeat')
      } else {
        setShown(i)
      }
    }, t.flash)
    return () => clearInterval(iv)
  }, [])

  function tap(key) {
    if (phase !== 'repeat') return
    playClick()
    if (key === seq[inputIdx]) {
      const next = inputIdx + 1
      setInputIdx(next)
      if (next >= seq.length) {
        setPhase('over')
        setTimeout(() => onDone(1.0), 500)
      }
    } else {
      failedAt.current = inputIdx
      setPhase('over')
      // one wrong move ends it — credit for steps landed before the slip
      setTimeout(() => onDone(inputIdx / seq.length * 0.8), 500)
    }
  }

  const current = shown >= 0 ? GLYPHS.find(g => g.key === seq[shown]) : null
  return (
    <div style={{ marginTop: 20, textAlign: 'center' }}>
      <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: 10, color: 'var(--muted)' }}>
        {phase === 'watch' ? `WATCH THE RECIPE · ${t.len} STEPS` : phase === 'repeat' ? `SEASON IN ORDER · ${inputIdx}/${seq.length}` : failedAt.current != null ? 'THE FLAVOR TURNS' : 'PERFECTLY SEASONED'}
      </div>

      {/* the flash pane */}
      <div style={{ height: 92, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '14px 0', border: '1px solid rgba(184,151,98,.3)', background: 'rgba(0,0,0,.4)' }}>
        {phase === 'watch' && current && (
          <span key={shown} style={{ fontSize: 44, color: current.color, animation: 'page-in .18s ease-out' }}>{current.glyph}</span>
        )}
        {phase === 'repeat' && (
          <div style={{ display: 'flex', gap: 6 }}>
            {seq.map((_, i) => (
              <span key={i} style={{ width: 10, height: 10, transform: 'rotate(45deg)', display: 'inline-block',
                background: i < inputIdx ? 'var(--gold-hi)' : 'transparent', border: '1px solid rgba(184,151,98,.45)' }} />
            ))}
          </div>
        )}
        {phase === 'over' && (
          <span style={{ fontStyle: 'italic', color: failedAt.current != null ? '#d98a8a' : '#a8dfb8', fontSize: 15 }}>
            {failedAt.current != null ? 'A hand slips over the pot…' : 'The kitchen falls silent in respect.'}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
        {GLYPHS.map(g => (
          <button key={g.key} onClick={() => tap(g.key)} disabled={phase !== 'repeat'}
            style={{ padding: '14px 0', cursor: phase === 'repeat' ? 'pointer' : 'default', background: 'rgba(12,7,24,.6)', border: '1px solid rgba(184,151,98,.35)', opacity: phase === 'repeat' ? 1 : 0.55 }}>
            <div style={{ fontSize: 22, color: g.color }}>{g.glyph}</div>
            <div style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.2em', color: 'var(--muted)', marginTop: 4 }}>{g.label}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
