/*
 * KNUCKLE & BONE — the Tavern's dice game.
 *
 * Three bone dice, two rerolls: click dice to HOLD them, throw the rest.
 * Beat the house's total. Difficulty stiffens the house's luck (a flat
 * bonus to its total) — LEGENDARY plays against a house that always seems
 * to roll high. Score maps from the final margin.
 */
import React, { useState } from 'react'
import { playClick } from '../../audio'

const HOUSE_BONUS = { novice: -1, apprentice: 0, adept: 1, expert: 2, master: 3, legendary: 5 }
const d6 = () => 1 + Math.floor(Math.random() * 6)
const PIP = ['', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅']  // die faces are typographic glyphs, not emoji

export default function DiceKnuckle({ difficulty, onDone }) {
  const bonus = HOUSE_BONUS[difficulty] ?? 0
  const [dice, setDice] = useState([d6(), d6(), d6()])
  const [held, setHeld] = useState([false, false, false])
  const [rerolls, setRerolls] = useState(2)
  const [house, setHouse] = useState(null)

  function reroll() {
    if (rerolls <= 0) return
    playClick()
    setDice(d => d.map((v, i) => (held[i] ? v : d6())))
    setRerolls(r => r - 1)
  }

  function stand() {
    playClick()
    // The house rolls 3, rerolls anything under 4 once, then adds its bonus.
    let h = [d6(), d6(), d6()].map(v => (v < 4 ? d6() : v))
    const total = h.reduce((a, b) => a + b, 0) + bonus
    setHouse({ dice: h, total })
    const mine = dice.reduce((a, b) => a + b, 0)
    const margin = mine - total
    // margin -6+ → 0 · tie → .45 · +6 or better → 1
    const score = Math.max(0, Math.min(1, 0.45 + margin / 11))
    setTimeout(() => onDone(score), 1400)
  }

  const mine = dice.reduce((a, b) => a + b, 0)
  return (
    <div style={{ marginTop: 20, textAlign: 'center' }}>
      <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: 10, color: 'var(--muted)' }}>
        {house ? `THE HOUSE SHOWS ${house.total}` : `YOUR HAND · ${mine} — ${rerolls} THROW${rerolls === 1 ? '' : 'S'} LEFT`}
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: 12, margin: '16px 0' }}>
        {dice.map((v, i) => (
          <button key={i} onClick={() => { if (!house && rerolls > 0) { playClick(); setHeld(h => h.map((x, j) => (j === i ? !x : x))) } }}
            style={{ width: 64, height: 64, fontSize: 44, lineHeight: 1, cursor: house ? 'default' : 'pointer',
              color: held[i] ? 'var(--gold-hi)' : 'var(--text-hi)',
              background: 'rgba(12,7,24,.6)', border: `1px solid ${held[i] ? 'var(--gold)' : 'rgba(184,151,98,.35)'}`,
              boxShadow: held[i] ? '0 0 12px rgba(216,187,132,.3)' : 'none' }}>
            {PIP[v]}
          </button>
        ))}
      </div>
      {!house && <div style={{ fontStyle: 'italic', fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>Click a die to hold it between throws.</div>}

      {house ? (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 10, alignItems: 'baseline' }}>
          <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.14em', color: 'var(--muted)' }}>HOUSE</span>
          {house.dice.map((v, i) => <span key={i} style={{ fontSize: 34, color: '#c8a9f5' }}>{PIP[v]}</span>)}
          {bonus !== 0 && <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, color: bonus > 0 ? 'var(--red-hi)' : '#8fbf9f' }}>{bonus > 0 ? `+${bonus}` : bonus}</span>}
          <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 24, color: mine > house.total ? 'var(--gold-hi)' : 'var(--red-hi)' }}>
            {mine > house.total ? 'YOU TAKE THE POT' : mine === house.total ? 'EVEN BONES' : 'THE HOUSE TAKES IT'}
          </span>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn" style={{ flex: 1, padding: '11px 0', fontFamily: "'Cinzel',serif", letterSpacing: '.18em', border: '1px solid rgba(150,110,230,.45)', color: '#cdbfe4', background: 'none', cursor: 'pointer' }}
            disabled={rerolls <= 0} onClick={reroll}>
            THROW AGAIN
          </button>
          <button className="btn btn-primary" style={{ flex: 1, padding: '11px 0', letterSpacing: '.18em' }} onClick={stand}>
            STAND
          </button>
        </div>
      )}
    </div>
  )
}
