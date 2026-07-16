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

// Best value in a row reads green, worst reads red, everything else (and
// full ties) stays neutral gold — "which of these is better" should be
// answerable by color alone without cross-reading numbers.
function cellStyle(value, values) {
  const nums = values.map(Number)
  if (!nums.every(Number.isFinite) || values.length < 2) return { color: '#ddd' }
  const best = Math.max(...nums)
  const worst = Math.min(...nums)
  if (best === worst) return { color: 'var(--gold)' } // full tie
  const n = Number(value)
  if (n === best) return { color: 'var(--green)', fontWeight: 'bold' }
  if (n === worst) return { color: 'var(--red)' }
  return { color: '#ddd' }
}

function StatTable({ columns, rows, columnHeader }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
      <thead>
        <tr>
          <th style={{ textAlign: 'left', padding: '0.4rem 0.6rem', color: 'var(--text-dim)', fontFamily: 'Cinzel, serif', fontSize: '0.75rem', textTransform: 'uppercase' }}></th>
          {columns.map((col, i) => (
            <th key={i} style={{ textAlign: 'center', padding: '0.4rem 0.6rem', fontFamily: 'Cinzel, serif', verticalAlign: 'bottom' }}>
              {columnHeader(col)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map(row => {
          const values = columns.map(col => row.get(col))
          return (
            <tr key={row.key} style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
              <td style={{ padding: '0.4rem 0.6rem', color: 'var(--text-dim)' }}>{row.label}</td>
              {values.map((v, i) => (
                <td key={i} style={{ textAlign: 'center', padding: '0.4rem 0.9rem', ...cellStyle(v, values) }}>
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

function HeroSidePanel({ hero, accent }) {
  return (
    <div style={{
      width: 280, flexShrink: 0, borderRadius: 8, border: '1px solid var(--border)',
      background: 'var(--bg-card)', padding: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center',
    }}>
      {hero.portrait_path ? (
        <img
          src={`/heroes/${hero.id}/card-image?mini=true`}
          onError={(e) => { e.target.onerror = null; e.target.src = `/${hero.portrait_path}` }}
          draggable={false}
          style={{ width: '100%', aspectRatio: '1 / 1', objectFit: 'cover', objectPosition: 'center', borderRadius: 6, border: `1px solid ${accent}`, display: 'block' }}
          alt={hero.name}
        />
      ) : (
        <div style={{
          width: '100%', aspectRatio: '2 / 3', borderRadius: 6,
          background: 'var(--bg-panel)', border: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--border-hi)', fontSize: '2rem',
        }}>?</div>
      )}
      <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.1rem', color: 'var(--text-hi)', marginTop: '0.7rem', textAlign: 'center' }}>{hero.name}</div>
      <div className="text-dim" style={{ fontSize: '0.8rem' }}>
        {hero.hero_class} · Lv.{hero.level} · {(hero.current_star || hero.birth_star)}★
      </div>
    </div>
  )
}

// Hero vs Hero — exactly two heroes, full-size portraits flanking the stat
// table (three boxes: portrait | numbers | portrait). Green = better,
// red = worse, gold = tie.
export function HeroCompareModal({ heroes, onClose }) {
  const [a, b] = heroes
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(3px)' }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 8, padding: '1.5rem', maxWidth: '95vw', maxHeight: '90vh', overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', gap: '2rem' }}>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)' }}>Hero Comparison</div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'stretch' }}>
          <HeroSidePanel hero={a} accent="var(--gold)" />
          <div style={{ minWidth: 340, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <StatTable
              columns={[a, b]}
              rows={HERO_STAT_ROWS}
              columnHeader={h => (
                <div>
                  <div>{h.name}</div>
                  <div className="text-dim" style={{ fontSize: '0.7rem', fontFamily: 'inherit', textTransform: 'none' }}>{h.hero_class}</div>
                </div>
              )}
            />
          </div>
          <HeroSidePanel hero={b} accent="var(--gold)" />
        </div>
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
  { key: 'avg_star', label: 'Avg Star', get: t => t.heroes.length ? Number((t.heroes.reduce((s, h) => s + (h.current_star || h.birth_star || 1), 0) / t.heroes.length).toFixed(1)) : 0 },
  { key: 'total_health', label: 'Total Max Health', get: t => t.heroes.reduce((s, h) => s + h.max_health, 0) },
  { key: 'total_str', label: 'Total STR', get: t => t.heroes.reduce((s, h) => s + h.strength, 0) },
  { key: 'total_int', label: 'Total INT', get: t => t.heroes.reduce((s, h) => s + h.intelligence, 0) },
  { key: 'total_end', label: 'Total END', get: t => t.heroes.reduce((s, h) => s + (h.endurance ?? 5), 0) },
  { key: 'total_agi', label: 'Total AGI', get: t => t.heroes.reduce((s, h) => s + h.agility, 0) },
]

// Which team leads in more of the aggregate categories (skipping ties and
// the plain roster-size row) — a one-line verdict for people who don't want
// to read the table.
function teamVerdict(teamA, teamB) {
  let a = 0, b = 0
  for (const row of TEAM_STAT_ROWS) {
    if (row.key === 'count') continue
    const va = Number(row.get(teamA))
    const vb = Number(row.get(teamB))
    if (va > vb) a++
    else if (vb > va) b++
  }
  if (a === b) return { text: 'Dead even across categories.', winner: null }
  const winner = a > b ? teamA : teamB
  return { text: `Team ${winner.label} leads in ${Math.max(a, b)} of ${a + b} contested categories.`, winner }
}

function classSummary(team) {
  const counts = {}
  for (const h of team.heroes) counts[h.hero_class] = (counts[h.hero_class] || 0) + 1
  return Object.entries(counts).map(([c, n]) => (n > 1 ? `${c} ×${n}` : c)).join(' · ')
}

export function TeamCompareModal({ teamA, teamB, onClose }) {
  const verdict = teamVerdict(teamA, teamB)
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(3px)' }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 8, padding: '1.5rem', maxWidth: '90vw', maxHeight: '85vh', overflow: 'auto', minWidth: '560px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)' }}>Team Comparison</div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>

        <div style={{
          textAlign: 'center', padding: '0.5rem 1rem', marginBottom: '1rem', borderRadius: 6,
          background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.25)',
          fontFamily: 'Cinzel, serif', fontSize: '0.9rem',
          color: verdict.winner ? 'var(--green)' : 'var(--gold)',
        }}>
          {verdict.text}
        </div>

        <StatTable
          columns={[teamA, teamB]}
          rows={TEAM_STAT_ROWS}
          columnHeader={t => <div>Team {t.label}</div>}
        />

        <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1.2rem', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '1rem' }}>
          {[teamA, teamB].map((t, i) => (
            <div key={i} style={{ flex: 1 }}>
              <div className="text-dim" style={{ fontSize: '0.7rem', fontFamily: 'Cinzel, serif', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Team {t.label} Roster</div>
              {t.heroes.length > 0 && (
                <div className="text-dim" style={{ fontSize: '0.7rem', fontStyle: 'italic', marginBottom: '0.5rem' }}>{classSummary(t)}</div>
              )}
              {t.heroes.length === 0
                ? <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>No heroes assigned.</div>
                : t.heroes.map(h => (
                  <div key={h.id} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.25rem 0' }}>
                    {h.portrait_path
                      ? <img src={`/heroes/${h.id}/card-image?mini=1`} alt="" draggable={false}
                          onError={(e) => { if (!e.currentTarget.dataset.fb) { e.currentTarget.dataset.fb = '1'; e.currentTarget.src = `/${h.portrait_path}` } }}
                          style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover', objectPosition: 'center', border: '1px solid var(--border)', flexShrink: 0 }} />
                      : <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--bg-card)', border: '1px solid var(--border)', flexShrink: 0 }} />}
                    <div style={{ fontSize: '0.82rem', minWidth: 0 }}>
                      <span style={{ color: 'var(--text-hi)' }}>{h.name}</span>{' '}
                      <span className="text-dim">({h.hero_class}, {h.current_star || h.birth_star}★, Lv.{h.level})</span>
                    </div>
                  </div>
                ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
