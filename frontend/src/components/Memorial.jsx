/*
 * THE MEMORIAL — live. The roll of fallen heroes comes from the legacy
 * system (/heroes/legacies): every qualifying death is enshrined with a
 * title and score; only the SACRIFICED lend "bonds upon the living"
 * (active_bonuses — the same numbers apply_legacy_bonuses feeds combat).
 */
import React, { useState, useEffect } from 'react'
import { getLegacies } from '../api/client'

const FILTERS = ['ALL WHO FELL', 'THE SACRIFICED', 'CLAIMED IN COMBAT']

// active_bonuses key -> display row. Stress reduce reads as a reduction
// (green, minus); everything else is a team-wide plus.
const BOND_LABELS = [
  ['str_pct', 'ATK', false],
  ['int_pct', 'DEF', false],
  ['hlt_pct', 'HEALTH', false],
  ['agi_pct', 'SPD', false],
  ['team_crit_pct', 'CRIT CHANCE', false],
  ['team_stress_reduce', 'STRESS GAIN', true],
  ['team_fear_resist', 'FEAR RESIST', false],
]

export default function Memorial({ onClose }) {
  const [filter, setFilter] = useState('ALL WHO FELL')
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    getLegacies().then(setData).catch(e => setErr(e.message))
  }, [])

  const legacies = (data?.legacies || []).slice().sort((a, b) => (b.score || 0) - (a.score || 0))
  const rows = legacies.filter(f =>
    filter === 'ALL WHO FELL' || (filter === 'THE SACRIFICED' ? f.is_sacrifice : !f.is_sacrifice))

  const bonds = BOND_LABELS
    .map(([key, label, invert]) => ({ key, label, invert, v: data?.active_bonuses?.[key] || 0 }))
    .filter(b => b.v > 0)

  return (
    <div className="ilm-memorial">
      <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 2 }}>
        <span style={{ width: 9, height: 9, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
        <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 600, letterSpacing: '.5em', fontSize: '0.7rem', color: 'var(--gold)' }}>REMEMBRANCE</span>
      </div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.6rem', color: 'var(--text-hi)', letterSpacing: '.04em', textShadow: '0 6px 40px rgba(124,58,214,.4)' }}>THE MEMORIAL</div>
      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 4 }}>The Tower keeps their bodies. We keep their names.</div>

      <div className="ilm-memorial-grid">
        {/* left — bonds upon the living */}
        <div className="ilm-memorial-bonds">
          <span className="ilm-corner" />
          <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: '0.6rem', color: 'var(--gold-hi)' }}>BONDS UPON THE LIVING</div>
          <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.85rem', margin: '6px 0 14px' }}>Only the sacrificed lend their strength.</div>
          {bonds.length === 0 && (
            <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: '0.82rem' }}>
              No bonds yet — no hero has been given to the Tower willingly.
            </div>
          )}
          {bonds.map(b => (
            <div key={b.key} className="ilm-memorial-bond">
              <span className="ilm-micro">{b.label}</span>
              <span style={{ flex: 1, height: 1, background: 'rgba(184,151,98,.15)' }} />
              <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, color: b.invert ? 'var(--green-hi)' : 'var(--gold-hi)' }}>
                {b.invert ? '-' : '+'}{Math.round(b.v * 100)}%
              </span>
            </div>
          ))}
        </div>

        {/* right — roll of the dead */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
            {FILTERS.map(f => (
              <button key={f} className={`ilm-fac-chip ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>{f}</button>
            ))}
            <span style={{ flex: 1 }} />
            <span className="ilm-micro">THE ROLL OF THE DEAD · BY DEED</span>
          </div>
          {err && <div style={{ color: 'var(--red-hi)', fontSize: '0.85rem' }}>{err}</div>}
          {!err && rows.length === 0 && (
            <div style={{ fontStyle: 'italic', color: 'var(--muted)', padding: '2rem 0', textAlign: 'center' }}>
              {legacies.length === 0
                ? 'No names are carved here yet. May it stay that way a while.'
                : 'None who fell this way.'}
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {rows.map((f, i) => (
              <div key={f.id ?? `${f.hero_name}-${i}`} className="ilm-memorial-row">
                <span className="ilm-memorial-rank">{i + 1}</span>
                <span className="ilm-memorial-urn">⚱</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                    <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.86rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{(f.hero_name || 'UNKNOWN').toUpperCase()}</span>
                    <span className="ilm-chip" style={{ padding: '1px 8px', color: f.is_sacrifice ? 'var(--lavender)' : 'var(--muted)', border: `1px solid ${f.is_sacrifice ? 'rgba(150,110,230,.4)' : 'rgba(150,110,230,.2)'}` }}>
                      {f.is_sacrifice ? 'SACRIFICED' : 'FELL IN BATTLE'}
                    </span>
                    {f.hero_star > 0 && <span className="ilm-micro" style={{ color: 'var(--gold-dim)' }}>{'★'.repeat(f.hero_star)}</span>}
                  </div>
                  <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.84rem' }}>
                    “{f.title || 'They climbed, and the Tower remembers.'}”{!f.is_sacrifice && ' · leaves no bond'}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="ilm-micro">SCORE</div>
                  <div style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, color: 'var(--gold-hi)', fontSize: '1.1rem' }}>{(f.score || 0).toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
