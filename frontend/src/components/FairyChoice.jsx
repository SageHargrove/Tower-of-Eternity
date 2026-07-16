import React, { useState } from 'react'
import { chooseFairy } from '../api/client'

// First thing a brand-new profile sees: pick which fairy guide accompanies
// them through the tutorial and beyond. Shown before TutorialOverlay when the
// profile has no fairy_gender chosen yet (App.jsx gate).
export default function FairyChoice({ onChosen }) {
  const [busy, setBusy] = useState(false)
  const [hover, setHover] = useState(null)

  const pick = async (gender) => {
    if (busy) return
    setBusy(true)
    try {
      await chooseFairy(gender)
      onChosen(gender)
    } catch {
      setBusy(false)
    }
  }

  const options = [
    { g: 'female', label: 'Sylph', hint: 'the violet-eyed wisp' },
    { g: 'male', label: 'Puck', hint: 'the teal-eyed sprite' },
  ]

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9000,
      background: 'radial-gradient(ellipse at center, #14101f 0%, #06040b 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', gap: '2rem', padding: '2rem',
    }}>
      <div style={{ textAlign: 'center', maxWidth: 620 }}>
        <h1 style={{ color: '#e8e0ff', fontSize: '1.9rem', margin: '0 0 .5rem', letterSpacing: '.02em' }}>
          A Guide Awaits
        </h1>
        <p style={{ color: '#9a8fb8', fontSize: '1.05rem', lineHeight: 1.5, margin: 0 }}>
          Two spirits linger at the foot of the Hollow Spire. One will follow you
          into the climb. Choose who guides you.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '2.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        {options.map(({ g, label, hint }) => (
          <button
            key={g}
            disabled={busy}
            onClick={() => pick(g)}
            onMouseEnter={() => setHover(g)}
            onMouseLeave={() => setHover(null)}
            style={{
              background: 'transparent', border: 'none', cursor: busy ? 'default' : 'pointer',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '.75rem',
              transform: hover === g ? 'translateY(-6px) scale(1.03)' : 'none',
              transition: 'transform .18s ease', opacity: busy && hover !== g ? 0.5 : 1,
            }}
          >
            <div style={{
              width: 230, height: 300, borderRadius: 16, overflow: 'hidden',
              background: 'rgba(20,16,32,0.6)',
              border: `2px solid ${hover === g ? '#a98bff' : 'rgba(120,100,180,0.35)'}`,
              boxShadow: hover === g ? '0 0 32px rgba(150,110,255,0.45)' : '0 0 12px rgba(0,0,0,0.5)',
              transition: 'border-color .18s, box-shadow .18s',
            }}>
              <img
                src={`/static/portraits/fairy/${g}.png`}
                alt={label}
                style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top center' }}
              />
            </div>
            <div style={{ color: '#e8e0ff', fontSize: '1.25rem', fontWeight: 600 }}>{label}</div>
            <div style={{ color: '#8a7fa8', fontSize: '.85rem' }}>{hint}</div>
          </button>
        ))}
      </div>
      <p style={{ color: '#5c5470', fontSize: '.8rem', margin: 0 }}>This choice is only cosmetic.</p>
    </div>
  )
}
