/*
 * THE COMMANDER'S TABLE — a pawn-duel board game vs a hero (Training Grounds).
 *
 * Hexapawn family: pawns step forward into empty squares or capture
 * diagonally. Win by reaching the far rank, taking every enemy stone, or
 * leaving the opponent no legal move. Small boards make full minimax cheap —
 * difficulty sets board size AND how often the hero blunders (LEGENDARY
 * never blunders: perfect play on 5x5; beating it is genuinely brutal).
 *
 * Score: win = 1.0; a loss still earns partial credit for stones taken.
 */
import React, { useState, useMemo } from 'react'
import { playClick } from '../../audio'

const TUNING = {
  novice:     { n: 3, blunder: 0.55 },
  apprentice: { n: 3, blunder: 0.35 },
  adept:      { n: 4, blunder: 0.22 },
  expert:     { n: 4, blunder: 0.10 },
  master:     { n: 5, blunder: 0.04 },
  legendary:  { n: 5, blunder: 0.0 },
}

// board: n×n array, 1 = manager (moves "up", row--), -1 = hero AI (row++), 0 empty
function initBoard(n) {
  const b = Array.from({ length: n }, () => Array(n).fill(0))
  for (let c = 0; c < n; c++) { b[n - 1][c] = 1; b[0][c] = -1 }
  return b
}
function legalMoves(b, side) {
  const n = b.length, dir = side === 1 ? -1 : 1, out = []
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
    if (b[r][c] !== side) continue
    const nr = r + dir
    if (nr < 0 || nr >= n) continue
    if (b[nr][c] === 0) out.push({ r, c, nr, nc: c })
    for (const dc of [-1, 1]) {
      const nc = c + dc
      if (nc >= 0 && nc < n && b[nr][nc] === -side) out.push({ r, c, nr, nc })
    }
  }
  return out
}
function applyMove(b, m, side) {
  const nb = b.map(row => [...row])
  nb[m.r][m.c] = 0
  nb[m.nr][m.nc] = side
  return nb
}
// terminal check for the side ABOUT to move; returns +1 manager won, -1 hero won, null ongoing
function winner(b, toMove) {
  const n = b.length
  if (b[0].some(v => v === 1)) return 1        // manager reached far rank
  if (b[n - 1].some(v => v === -1)) return -1  // hero reached near rank
  const managerAlive = b.flat().some(v => v === 1)
  const heroAlive = b.flat().some(v => v === -1)
  if (!managerAlive) return -1
  if (!heroAlive) return 1
  if (legalMoves(b, toMove).length === 0) return -toMove  // stuck = loss
  return null
}
// full-depth minimax with memo — boards are tiny (≤5x5)
function minimax(b, toMove, memo) {
  const key = toMove + ':' + b.flat().join('')
  if (memo.has(key)) return memo.get(key)
  const w = winner(b, toMove)
  if (w !== null) { memo.set(key, w * 100); return w * 100 }
  let best = toMove === 1 ? -Infinity : Infinity
  for (const m of legalMoves(b, toMove)) {
    const v = minimax(applyMove(b, m, toMove), -toMove, memo)
    if (toMove === 1) best = Math.max(best, v)
    else best = Math.min(best, v)
  }
  memo.set(key, best)
  return best
}

