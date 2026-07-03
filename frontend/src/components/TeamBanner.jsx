import React from 'react'

// Renders the player's team banner: template cloth (tier art) + either the
// chosen emblem overlay or their hand-painted layer. Pure display — the
// same composite the Banner Studio edits. banner = {template_tier, emblem,
// paint} (see /base/banner).
export default function TeamBanner({ banner, size = 96, style, title }) {
  const tier = banner?.template_tier || 1
  return (
    <div
      title={title || 'Team Banner'}
      style={{ position: 'relative', width: size, height: size, flexShrink: 0, ...style }}
    >
      <img
        src={`/icons/banners/banner_tier${tier}.png`}
        alt=""
        draggable={false}
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain' }}
      />
      {banner?.paint && (
        <img
          src={banner.paint}
          alt=""
          draggable={false}
          style={{ 
            position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain',
            WebkitMaskImage: `url(/icons/banners/banner_tier${tier}.png)`,
            WebkitMaskSize: 'contain',
            WebkitMaskPosition: 'center',
            WebkitMaskRepeat: 'no-repeat',
            maskImage: `url(/icons/banners/banner_tier${tier}.png)`,
            maskSize: 'contain',
            maskPosition: 'center',
            maskRepeat: 'no-repeat'
          }}
        />
      )}
      {banner?.emblem && (
        <img
          src={`/icons/emblems/${banner.emblem}.png`}
          alt=""
          draggable={false}
          style={{
            position: 'absolute',
            left: '28%', top: '28%', width: '44%', height: '44%',
            objectFit: 'contain',
            filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.6))',
          }}
        />
      )}
    </div>
  )
}
