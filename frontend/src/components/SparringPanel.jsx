import React, { useState } from 'react'
import { sparHeroes } from '../api/client'

// Training Grounds sparring — pick two assigned heroes; the backend
// auto-detects Peer (similar level: both gain XP + likely skill-ups) vs
// Mentorship (8+ level gap: mentor pours XP into the student). Rendered
// inline inside the Training Grounds facility card.
const MENTOR_GAP = 8

export default function SparringPanel({ assignedHeroes = [], onSparred }) {
  const [aId, setAId] = useState('')
  const [bId, setBId] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)

  const a = assignedHeroes.find(h => String(h.id) === aId)
  const b = assignedHeroes.find(h => String(h.id) === bId)
  const gap = a && b ? Math.abs((a.level || 1) - (b.level || 1)) : null
  const predictedMode = gap == null ? null : gap >= MENTOR_GAP ? 'Mentorship' : gap <= 5 ? 'Peer Sparring' : 'mismatch'

  async function handleSpar() {
    if (!a || !b) return
    setBusy(true)
    setMsg(null)
    try {
      const res = await sparHeroes(a.id, b.id)
      setMsg({ lines: res.messages || [], err: false })
      if (onSparred) onSparred()
    } catch (e) {
      setMsg({ lines: [e.message], err: true })
    } finally {
      setBusy(false)
    }
  }

  if (assignedHeroes.length < 2) {
    return (
      <div style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: 6 }}>
        <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif', marginBottom: '0.3rem' }}>⚔ Sparring</div>
        <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>
          Assign at least two heroes to the Training Grounds to spar them together.
        </div>
      </div>
    )
  }

  return (
    <div style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: 6 }}>
      <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif', marginBottom: '0.4rem' }}>⚔ Sparring</div>
      <div className="text-dim text-sm" style={{ marginBottom: '0.5rem' }}>
        Similar levels → <b>Peer Sparring</b> (both gain XP + likely a skill level). An {MENTOR_GAP}+ level gap → <b>Mentorship</b> (the veteran pours XP into the student and sharpens a skill; a career mentor is remembered even in death).
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <select className="input" value={aId} onChange={e => setAId(e.target.value)} style={{ flex: 1, minWidth: 130, fontSize: '0.85rem' }}>
          <option value="">First hero…</option>
          {assignedHeroes.map(h => <option key={h.id} value={h.id} disabled={String(h.id) === bId}>{h.name} (Lv.{h.level})</option>)}
        </select>
        <span className="text-dim">vs</span>
        <select className="input" value={bId} onChange={e => setBId(e.target.value)} style={{ flex: 1, minWidth: 130, fontSize: '0.85rem' }}>
          <option value="">Second hero…</option>
          {assignedHeroes.map(h => <option key={h.id} value={h.id} disabled={String(h.id) === aId}>{h.name} (Lv.{h.level})</option>)}
        </select>
      </div>
      {predictedMode && predictedMode !== 'mismatch' && (
        <div className="text-dim text-sm" style={{ marginTop: '0.4rem' }}>
          Level gap {gap} → <span style={{ color: 'var(--gold)' }}>{predictedMode}</span>
        </div>
      )}
      {predictedMode === 'mismatch' && (
        <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', color: '#f0a848' }}>
          Gap {gap} is too wide for peers but not wide enough to mentor (needs {MENTOR_GAP}+). Pick a closer or further-apart pair.
        </div>
      )}
      <button
        className="btn btn-gold"
        disabled={busy || !a || !b || predictedMode === 'mismatch'}
        onClick={handleSpar}
        style={{ marginTop: '0.6rem', fontSize: '0.85rem' }}
      >
        {busy ? 'Sparring…' : 'Begin Sparring'}
      </button>
      {msg && (
        <div style={{ marginTop: '0.6rem', fontSize: '0.85rem', color: msg.err ? '#f87' : '#8e8', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
          {msg.lines.map((l, i) => <div key={i}>{l}</div>)}
        </div>
      )}
    </div>
  )
}