export default function StrategyDuel({ difficulty, onDone, opponentName = 'the Leader', aptitude = 50 }) {
  const base = TUNING[difficulty] || TUNING.novice
  // The tier sets the STAKES; the hero's Leadership aptitude sets how well
  // they actually play at them. A born tactician (apt 140) blunders half as
  // often as the tier says; a farmhand blunders more — and even at LEGENDARY
  // (perfect play), a dull mind still cracks occasionally under the weight,
  // while a brilliant one truly never does. Heroes are not the same.
  const aptScale = Math.max(0.4, 1.15 - (aptitude || 50) / 200)
  const legendaryCrack = base.blunder === 0 && (aptitude || 50) < 60 ? (60 - (aptitude || 50)) / 500 : 0
  const t = { n: base.n, blunder: Math.min(0.9, base.blunder * aptScale + legendaryCrack) }
  const [board, setBoard] = useState(() => initBoard(t.n))
  const [sel, setSel] = useState(null)
  const [turn, setTurn] = useState(1)          // 1 = manager, -1 = hero
  const [status, setStatus] = useState('Your move — stones advance, take on the diagonal.')
  const memo = useMemo(() => new Map(), [])
  const heroStart = t.n

  function finish(b) {
    const heroLeft = b.flat().filter(v => v === -1).length
    const w = winner(b, 1) ?? winner(b, -1)
    const taken = heroStart - heroLeft
    const score = w === 1 ? 1.0 : Math.min(0.45, (taken / heroStart) * 0.45)
    setTimeout(() => onDone(score), 900)
  }

  function heroMove(b) {
    const moves = legalMoves(b, -1)
    if (!moves.length) { setStatus(`${opponentName} has no move — the table is yours.`); finish(b); return }
    let pick
    if (Math.random() < t.blunder) {
      pick = moves[Math.floor(Math.random() * moves.length)]
    } else {
      let bestV = Infinity
      for (const m of moves) {
        const v = minimax(applyMove(b, m, -1), 1, memo)
        if (v < bestV) { bestV = v; pick = m }
      }
    }
    const nb = applyMove(b, pick, -1)
    setBoard(nb)
    const w = winner(nb, 1)
    if (w !== null) {
      setStatus(w === 1 ? 'Victory — the board is yours.' : `${opponentName} takes the game.`)
      finish(nb)
    } else {
      setTurn(1)
      setStatus('Your move.')
    }
  }

  function clickCell(r, c) {
    if (turn !== 1) return
    if (board[r][c] === 1) { playClick(); setSel({ r, c }); return }
    if (!sel) return
    const mv = legalMoves(board, 1).find(m => m.r === sel.r && m.c === sel.c && m.nr === r && m.nc === c)
    if (!mv) return
    playClick()
    const nb = applyMove(board, mv, 1)
    setBoard(nb); setSel(null)
    const w = winner(nb, -1)
    if (w !== null) {
      setStatus(w === 1 ? 'Victory — the board is yours.' : `${opponentName} takes the game.`)
      finish(nb)
      return
    }
    setTurn(-1)
    setStatus(`${opponentName} considers…`)
    setTimeout(() => heroMove(nb), 450)
  }

  const targets = sel ? legalMoves(board, 1).filter(m => m.r === sel.r && m.c === sel.c) : []
  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${t.n}, 1fr)`, gap: 4, maxWidth: 340, margin: '0 auto' }}>
        {board.map((row, r) => row.map((v, c) => {
          const isSel = sel && sel.r === r && sel.c === c
          const isTarget = targets.some(m => m.nr === r && m.nc === c)
          return (
            <button key={`${r}-${c}`} onClick={() => clickCell(r, c)}
              style={{ aspectRatio: '1', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
                background: (r + c) % 2 ? 'rgba(24,14,42,.85)' : 'rgba(12,7,24,.85)',
                border: isSel ? '1px solid var(--gold-hi)' : isTarget ? '1px solid var(--lavender)' : '1px solid rgba(184,151,98,.2)',
                boxShadow: isTarget ? 'inset 0 0 12px rgba(150,110,230,.35)' : 'none' }}>
              {v !== 0 && (
                <span style={{ width: '52%', height: '52%', transform: 'rotate(45deg)', display: 'inline-block',
                  background: v === 1 ? 'linear-gradient(135deg, var(--gold-hi), var(--gold))' : 'linear-gradient(135deg, #8b46d6, #4a2a80)',
                  boxShadow: v === 1 ? '0 0 10px rgba(216,187,132,.5)' : '0 0 10px rgba(139,70,214,.5)' }} />
              )}
            </button>
          )
        }))}
      </div>
      <div style={{ textAlign: 'center', fontStyle: 'italic', fontSize: 13, color: 'var(--muted)', marginTop: 12 }}>{status}</div>
    </div>
  )
}
