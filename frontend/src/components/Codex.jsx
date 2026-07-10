/*
 * THE CODEX — static UI shell (Group B). The game's in-world encyclopedia:
 * category rail + entry list. Mock data only.
 */
import React, { useState } from 'react'

const CATS = ['THE TOWER', 'HEROES & CLASSES', 'COMBAT', 'MIND & MORALE', 'DEATH & LEGACY', 'THE BASE', 'SUMMONING', 'THE WORLD']
const ENTRIES = {
  COMBAT: [
    { t: 'STATUS EFFECTS', d: 'Bleed, burn, stun, blind, silence — and how they end' },
    { t: 'POSITIONING', d: 'Frontline, backline, and column splash damage' },
    { t: 'REACTIVE PASSIVES', d: 'Counters, on-kill triggers, and last stands' },
    { t: 'CRITS & ARMOR PEN', d: 'How damage is rolled and mitigated' },
    { t: 'TURN ORDER', d: 'Agility, initiative, and acting twice' },
    { t: 'THE SURVIVAL SWARM', d: 'Outlast the clock when the floor never empties' },
  ],
}

export default function Codex({ onClose }) {
  const [cat, setCat] = useState('COMBAT')
  const entries = ENTRIES[cat] || Array.from({ length: 4 }).map((_, i) => ({ t: `${cat} · ENTRY ${i + 1}`, d: 'Written down by those who lived to tell it.' }))
  return (
    <div className="ilm-codex">
      <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>
      <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>KNOWLEDGE</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.4rem', color: 'var(--text-hi)', letterSpacing: '.04em', textShadow: '0 6px 40px rgba(124,58,214,.4)' }}>THE CODEX</div>
      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 2 }}>Everything the Tower will not tell you — written down by those who lived to tell it.</div>

      <div className="ilm-codex-grid">
        <div className="ilm-codex-rail">
          {CATS.map(c => (
            <button key={c} className={`ilm-codex-cat ${cat === c ? 'active' : ''}`} onClick={() => setCat(c)}>{c}</button>
          ))}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: '0.62rem', color: 'var(--gold)' }}>{cat} · {entries.length} ENTRIES</span>
            <span style={{ flex: 1 }} />
            <input className="ilm-social-search" placeholder="SEARCH THE CODEX…" style={{ maxWidth: 260 }} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {entries.map(e => (
              <div key={e.t} className="ilm-codex-entry">
                <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold-dim)', display: 'inline-block', flex: 'none' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.82rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{e.t}</div>
                  <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.84rem' }}>{e.d}</div>
                </div>
                <span style={{ color: 'var(--gold-dim)' }}>›</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
