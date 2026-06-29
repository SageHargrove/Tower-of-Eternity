import React from 'react'

// Stat rows shown for Hero vs Hero — same fields HeroCard already surfaces
// on a roster card, just laid out side by side instead of one at a time.
const HERO_STAT_ROWS = [
  { key: 'current_star', label: 'Star', get: h => h.current_star || h.birth_star || 1 },
  { key: 'level', label: 'Level', get: h => h.level },
  { key: 'max_health', label: 'Max Health', get: h => h.max_health },
  { key: 'max_mana', label: 'Max Mana', get: h => h.max_mana ?? '—' },
  { key: 'strength', label: 'STR', get: h => h.strength },
  { key: 'intelligence', label: 'INT', get: h => h.intelligence },
  { key: 'endurance', label: 'END', get: h => h.endurance ?? 5 },
  { key: 'agility', label: 'AGI', get: h => h.agility },
  { key: 'willpower', label: 'WIL', get: h => h.willpower ?? 6 },
  { key: 'luck', label: 'LUC', get: h => h.luck ?? 5 },
  { key: 'kills', label: 'Kills', get: h => h.kills ?? 0 },
  { key: 'floors_survived', label: 'Floors Survived', get: h => h.floors_survived ?? 0 },
]

function StatTable({ columns, rows, columnHeader }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
      <thead>
        <tr>
          <th style={{ textAlign: 'left', padding: '0.4rem 0.6rem', color: 'var(--text-dim)', fontFamily: 'Cinzel, serif', fontSize: '0.75rem', textTransform: 'uppercase' }}></th>
          {columns.map((col, i) => (
            <th key={i} style={{ textAlign: 'center', padding: '0.4rem 0.6rem', fontFamily: 'Cinzel, serif' }}>
              {columnHeader(col)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map(row => {
          const values = columns.map(col => row.get(col))
          const numeric = values.every(v => typeof v === 'number')
          const best = numeric ? Math.max(...values) : null
          return (
            <tr key={row.key} style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
              <td style={{ padding: '0.4rem 0.6rem', color: 'var(--text-dim)' }}>{row.label}</td>
              {values.map((v, i) => (
                <td key={i} style={{
                  textAlign: 'center', padding: '0.4rem 0.6rem',
                  color: numeric && v === best && columns.length > 1 ? 'var(--gold)' : '#ddd',
                  fontWeight: numeric && v === best && columns.length > 1 ? 'bold' : 'normal',
                }}>
                  {v}
                </td>
              ))}
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

// Hero vs Hero — 2-4 individually selected heroes, full stat breakdown.
export function HeroCompareModal({ heroes, onClose }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 8, padding: '1.5rem', maxWidth: '90vw', maxHeight: '85vh', overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)' }}>Hero Comparison</div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
        <StatTable
          columns={heroes}
          rows={HERO_STAT_ROWS}
          columnHeader={h => (
            <div>
              <div>{h.name}</div>
              <div className="text-dim" style={{ fontSize: '0.7rem', fontFamily: 'inherit', textTransform: 'none' }}>{h.hero_class}</div>
            </div>
          )}
        />
      </div>
    </div>
  )
}

// Team vs Team — aggregated totals for two teams side by side, plus each
// team's actual roster underneath so "who do I bring" has the per-hero
// detail too, not just a flattened total.
const TEAM_STAT_ROWS = [
  { key: 'count', label: 'Heroes', get: t => t.heroes.length },
  { key: 'avg_level', label: 'Avg Level', get: t => t.heroes.length ? Math.round(t.heroes.reduce((s, h) => s + h.level, 0) / t.heroes.length) : 0 },
  { key: 'total_health', label: 'Total Max Health', get: t => t.heroes.reduce((s, h) => s + h.max_health, 0) },
  { key: 'total_str', label: 'Total STR', get: t => t.heroes.reduce((s, h) => s + h.strength, 0) },
  { key: 'total_int', label: 'Total INT', get: t => t.heroes.reduce((s, h) => s + h.intelligence, 0) },
  { key: 'total_agi', label: 'Total AGI', get: t => t.heroes.reduce((s, h) => s + h.agility, 0) },
  { key: 'avg_star', label: 'Avg Star', get: t => t.heroes.length ? (t.heroes.reduce((s, h) => s + (h.current_star || h.birth_star || 1), 0) / t.heroes.length).toFixed(1) : 0 },
]

export function TeamCompareModal({ teamA, teamB, onClose }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 8, padding: '1.5rem', maxWidth: '90vw', maxHeight: '85vh', overflow: 'auto', minWidth: '500px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)' }}>Team Comparison</div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
        <StatTable
          columns={[teamA, teamB]}
          rows={TEAM_STAT_ROWS}
          columnHeader={t => <div>Team {t.label}</div>}
        />
        <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1.2rem', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '1rem' }}>
          {[teamA, teamB].map((t, i) => (
            <div key={i} style={{ flex: 1 }}>
              <div className="text-dim" style={{ fontSize: '0.7rem', fontFamily: 'Cinzel, serif', textTransform: 'uppercase', marginBottom: '0.4rem' }}>Team {t.label} Roster</div>
              {t.heroes.length === 0
                ? <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>No heroes assigned.</div>
                : t.heroes.map(h => (
                  <div key={h.id} style={{ fontSize: '0.82rem', padding: '0.2rem 0' }}>
                    {h.name} <span className="text-dim">({h.hero_class}, {h.current_star || h.birth_star}★, Lv.{h.level})</span>
                  </div>
                ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
