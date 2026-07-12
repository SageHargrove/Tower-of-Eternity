/*
 * READ THE GLASS — the Mirror of Fate's recognition minigame.
 *
 * The glass flashes a handful of visions, then clouds — and asks what you
 * truly saw among the false memories. Recognition under pressure: rounds
 * multiply, flashes shorten, and the liar-options grow with difficulty.
 * Score = correct identifications across all rounds.
 */
import React, { useState, useEffect } from 'react'
import { playClick } from '../../audio'

const TUNING = {
  novice:     { rounds: 2, show: 3, options: 6, flash: 1200 },
  apprentice: { rounds: 2, show: 3, options: 7, flash: 950 },
  adept:      { rounds: 2, show: 4, options: 8, flash: 800 },
  expert:     { rounds: 3, show: 4, options: 8, flash: 600 },
  master:     { rounds: 3, show: 4, options: 9, flash: 430 },
  legendary:  { rounds: 3, show: 5, options: 10, flash: 300 },
}
// Vision glyphs — typographic, in-style, visually distinct.
const GLYPHS = ['✦', '◆', '▲', '●', '◇', '★', '☽', '♛', '✚', '✟', '▣', '♦', '☆', '‡', '§', 'Ω']

function pick(arr, n) {
  const pool = [...arr]
  const out = []
  while (out.length < n && pool.length) out.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0])
  return out
}

export default function MirrorGlimpse({ difficulty, onDone }) {
  const t = TUNING[difficulty] || TUNING.novice
  const [round, setRound] = useState(0)
  const [phase, setPhase] = useState('flash')   // flash -> ask
  const [visions, setVisions] = useState(() => pick(GLYPHS, t.show))
  const [options, setOptions] = useState([])
  const [chosen, setChosen] = useState([])
  const [tally, setTally] = useState({ right: 0, total: 0 })

  useEffect(() => {
    if (phase !== 'flash') return
    const timer = setTimeout(() => {
      setOptions(pick([...visions, ...pick(GLYPHS.filter(g => !visions.includes(g)), t.options - t.show)], t.options))
      setPhase('ask')
    }, t.flash)
    return () => clearTimeout(timer)
  }, [phase, visions])

  function choose(g) {
    if (phase !== 'ask' || chosen.includes(g)) return
    playClick()
    const next = [...chosen, g]
    setChosen(next)
    if (next.length >= t.show) {
      const right = next.filter(x => visions.includes(x)).length
      const nt = { right: tally.right + right, total: tally.total + t.show }
      setTally(nt)
      if (round + 1 >= t.rounds) {
        setTimeout(() => onDone(nt.right / nt.total), 700)
      } else {
        setTimeout(() => {
          setRound(r => r + 1)
          setVisions(pick(GLYPHS, t.show))
          setChosen([])
          setPhase('flash')
        }, 700)
      }
    }
  }

  return (
    <div style={{ marginTop: 20, textAlign: 'center' }}>
      <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: 10, color: 'var(--muted)' }}>
        READING {round + 1} OF {t.rounds} · {phase === 'flash' ? 'THE GLASS SHOWS…' : `WHAT DID YOU SEE? · ${chosen.length}/${t.show}`}
      </div>

      {/* the glass */}
      <div style={{ minHeight: 96, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 18, margin: '14px 0',
        border: '1px solid rgba(150,110,230,.4)', background: 'radial-gradient(60% 80% at 50% 50%, rgba(42,22,80,.5), rgba(9,6,15,.95))' }}>
        {phase === 'flash'
          ? visions.map((g, i) => <span key={i} style={{ fontSize: 38, color: 'var(--lavender)', textShadow: '0 0 16px rgba(150,110,230,.8)' }}>{g}</span>)
          : <span style={{ fontStyle: 'italic', fontSize: 14, color: 'var(--muted)' }}>The glass clouds. Name what it showed you.</span>}
      </div>

      {phase === 'ask' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8, maxWidth: 380, margin: '0 auto' }}>
          {options.map(g => {
            const isChosen = chosen.includes(g)
            const wasVision = visions.includes(g)
            return (
              <button key={g} onClick={() => choose(g)}
                style={{ aspectRatio: '1', fontSize: 26, cursor: isChosen ? 'default' : 'pointer',
                  color: isChosen ? (wasVision ? 'var(--gold-hi)' : 'var(--red-hi)') : 'var(--text-hi)',
                  background: 'rgba(12,7,24,.7)',
                  border: `1px solid ${isChosen ? (wasVision ? 'var(--gold)' : 'var(--red)') : 'rgba(184,151,98,.3)'}` }}>
                {g}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
