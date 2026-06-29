import React, { useState, useEffect } from 'react'
import { listHeroes, revealHeroTalent, buyBaseUpgrade } from '../api/client'

// Talent Observatory: a paid, on-demand Talent reveal, separate from
// Archive's free per-level aptitude drip (see backend/services/
// level_service.py for why these two don't share state). The level of
// detail (tier/range/exact) is gated by this facility's own level.
export default function TalentObservatory({ upgrade, gold, onGoldChange, onUpgrade }) {
  const [heroes, setHeroes] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState(null)
  const [revealing, setRevealing] = useState(false)
  const [msg, setMsg] = useState(null)

  useEffect(() => { refresh() }, [])

  async function refresh() {
    setLoading(true)
    try {
      const all = await listHeroes(true)
      setHeroes(all)
    } catch (e) {
      setMsg(e.message)
    } finally {
      setLoading(false)
    }
  }

  const level = upgrade?.level || 0
  const maxLevel = upgrade?.max_level || 3
  const selected = heroes.find(h => h.id === selectedId)
  const cost = selected ? (selected.current_star || selected.birth_star) * 500 : 0

  async function handleReveal() {
    if (!selected) return
    setRevealing(true)
    setMsg(null)
    try {
      const res = await revealHeroTalent(selected.id)
      setHeroes(prev => prev.map(h => h.id === selected.id ? { ...h, talent_reveal: res.talent_reveal } : h))
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setMsg(e.message)
    } finally {
      setRevealing(false)
    }
  }

  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <h3 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', margin: 0 }}>
          Talent Observatory <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>(Lv.{level}/{maxLevel})</span>
        </h3>
        {level < maxLevel && (
          <button className="btn" style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }} onClick={onUpgrade}>
            Upgrade ({upgrade?.next_cost ?? '?'}g)
          </button>
        )}
      </div>
      <div className="text-dim text-sm" style={{ marginBottom: '1rem', lineHeight: 1.5 }}>
        Pay gold to reveal a hero's hidden Talent right now, instead of waiting on it to surface naturally as they level.{' '}
        {level <= 1 && 'At this level, you only learn a vague tier (Poor/Average/Good/Exceptional).'}
        {level === 2 && 'At this level, you learn a numeric range.'}
        {level >= 3 && 'At this level, you learn the exact number.'}
      </div>

      {msg && <div style={{ color: '#f87', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{msg}</div>}

      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 280px', maxHeight: '320px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {loading && <div className="text-dim text-sm">Loading heroes...</div>}
          {!loading && heroes.length === 0 && <div className="text-dim text-sm">No heroes yet.</div>}
          {heroes.map(h => (
            <button
              key={h.id}
              onClick={() => setSelectedId(h.id)}
              className={`btn ${selectedId === h.id ? 'btn-gold' : ''}`}
              style={{ textAlign: 'left', padding: '0.5rem 0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <span>{h.name} <span className="text-dim" style={{ fontSize: '0.78rem' }}>Lv.{h.level} {h.hero_class}</span></span>
              {h.talent_reveal
                ? <span style={{ fontSize: '0.78rem', color: 'var(--gold)' }}>{h.talent_reveal}</span>
                : <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Unrevealed</span>}
            </button>
          ))}
        </div>

        <div style={{ flex: '1 1 220px' }}>
          {!selected && <div className="text-dim text-sm">Select a hero to reveal their Talent.</div>}
          {selected && selected.talent_reveal && (
            <div>
              <div className="text-hi" style={{ fontFamily: 'Cinzel, serif', marginBottom: '0.5rem' }}>{selected.name}</div>
              <div style={{ fontSize: '1.1rem', color: 'var(--gold)' }}>{selected.talent_reveal}</div>
              <div className="text-dim text-sm" style={{ marginTop: '0.5rem' }}>Already revealed — frozen at the Observatory's level when revealed.</div>
            </div>
          )}
          {selected && !selected.talent_reveal && (
            <div>
              <div className="text-hi" style={{ fontFamily: 'Cinzel, serif', marginBottom: '0.5rem' }}>{selected.name}</div>
              <div className="text-dim text-sm" style={{ marginBottom: '0.75rem' }}>Cost to reveal: <span className="text-gold">{cost}g</span></div>
              <button className="btn btn-gold" disabled={revealing || gold < cost} onClick={handleReveal}>
                {revealing ? 'Awakening...' : 'Awaken'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
