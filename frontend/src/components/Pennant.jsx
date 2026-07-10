import React from 'react'

/*
 * Pennant — the Illuminated banner renderer (Banner Studio mockup model):
 * a hanging rod, a cloth of any color cut to a tail shape (mask_<cut>.svg),
 * a metal FRAME trim by earned tier, and a sigil glyph / emblem PNG / painted
 * layer on the cloth. Shared by the Banner Studio preview and TeamBanner so
 * a banner always looks the same everywhere it flies.
 *
 * Legacy banners (no cloth/cut saved) should keep using the old PNG path —
 * callers decide (see TeamBanner).
 */

export const CLOTH_SWATCHES = ['#e8c46a', '#7a3df0', '#c0392b', '#5aa88a']
export const CUTS = ['swallow', 'point', 'square']
export const FRAME_TIERS = [
  { tier: 1, name: 'BRONZE', metal: '#8a5a2e' },
  { tier: 2, name: 'SILVER', metal: '#b9bfcc' },
  { tier: 3, name: 'GOLD', metal: '#c9a84c' },
  { tier: 4, name: 'RADIANT', metal: '#f2ecd8' },
]
export const SIGILS = [
  { id: null, glyph: '—' },
  { id: 'star', glyph: '✦' },
  { id: 'crown', glyph: '♛' },
  { id: 'diamond', glyph: '◆' },
  { id: 'spark', glyph: '✧' },
  { id: 'moon', glyph: '☽' },
]
export const SIGIL_GLYPHS = Object.fromEntries(SIGILS.filter(s => s.id).map(s => [s.id, s.glyph]))

const maskUrl = (cut) => `/icons/banners/mask_${CUTS.includes(cut) ? cut : 'swallow'}.svg`

function maskStyle(cut) {
  const url = `url(${maskUrl(cut)})`
  return {
    WebkitMaskImage: url, maskImage: url,
    WebkitMaskSize: 'contain', maskSize: 'contain',
    WebkitMaskPosition: 'center', maskPosition: 'center',
    WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat',
  }
}

export default function Pennant({
  cloth = '#7a3df0', cut = 'swallow', frameTier = 1, sigil = null,
  emblem = null, paint = null,
  width = 120, style, children,
}) {
  const height = width * 1.8 // mask svgs are 120×216
  const frame = FRAME_TIERS.find(f => f.tier === frameTier) || FRAME_TIERS[0]
  return (
    <div style={{ position: 'relative', width, height, ...style }}>
      {/* rod */}
      <div style={{ position: 'absolute', left: '-9%', right: '-9%', top: '1.5%', height: Math.max(3, width * 0.032), background: `linear-gradient(90deg, transparent, ${frame.metal}, transparent)` }} />
      <div style={{ position: 'absolute', left: '-11%', top: '0.2%', width: width * 0.075, height: width * 0.075, transform: 'rotate(45deg)', background: frame.metal }} />
      <div style={{ position: 'absolute', right: '-11%', top: '0.2%', width: width * 0.075, height: width * 0.075, transform: 'rotate(45deg)', background: frame.metal }} />
      {/* frame trim — the same mask, scaled up a hair behind the cloth */}
      <div style={{ position: 'absolute', inset: 0, background: frame.metal, transform: 'scale(1.045)', transformOrigin: '50% 12%', ...maskStyle(cut), ...(frameTier === 4 ? { filter: 'drop-shadow(0 0 6px rgba(242,236,216,.55))' } : {}) }} />
      {/* cloth */}
      <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(100deg, rgba(0,0,0,.28) 0%, rgba(255,255,255,.10) 18%, rgba(0,0,0,0) 40%, rgba(0,0,0,.30) 100%), ${cloth}`, ...maskStyle(cut) }} />
      {/* painted layer */}
      {paint && (
        <img src={paint} alt="" draggable={false}
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', pointerEvents: 'none', ...maskStyle(cut) }} />
      )}
      {/* sigil glyph or emblem png */}
      {emblem ? (
        <img src={`/icons/emblems/${emblem}.png`} alt="" draggable={false}
          style={{ position: 'absolute', left: '26%', top: '22%', width: '48%', height: '30%', objectFit: 'contain', pointerEvents: 'none', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,.6))' }} />
      ) : sigil && SIGIL_GLYPHS[sigil] ? (
        <div style={{ position: 'absolute', left: 0, right: 0, top: '26%', textAlign: 'center', fontSize: width * 0.34, lineHeight: 1, color: 'rgba(10,6,18,.72)', textShadow: '0 1px 0 rgba(255,255,255,.14)', pointerEvents: 'none' }}>
          {SIGIL_GLYPHS[sigil]}
        </div>
      ) : null}
      {children}
    </div>
  )
}
