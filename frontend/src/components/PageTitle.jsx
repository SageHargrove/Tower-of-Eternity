import React from 'react'

// Illuminated stacked page title: gold eyebrow line, then a solid Cinzel-900
// word overlapping a ghost outline word (the design system's signature
// watermark treatment). `right` renders actions aligned to the title's
// baseline; `flavor` is the italic subtitle line.
export default function PageTitle({ eyebrow, title, ghost, flavor, right, compact }) {
  return (
    <div className="ent-1" style={{ marginBottom: compact ? '0.6rem' : '1.2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: '1rem' }}>
        <div>
          {eyebrow && <div className="ilm-eyebrow" style={{ marginBottom: 2 }}>{eyebrow}</div>}
          {/* `compact` used to shrink the fonts — every page ended up a
              different size. The stack is one canonical size now; compact
              only tightens the margin below. */}
          <div className="ilm-title-stack">
            {ghost && <div className="ghost">{ghost}</div>}
            <div className="solid">{title}</div>
          </div>
          {flavor && (
            <div style={{ fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 2 }}>
              {flavor}
            </div>
          )}
        </div>
        {right && <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', paddingBottom: 10 }}>{right}</div>}
      </div>
    </div>
  )
}
