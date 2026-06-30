import React, { useState, useEffect } from 'react'
import { getLore } from '../api/client'

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
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)' }}>📖 Lore Journal</div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
      )}

      {error && <div className="text-dim" style={{ color: 'var(--red)' }}>{error}</div>}

      {entries === null && !error && (
        <div className="text-dim" style={{ fontStyle: 'italic' }}>Reading...</div>
      )}

      {entries && entries.length === 0 && (
        <div className="text-dim" style={{ fontStyle: 'italic' }}>
          Nothing's been written yet. Clear floor 10 to unlock the first page.
        </div>
      )}

      {entries && entries.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {entries.slice().reverse().map(e => (
            <div key={e.milestone} style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
                <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', fontSize: '1rem' }}>{e.title}</div>
                <div className="text-dim" style={{ fontSize: '0.7rem' }}>Floor {e.milestone}</div>
              </div>
              <div style={{ lineHeight: 1.6, fontStyle: 'italic', color: 'var(--text-hi)' }}>{e.text}</div>
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
