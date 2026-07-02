import React, { useState, useEffect } from 'react'
import { getGiftCatalog, giveGift } from '../api/client'
import GameIcon from './GameIcon'

// Gift shop + reaction scene for one hero. Heroes have hidden preferences
// (2 loved gifts, 1 disliked — stable per hero); a loved gift permanently
// raises a stat and lifts morale, and every gift moves their affinity.
// The reaction is the centerpiece: the hero's face, a speech bubble, and
// floating hearts (or a storm cloud) so gifting feels like a moment, not
// a transaction.

const REACTION_STYLE = {
  loved: { color: '#e06080', label: 'LOVED IT', symbol: '♥' },
  neutral: { color: 'var(--gold)', label: 'Appreciated', symbol: '✦' },
  disliked: { color: '#7a8a9a', label: 'Not a fan…', symbol: '…' },
}

export default function GiftModal({ hero, onClose, onGifted }) {
  const [catalog, setCatalog] = useState([])
  const [selected, setSelected] = useState(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getGiftCatalog().then(d => setCatalog(d.gifts || [])).catch(e => setError(e.message))
  }, [])

  async function handleGive() {
    if (!selected || busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await giveGift(hero.id, selected.id)
      setResult(res)
      if (onGifted) onGifted()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const rs = result ? REACTION_STYLE[result.reaction] || REACTION_STYLE.neutral : null

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 1200,
      display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)',
    }} onClick={onClose}>
      <style>{`
        @keyframes gift-float-up {
          0%   { opacity: 0; transform: translateY(10px) scale(0.6); }
          20%  { opacity: 1; }
          100% { opacity: 0; transform: translateY(-90px) scale(1.3); }
        }
        @keyframes gift-pop-in {
          from { opacity: 0; transform: scale(0.8); }
          to   { opacity: 1; transform: scale(1); }
        }
      `}</style>

      <div className="card" onClick={e => e.stopPropagation()} style={{ width: 560, maxWidth: '94vw', maxHeight: '88vh', overflowY: 'auto', padding: '1.5rem' }}>
        {!result ? (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)' }}>
                🎁 A Gift for {hero.name}
              </div>
              <button className="btn" onClick={onClose}>Close</button>
            </div>
            <div className="text-dim" style={{ fontSize: '0.82rem', fontStyle: 'italic', marginBottom: '1rem' }}>
              Every hero secretly loves some gifts and resents others — a loved gift permanently
              strengthens them. Their tastes don't change; remember what lands.
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.7rem' }}>
              {catalog.map(g => {
                const isSel = selected?.id === g.id
                return (
                  <div
                    key={g.id}
                    onClick={() => setSelected(g)}
                    title={g.desc}
                    style={{
                      border: isSel ? '2px solid var(--gold)' : '1px solid var(--border)',
                      borderRadius: 8, padding: '0.7rem 0.5rem', textAlign: 'center', cursor: 'pointer',
                      background: isSel ? 'rgba(201,168,76,0.1)' : 'rgba(0,0,0,0.3)',
                      boxShadow: isSel ? '0 0 12px rgba(201,168,76,0.3)' : 'none',
                      transition: 'border-color 0.15s, box-shadow 0.15s',
                    }}
                  >
                    <GameIcon name={g.icon} size={44} />
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-hi)', marginTop: '0.3rem' }}>{g.name}</div>
                    <div style={{ fontSize: '0.72rem', marginTop: '0.2rem' }}>
                      {g.cost_gold > 0
                        ? <span className="text-gold">{g.cost_gold.toLocaleString()} <GameIcon name="gold_coin" size={11} /></span>
                        : <span style={{ color: '#00ffff' }}>{g.cost_gems} <GameIcon name="gem" size={11} /></span>}
                    </div>
                  </div>
                )
              })}
            </div>

            {selected && (
              <div className="text-dim" style={{ fontSize: '0.8rem', fontStyle: 'italic', marginTop: '0.8rem', textAlign: 'center' }}>
                “{selected.desc}”
              </div>
            )}
            {error && <div className="text-red" style={{ marginTop: '0.6rem', textAlign: 'center', fontSize: '0.85rem' }}>{error}</div>}

            <button
              className="btn btn-gold"
              disabled={!selected || busy}
              onClick={handleGive}
              style={{ width: '100%', marginTop: '1rem', padding: '0.8rem', fontSize: '1rem' }}
            >
              {busy ? 'Wrapping it up…' : selected ? `Give ${selected.name}` : 'Pick a gift'}
            </button>
          </>
        ) : (
          /* ── Reaction scene ── */
          <div style={{ textAlign: 'center', animation: 'gift-pop-in 0.3s ease-out', position: 'relative', padding: '0.5rem 0 0.2rem' }}>
            {/* Floating reaction symbols around the portrait */}
            {[0, 1, 2, 3, 4].map(i => (
              <div key={i} style={{
                position: 'absolute', top: 90, left: `${30 + i * 10}%`,
                fontSize: result.reaction === 'loved' ? '1.4rem' : '1.1rem', color: rs.color,
                animation: `gift-float-up 1.8s ease-out ${i * 0.25}s infinite`,
                pointerEvents: 'none',
              }}>{rs.symbol}</div>
            ))}

            <div style={{ position: 'relative', display: 'inline-block' }}>
              {hero.portrait_path ? (
                <img
                  src={`/${hero.portrait_path}`}
                  alt={hero.name}
                  draggable={false}
                  style={{
                    width: 130, height: 130, borderRadius: '50%', objectFit: 'cover', objectPosition: 'center 15%',
                    border: `3px solid ${rs.color}`, boxShadow: `0 0 25px ${rs.color}66`,
                  }}
                />
              ) : (
                <div style={{ width: 130, height: 130, borderRadius: '50%', background: 'var(--bg-card)', border: `3px solid ${rs.color}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Cinzel, serif' }}>{hero.name[0]}</div>
              )}
              <div style={{ position: 'absolute', bottom: -6, right: -6, background: 'var(--bg-panel)', border: `1px solid ${rs.color}`, borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <GameIcon name={result.gift.icon} size={24} />
              </div>
            </div>

            <div style={{ fontFamily: 'Cinzel, serif', letterSpacing: '0.15em', color: rs.color, marginTop: '0.9rem', fontSize: '0.85rem', textTransform: 'uppercase' }}>
              {rs.label}
            </div>

            {/* Speech bubble */}
            <div style={{
              margin: '0.8rem auto 0', maxWidth: 420, background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border)', borderRadius: 12, padding: '0.9rem 1.2rem',
              fontStyle: 'italic', fontSize: '1.02rem', lineHeight: 1.6, color: 'var(--text-hi)',
            }}>
              “{result.line}”
            </div>

            <div style={{ marginTop: '0.9rem', display: 'flex', justifyContent: 'center', gap: '1.5rem', fontSize: '0.85rem' }}>
              <span style={{ color: result.affinity_delta >= 0 ? 'var(--green)' : 'var(--red)' }}>
                Affinity {result.affinity_delta >= 0 ? '+' : ''}{result.affinity_delta} <span className="text-dim">({result.affinity}/100)</span>
              </span>
              {result.stat_gain && (
                <span className="text-gold" style={{ textTransform: 'capitalize' }}>
                  {result.stat_gain.stat} +{result.stat_gain.amount} (permanent)
                </span>
              )}
            </div>

            <div style={{ marginTop: '1.2rem', display: 'flex', gap: '0.8rem', justifyContent: 'center' }}>
              <button className="btn" onClick={() => { setResult(null); setSelected(null) }}>Give Another</button>
              <button className="btn btn-gold" onClick={onClose}>Done</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
