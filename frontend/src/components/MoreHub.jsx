/*
 * ARCHIVE — the Tower's records: the Codex (knowledge) and the Herald
 * (tidings). Everything else that once squatted here has moved to its real
 * home: Daily Gates → Tower console · Expeditions/Tournament/Scout → World ·
 * Memorial → Base lobby · Profile Card → the menu · Banner Tiers → Banner
 * Studio · Tavern is a Base facility · Death Ceremony / Designate Runner /
 * Disconnected fire only inside the flows they belong to.
 */
import React, { useState } from 'react'
import PageTitle from './PageTitle'
import Codex from './Codex'
import Herald from './Herald'

const CARDS = [
  { id: 'codex', name: 'THE CODEX', sub: 'Knowledge', blurb: 'Everything the Tower will not tell you, written down — classes, floors, rites, and the numbers beneath them.', glyph: '❦', tone: 'rgba(216,187,132,.45)' },
  { id: 'herald', name: 'THE HERALD', sub: 'Tidings', blurb: 'Word from the keepers of the Tower — news, notices, and decrees. Read before you climb.', glyph: '✦', tone: 'rgba(150,110,230,.4)' },
]

export default function MoreHub() {
  const [view, setView] = useState(null)

  if (view === 'codex') return <Codex onClose={() => setView(null)} />
  if (view === 'herald') return <Herald onClose={() => setView(null)} />

  return (
    <div className="page">
      <PageTitle eyebrow="The Tower's Records" title="ARCHIVE" ghost="RECORDS"
        flavor="What the Tower knows, and what the keepers proclaim." />
      <div className="ilm-morehub" style={{ maxWidth: 760 }}>
        {CARDS.map(c => (
          <button key={c.id} className="ilm-morehub-card" style={{ borderColor: c.tone }} onClick={() => setView(c.id)}>
            <span className="ilm-morehub-glyph">{c.glyph}</span>
            <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.1rem', letterSpacing: '.04em', color: 'var(--text-hi)' }}>{c.name}</div>
            <div className="ilm-micro" style={{ color: 'var(--gold-hi)', marginTop: 2 }}>{c.sub}</div>
            <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 8, lineHeight: 1.4, fontSize: '0.88rem' }}>{c.blurb}</div>
            <span className="ilm-morehub-open">OPEN ›</span>
          </button>
        ))}
      </div>
    </div>
  )
}
