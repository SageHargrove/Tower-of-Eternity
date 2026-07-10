/*
 * Sigil — renders one of the custom line-icon SVGs (status / facility / floor /
 * class-base / class-evolution / ui) as a CSS mask so it takes the element's
 * `color` (currentColor). An <img> can't inherit color from CSS, so mask is the
 * only way to recolor these currentColor SVGs per-context.
 *
 * Files live under /public/icons/<set>/<NAME>.svg (UPPERCASE for game sets;
 * the ui set uses its own lowercase names). Missing files just render nothing.
 */
import React, { useState, useEffect } from 'react'

// Module-level cache of which sigil URLs exist, so we don't re-probe every
// mount (and so a known-good icon shows instantly on remount).
const _known = new Map() // url -> boolean

export default function Sigil({ set, name, size = 16, color, title, className = '', style, fallback = null }) {
  const url = name ? `/icons/${set}/${name}.svg` : null
  const [ok, setOk] = useState(() => (url ? _known.get(url) ?? null : false))

  useEffect(() => {
    if (!url || _known.get(url) != null) return
    let live = true
    const img = new Image()
    img.onload = () => { _known.set(url, true); if (live) setOk(true) }
    img.onerror = () => { _known.set(url, false); if (live) setOk(false) }
    img.src = url
    return () => { live = false }
  }, [url])

  // Missing file → render the fallback (or nothing), never a solid square.
  if (!url || ok === false) return fallback
  if (ok === null) return fallback // still probing — show fallback meanwhile
  return (
    <span
      className={`ilm-sigil ${className}`}
      title={title}
      role="img"
      aria-label={title || name}
      style={{
        width: size,
        height: size,
        backgroundColor: color || 'currentColor',
        WebkitMaskImage: `url("${url}")`,
        maskImage: `url("${url}")`,
        ...style,
      }}
    />
  )
}
