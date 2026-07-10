/*
 * STAKES BANNER — one strip on every combat entry point telling the player
 * what they stand to lose before they commit (Claude-Design mockup
 * "Combat Stakes Banners"). Three risk tiers, one icon each:
 *   souls   — Tower floors: permadeath
 *   echo    — arena / tournament / guild boss / sparring: nothing is lost
 *   capture — raids: lose and a hero is taken
 * `compact` renders the thin pinned strip for the top of an entry gate.
 */
import React from 'react'

const VARIANTS = {
  souls: {
    glyph: '☠',
    color: '#e8738a',
    dim: 'rgba(192,64,64,.5)',
    stripe: 'rgba(192,64,64,.07)',
    bg: 'linear-gradient(90deg, rgba(60,16,24,.55), rgba(20,8,14,.65))',
    title: 'SOULS AT RISK',
    sub: 'Fall here and your heroes are lost for good. The Tower does not return what it takes.',
    tag: 'PERMADEATH',
    compactNote: 'defeat is permanent on this floor',
  },
  echo: {
    glyph: '✦',
    color: '#7fd9a8',
    dim: 'rgba(74,154,106,.5)',
    stripe: 'rgba(74,154,106,.06)',
    bg: 'linear-gradient(90deg, rgba(14,42,30,.5), rgba(8,18,14,.6))',
    title: 'ECHO BATTLE',
    titleSuffix: ' — NOTHING IS LOST',
    sub: 'A remembered fight. Win or fall, every hero walks away unharmed.',
    tag: 'SAFE',
    compactNote: 'snapshot teams — no hero truly dies here',
  },
  capture: {
    glyph: '⛓',
    color: '#ffd88a',
    dim: 'rgba(216,187,132,.55)',
    stripe: 'rgba(216,187,132,.07)',
    bg: 'linear-gradient(90deg, rgba(58,44,16,.5), rgba(22,16,8,.6))',
    title: 'CAPTURE AT STAKE',
    sub: 'Lose the raid and a hero is taken — held by the victor until you win them back.',
    tag: 'RANSOM',
    compactNote: 'lose and a hero may be taken prisoner',
  },
}

export default function StakesBanner({ variant = 'souls', compact = false, note, style }) {
  const v = VARIANTS[variant] || VARIANTS.souls
  const stripes = `repeating-linear-gradient(115deg, ${v.stripe} 0 2px, transparent 2px 14px)`

  if (compact) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, padding: '6px 14px',
        border: `1px solid ${v.dim}`, background: `${stripes}, ${v.bg}`,
        ...style,
      }}>
        <span style={{ width: 16, height: 16, transform: 'rotate(45deg)', border: `1px solid ${v.dim}`, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flex: 'none', background: 'rgba(8,6,14,.6)' }}>
          <span style={{ transform: 'rotate(-45deg)', fontSize: 9, color: v.color, lineHeight: 1 }}>{v.glyph}</span>
        </span>
        <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.22em', fontSize: '0.6rem', color: v.color }}>{v.title}</span>
        <span style={{ fontStyle: 'italic', fontSize: '0.78rem', color: 'var(--text-dim)' }}>— {note || v.compactNote}</span>
        <span style={{ flex: 1 }} />
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: v.color, boxShadow: `0 0 7px ${v.color}`, flex: 'none' }} />
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16, padding: '14px 18px',
      border: `1px solid ${v.dim}`, background: `${stripes}, ${v.bg}`,
      ...style,
    }}>
      <span style={{ width: 34, height: 34, transform: 'rotate(45deg)', border: `1px solid ${v.color}`, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flex: 'none', margin: '0 6px', background: 'rgba(8,6,14,.6)', boxShadow: `0 0 14px ${v.dim}` }}>
        <span style={{ transform: 'rotate(-45deg)', fontSize: 15, color: v.color, lineHeight: 1 }}>{v.glyph}</span>
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.24em', fontSize: '0.82rem', color: v.color }}>
          {v.title}{v.titleSuffix && <span style={{ color: 'var(--text-dim)', fontWeight: 500 }}>{v.titleSuffix}</span>}
        </div>
        <div style={{ fontStyle: 'italic', fontSize: '0.88rem', color: 'var(--text-dim)', marginTop: 2 }}>{note || v.sub}</div>
      </div>
      <span style={{ display: 'flex', alignItems: 'center', gap: 7, flex: 'none' }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: v.color, boxShadow: `0 0 7px ${v.color}` }} />
        <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: '0.58rem', color: v.color }}>{v.tag}</span>
      </span>
    </div>
  )
}
