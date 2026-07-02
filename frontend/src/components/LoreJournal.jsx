import React, { useState, useEffect } from 'react'
import { getLore } from '../api/client'
import GameIcon from './GameIcon'

// Renders as either an inline section (inline=true, for BasePage tab) or
// a modal overlay (default, for any direct call with onClose).
export default function LoreJournal({ onClose, inline = false }) {
  const [entries, setEntries] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getLore().then(res => setEntries(res.entries)).catch(e => setError(e.message))
  }, [])

  const content = (
    <div style={inline ? {} : { background: 'var(--bg-panel)', border: '1px solid var(--gold)', borderRadius: 8, padding: '1.5rem', maxWidth: '90vw', maxHeight: '85vh', overflow: 'auto', minWidth: '500px', width: '600px' }}>
      {!inline && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)' }}><GameIcon name="journal" size={20} /> Lore Journal</div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
      )}

      {error && <div className="text-dim" style={{ color: 'var(--red)' }}>{error}</div>}

      {entries === null && !error && (
        <div className="text-dim" style={{ fontStyle: 'italic' }}>Reading...</div>
      )}

      {entries && entries.length === 0 && (
        <div className="empty-state" style={{ padding: '3rem 2rem' }}>
          <div className="empty-state-icon"><GameIcon name="journal" size={44} /></div>
          <div className="empty-state-title">The Journal Is Blank</div>
          <div className="empty-state-hint">
            A new page is written every 10 floors, drawn from what your team actually fought
            and chose along the way. Clear Floor 10 to unlock the first entry.
          </div>
        </div>
      )}

      {entries && entries.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          {entries.slice().reverse().map(e => (
            <div key={e.milestone} style={{
              background: 'linear-gradient(160deg, rgba(201,168,76,0.05), rgba(0,0,0,0.3))',
              border: '1px solid rgba(201,168,76,0.2)',
              borderLeft: '2px solid var(--gold-dim)',
              borderRadius: 6,
              padding: '1.3rem 1.5rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.7rem' }}>
                <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', fontSize: '1.1rem', letterSpacing: '0.04em' }}>{e.title}</div>
                <div style={{ fontSize: '0.68rem', color: 'var(--gold-dim)', border: '1px solid var(--gold-dim)', borderRadius: 999, padding: '0.1rem 0.6rem', letterSpacing: '0.1em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
                  Floor {e.milestone}
                </div>
              </div>
              <div style={{ lineHeight: 1.75, fontStyle: 'italic', color: 'var(--text-hi)', fontSize: '1.02rem' }}>{e.text}</div>
              <div style={{ textAlign: 'center', color: 'var(--gold-dim)', marginTop: '0.9rem', fontSize: '0.9rem' }}>❦</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  if (inline) return content

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()}>{content}</div>
    </div>
  )
}
