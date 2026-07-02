import React from 'react'

// Inline SVGs from assets/icons (lucide), colored for the hero-card action
// chips. Inline (not <img>) so strokes can be colored per-path: the gift's
// box reads soft gold/bronze with a crimson ribbon; the heart follows
// currentColor so the button's own state colors it.

export function GiftIcon({ size = 14 }) {
  const box = '#c9a84c'      // soft gold/bronze
  const ribbon = '#d4364e'   // crimson
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
      fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      style={{ display: 'inline-block', verticalAlign: 'text-bottom' }}>
      <path d="M20 11v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8" stroke={box} />
      <rect x="3" y="7" width="18" height="4" rx="1" stroke={box} />
      <path d="M12 7v14" stroke={ribbon} />
      <path d="M7.5 7a1 1 0 0 1 0-5A4.8 8 0 0 1 12 7a4.8 8 0 0 1 4.5-5 1 1 0 0 1 0 5" stroke={ribbon} />
    </svg>
  )
}

export function HeartIcon({ size = 14, filled = false }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
      fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round"
      style={{ display: 'inline-block', verticalAlign: 'text-bottom' }}>
      <path d="M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5" />
    </svg>
  )
}
