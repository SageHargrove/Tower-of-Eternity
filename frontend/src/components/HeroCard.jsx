import React from 'react'

const MORALE_STATE_LABEL = {
  steady: 'Steady',
  shaken: 'Shaken',
  fearful: 'Fearful',
  broken: 'Broken',
}

export function Stars({ count, max = 7 }) {
  return (
    <div className={`stars birth-star-${count}`}>
      {Array.from({ length: max }).map((_, i) => (
        <span key={i} className="star">{i < count ? '★' : '☆'}</span>
      ))}
    </div>
  )
}

export function MoraleBar({ morale, state }) {
  return (
    <div className="morale-bar-wrap">
      <div className="morale-label">
        <span>Morale</span>
        <span className={`text-${state === 'steady' ? 'green' : state === 'broken' ? 'red' : 'gold'}`}>
          {MORALE_STATE_LABEL[state] || state} ({morale})
        </span>
      </div>
      <div className="morale-bar-bg">
        <div
          className={`morale-bar-fill ${state}`}
          style={{ width: `${morale}%` }}
        />
      </div>
    </div>
  )
}

export function HpBar({ hp, maxHp }) {
  const pct = Math.max(0, Math.min(100, (hp / maxHp) * 100))
  return (
    <div className="hp-bar-wrap">
      <div className="morale-label">
        <span>HP</span>
        <span>{hp} / {maxHp}</span>
      </div>
      <div className="hp-bar-bg">
        <div className="hp-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function HeroCard({ hero, selected, onClick, showFull = false }) {
  if (!hero) return null
  const dead = !hero.is_alive

  return (
    <div
      className={`hero-card ${selected ? 'selected' : ''} ${dead ? 'dead' : ''}`}
      onClick={!dead && onClick ? onClick : undefined}
    >
      {hero.portrait_path && (
        <img
          src={`http://localhost:8000/${hero.portrait_path}`}
          alt={hero.name}
          style={{ width: '100%', height: 140, objectFit: 'cover', borderRadius: 2, marginBottom: '0.5rem' }}
        />
      )}

      <div className="hero-name">{hero.name}</div>
      <div className="hero-title">{hero.title}</div>

      <Stars count={hero.birth_star} />

      {dead && <div className="text-red text-sm" style={{ marginTop: '0.3rem' }}>✦ Fallen</div>}

      {!dead && (
        <>
          <HpBar hp={hero.hp} maxHp={hero.max_hp} />
          <MoraleBar morale={hero.morale} state={hero.morale_state || 'steady'} />

          <div className="stats-row">
            <div className="stat">ATK <span>{hero.attack}</span></div>
            <div className="stat">DEF <span>{hero.defense}</span></div>
            <div className="stat">SPD <span>{hero.speed}</span></div>
          </div>

          {showFull && (
            <div style={{ marginTop: '0.75rem', borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
              <div className="text-sm text-dim" style={{ fontStyle: 'italic', lineHeight: 1.6 }}>
                {hero.backstory}
              </div>
              <div className="stats-row" style={{ marginTop: '0.5rem' }}>
                <div className="stat">Kills <span>{hero.kills}</span></div>
                <div className="stat">Floors <span>{hero.floors_survived}</span></div>
                <div className="stat">Stress <span>{hero.stress}</span></div>
                <div className="stat">Trauma <span>{hero.trauma}</span></div>
              </div>
            </div>
          )}
        </>
      )}

      {selected && (
        <div style={{
          position: 'absolute', top: 6, right: 8,
          color: 'var(--gold)', fontSize: '0.7rem', fontFamily: 'Cinzel, serif'
        }}>TEAM</div>
      )}
    </div>
  )
}
