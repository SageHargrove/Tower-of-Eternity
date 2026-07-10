import React from 'react'
import Pennant from './Pennant'

// Renders the player's team banner wherever it flies. Banners saved by the
// Illuminated studio carry {cloth, cut, frame_tier, sigil} and render as a
// vector Pennant; older saves (template_tier/emblem/paint only) fall back to
// the legacy PNG composite so nothing already flying changes appearance.
export default function TeamBanner({ banner, size = 96, style, title }) {
  if (banner?.cloth) {
    // Pennant is 1:1.8 — fit it inside the square slot callers reserve.
    const width = Math.round(size / 1.8)
    return (
      <div title={title || 'Team Banner'} style={{ position: 'relative', width: size, height: size, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', ...style }}>
        <Pennant
          cloth={banner.cloth} cut={banner.cut} frameTier={banner.frame_tier || 1}
          sigil={banner.sigil} emblem={banner.emblem} paint={banner.paint}
          width={width}
        />
      </div>
    )
  }

  // Legacy saves (no studio cloth) render the DRAWN Illuminated cloth — the
  // old banner_tierN.png composites are off-model and never render anymore.
  // The emblem PNG remains the player's own-art hook, masked to a diamond.
  const clip = 'polygon(0 0,100% 0,100% 82%,50% 100%,0 82%)'
  const clipInner = 'polygon(0 0,100% 0,100% 81%,50% 99%,0 81%)'
  const width = Math.round(size / 1.8)
  return (
    <div title={title || 'Team Banner'} style={{ position: 'relative', width: size, height: size, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', ...style }}>
      <div style={{ position: 'relative', width, height: size }}>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(170deg,#2a1650,#140b22 70%)', border: '1px solid rgba(184,151,98,.55)', clipPath: clip, boxShadow: '0 10px 30px rgba(0,0,0,.5)' }} />
        {banner?.paint && (
          <img src={banner.paint} alt="" draggable={false}
            style={{ position: 'absolute', inset: 2, width: 'calc(100% - 4px)', height: 'calc(100% - 4px)', objectFit: 'cover', clipPath: clip, opacity: 0.8 }} />
        )}
        <div style={{ position: 'absolute', inset: 5, border: '1px solid rgba(200,169,245,.3)', clipPath: clipInner, pointerEvents: 'none' }} />
        {banner?.emblem && (
          <span style={{ position: 'absolute', left: '50%', top: '30%', width: '52%', aspectRatio: '1', transform: 'translate(-50%,-50%)', clipPath: 'polygon(50% 0,100% 50%,50% 100%,0 50%)', overflow: 'hidden', display: 'block' }}>
            <img src={`/icons/emblems/${banner.emblem}.png`} alt="" draggable={false}
              style={{ width: '100%', height: '100%', objectFit: 'contain', filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.6))' }} />
          </span>
        )}
      </div>
    </div>
  )
}
