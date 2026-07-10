/*
 * ILLUMINATED KIT — per-page background ornaments.
 *
 * MODEST + VARIED (per feedback). A single faint diagonal hairline wash sets
 * the manuscript tone; on top of it a SMALL, seeded scatter of mixed motifs —
 * a couple of rotated diamonds, an upright square or two, a few ✦ sparkles, a
 * lone accent hairline — gives each screen some life without turning into a
 * dense lattice. Low counts, low alpha; the point is variety, not volume.
 */
import React, { useMemo } from 'react'

// Tiny deterministic PRNG (mulberry32) seeded from a string.
function rng(seedStr) {
  let h = 1779033703 ^ seedStr.length
  for (let i = 0; i < seedStr.length; i++) {
    h = Math.imul(h ^ seedStr.charCodeAt(i), 3432918353)
    h = (h << 13) | (h >>> 19)
  }
  let a = h >>> 0
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const GOLD = a => `rgba(184,151,98,${a})`
const VIOLET = a => `rgba(150,110,230,${a})`

export default function Ornaments({ seed = 'page' }) {
  const bits = useMemo(() => {
    const r = rng(seed)
    const pick = arr => arr[Math.floor(r() * arr.length)]
    const spread = () => ({ left: `${Math.round(6 + r() * 86)}%`, top: `${Math.round(6 + r() * 84)}%` })

    // 2-3 rotated diamond outlines — large, faint, spread; ~half nested.
    const diamonds = Array.from({ length: 2 + Math.floor(r() * 2) }, () => {
      const size = Math.round(180 + r() * 300)
      return { ...spread(), size, nested: r() < 0.45, color: (r() < 0.5 ? GOLD : VIOLET)(0.05 + r() * 0.04) }
    })
    // 1-2 upright squares (axis-aligned) — a different shape for variety.
    const squares = Array.from({ length: 1 + Math.floor(r() * 2) }, () => {
      const size = Math.round(90 + r() * 150)
      return { ...spread(), size, color: (r() < 0.5 ? GOLD : VIOLET)(0.045 + r() * 0.035) }
    })
    // 4 twinkling ✦ / ✧ sparkles.
    const sparks = Array.from({ length: 4 }, () => ({
      ...spread(), char: pick(['✦', '✧', '✦']), size: Math.round(9 + r() * 9),
      color: (r() < 0.5 ? 'rgba(200,169,245,' : 'rgba(216,187,132,') + (0.3 + r() * 0.25) + ')',
      dur: (3.5 + r() * 3).toFixed(1), delay: (r() * 3).toFixed(1),
    }))
    // 1-2 lone accent hairlines drawn ON TOP of the base wash.
    const lines = Array.from({ length: 1 + Math.floor(r() * 2) }, () => ({
      ...spread(), len: Math.round(120 + r() * 220), rot: Math.round(-70 + r() * 40),
      color: (r() < 0.5 ? GOLD : VIOLET)(0.1 + r() * 0.06),
    }))
    return { diamonds, squares, sparks, lines }
  }, [seed])

  return (
    <div aria-hidden style={{ position: 'fixed', inset: 0, pointerEvents: 'none', overflow: 'hidden', zIndex: 0 }}>
      {/* faint single-direction diagonal wash — the quiet base tone */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'repeating-linear-gradient(64deg, rgba(184,151,98,.028) 0 1px, transparent 1px 190px)',
      }} />
      {/* rotated diamond outlines */}
      {bits.diamonds.map((d, i) => (
        <div key={`d${i}`} style={{ position: 'absolute', left: d.left, top: d.top, width: d.size, height: d.size, transform: 'rotate(45deg)', border: `1px solid ${d.color}` }}>
          {d.nested && <div style={{ position: 'absolute', inset: Math.round(d.size * 0.08), border: `1px solid ${d.color}` }} />}
        </div>
      ))}
      {/* upright squares */}
      {bits.squares.map((s, i) => (
        <div key={`q${i}`} style={{ position: 'absolute', left: s.left, top: s.top, width: s.size, height: s.size, border: `1px solid ${s.color}` }} />
      ))}
      {/* accent hairlines on top of the wash */}
      {bits.lines.map((l, i) => (
        <div key={`l${i}`} style={{ position: 'absolute', left: l.left, top: l.top, width: l.len, height: 1, transform: `rotate(${l.rot}deg)`, transformOrigin: 'left center', background: `linear-gradient(90deg,transparent,${l.color},transparent)` }} />
      ))}
      {/* twinkling sparkles */}
      {bits.sparks.map((s, i) => (
        <span key={`s${i}`} style={{ position: 'absolute', left: s.left, top: s.top, fontSize: s.size, lineHeight: 1, color: s.color, animation: `orn-twinkle ${s.dur}s ease-in-out ${s.delay}s infinite` }}>{s.char}</span>
      ))}
      <style>{`
        @keyframes orn-twinkle {
          0%, 100% { opacity: .35; transform: scale(.9); }
          50%      { opacity: 1; transform: scale(1.15); }
        }
      `}</style>
    </div>
  )
}
