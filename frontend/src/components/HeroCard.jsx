import React, { useState } from 'react'
import { regenerateProfile } from '../api/client'

const MORALE_STATE_LABEL = {
  steady: 'Steady', shaken: 'Shaken', fearful: 'Fearful', broken: 'Broken',
}

const CLASS_COLORS = {
  'Warrior': '#c87830',
  'Spearman': '#c8a030',
  'Thief': '#7030c8',
  'Archer': '#30a030',
  'Mage': '#4060c8',
  'Magic Engineer': '#30b8c8',
  'Chef': '#c85030',
  'Medic': '#30c870',
  'Scout': '#a8c830',
  'Blacksmith': '#888',
  'Quartermaster': '#c8c030',
  'Tactician': '#8030c8',
  'Priest': '#c0c0e0',
  'Alchemist': '#30c8a0',
  'Classless': '#555',
}

const SKILL_RARITY_COLORS = {
  common: '#888',
  uncommon: '#4a9a6a',
  rare: '#4a7aaa',
  epic: '#8030c8',
  legendary: '#c9a84c',
}

const CLASS_ICONS = {
  'Warrior': '⚔', 'Spearman': '🔱', 'Thief': '🗡', 'Archer': '🏹',
  'Mage': '🔮', 'Magic Engineer': '⚙', 'Chef': '🍳', 'Medic': '✚',
  'Scout': '🦅', 'Blacksmith': '⚒', 'Quartermaster': '⚖',
  'Tactician': '♔', 'Priest': '☀️', 'Alchemist': '⚗', 'Classless': '♢',
}

const APTITUDE_ORDER = ['Combat', 'Survival', 'Tactical', 'Mental', 'Leadership']

function getAptitudeColor(value) {
  if (value >= 90) return '#c9a84c' // gold - exceptional
  if (value >= 75) return '#6fba6f' // green - high
  if (value >= 50) return 'var(--text-hi)' // normal
  if (value >= 25) return '#c87030' // orange - low
  return 'var(--red)' // very low
}

const RAINBOW_COLORS = ['#ff4444', '#ffaa00', '#ffff00', '#44ff44', '#4444ff', '#8a2be2', '#ee82ee'];

export function Stars({ count, max = 7 }) {
  return (
    <div className={`stars birth-star-${count}`}>
      {Array.from({ length: max }).map((_, i) => (
        <span key={i} className={count === 7 && i < count ? 'cyan-text' : 'star'}>
          {i < count ? '★' : '☆'}
        </span>
      ))}
    </div>
  )
}

export function ClassBadge({ heroClass }) {
  if (!heroClass) return null
  const color = CLASS_COLORS[heroClass] || '#555'
  const icon = CLASS_ICONS[heroClass] || '?'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '3px',
      background: `${color}22`, border: `1px solid ${color}66`,
      color: color, borderRadius: 3,
      padding: '1px 6px', fontSize: '0.7em',
      fontFamily: 'Cinzel, serif', letterSpacing: '0.05em',
      marginTop: '0.3em',
    }}>
      {icon} {heroClass}
    </span>
  )
}

export function LevelBadge({ level, ascensionStar }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.3)',
      color: 'var(--gold)', borderRadius: 3,
      padding: '1px 6px', fontSize: '0.7em',
      fontFamily: 'Cinzel, serif', marginLeft: '0.3em',
    }}>
      Lv.{level}
    </span>
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
        <div className={`morale-bar-fill ${state}`} style={{ width: `${morale}%` }} />
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

function AscensionStars({ count }) {
  if (!count || count <= 0) return null
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '2px',
      marginTop: '0.3em',
    }}>
      <span className="text-dim" style={{ fontSize: '0.65em', marginRight: '0.3em' }}>Ascension</span>
      {Array.from({ length: 7 }).map((_, i) => (
        <span key={i} style={{
          fontSize: '0.7em',
          color: i < count ? 'var(--gold)' : 'var(--border)',
          textShadow: i < count ? '0 0 4px rgba(201,168,76,0.5)' : 'none',
        }}>◆</span>
      ))}
    </div>
  )
}

function AptitudeDisplay({ hero }) {
  const level = hero.level || 1
  const reveals = Math.min(5, Math.floor(level / 5))
  const aptitudes = hero.aptitudes || {}

  return (
    <div style={{ marginTop: '0.5em' }}>
      <div className="text-dim" style={{ fontSize: '0.7em', marginBottom: '0.3em', fontFamily: 'Cinzel, serif' }}>
        Aptitudes
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2em' }}>
        {APTITUDE_ORDER.map((apt, index) => {
          const isRevealed = index < reveals
          const value = aptitudes[apt.toLowerCase()] ?? aptitudes[apt]
          return (
            <div key={apt} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              fontSize: '0.72em',
              padding: '0.15rem 0.4em',
              background: isRevealed ? 'rgba(255,255,255,0.03)' : 'transparent',
              borderRadius: 2,
            }}>
              <span className="text-dim">{apt}</span>
              {isRevealed && value != null ? (
                <span style={{
                  color: getAptitudeColor(value),
                  fontFamily: 'Cinzel, serif',
                  fontWeight: value >= 75 ? 'bold' : 'normal',
                }}>
                  {value}
                </span>
              ) : (
                <span style={{ color: 'var(--border)', fontStyle: 'italic', fontSize: '0.68em' }}>???</span>
              )}
            </div>
          )
        })}
      </div>
      {reveals < 5 && (
        <div className="text-dim" style={{ fontSize: '0.6em', marginTop: '0.2em', fontStyle: 'italic' }}>
          Next reveal at Lv.{(reveals + 1) * 5}
        </div>
      )}
    </div>
  )
}

export default function HeroCard({ hero, onAssign, onManageEquipment, selected, onClick, onToggleSelect, showFull = false, onRegenerateProfile, actions }) {
  if (!hero) return null
  const dead = !hero.is_alive
  const [refreshing, setRefreshing] = useState(false)
  const [imgError, setImgError] = useState(false)

  const handleRegenerateProfile = async (e) => {
    e.stopPropagation()
    setRefreshing(true)
    try {
      await regenerateProfile(hero.id)
      if (onRegenerateProfile) onRegenerateProfile()
    } catch (err) {
      console.error(err)
    } finally {
      setRefreshing(false)
    }
  }

  // Backstory unlocking based on star rank
  const activeStar = hero.current_star || hero.birth_star
  // If 5+ star, show full story. If 1-4 star, show proportional percentage.
  const unlockPct = Math.min(1.0, activeStar / 5)
  const totalChars = hero.backstory ? hero.backstory.length : 0
  const visibleChars = Math.floor(totalChars * unlockPct)
  const unlockedStory = hero.backstory ? hero.backstory.substring(0, visibleChars) : ''
  const lockedStory = hero.backstory ? hero.backstory.substring(visibleChars).replace(/[a-zA-Z0-9]/g, '█') : ''

  return (
    <div
      className={`hero-card ${selected ? 'selected' : ''} ${dead ? 'dead' : ''}`} style={{ fontSize: showFull ? "1.6em" : "1em" }}
      onClick={!dead && onClick ? onClick : undefined}
    >
      {onToggleSelect && (
        <div 
          onClick={(e) => { e.stopPropagation(); onToggleSelect(); }}
          style={{
            position: 'absolute', top: 5, left: 5, zIndex: 10,
            width: 20, height: 20, borderRadius: '50%',
            border: '2px solid var(--border-light)',
            background: selected ? 'var(--gold)' : 'rgba(0,0,0,0.5)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
            color: '#000', fontSize: '0.8em', fontWeight: 'bold'
          }}
        >
          {selected && '✓'}
        </div>
      )}
      <div style={{ position: 'relative' }}>
        {hero.is_on_team > 0 && !showFull && (
          <div style={{
            position: 'absolute', top: 5, right: 5, zIndex: 10,
            background: 'rgba(64, 96, 200, 0.9)', color: '#fff', fontSize: '0.65em',
            padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold',
            border: '1px solid rgba(255,255,255,0.3)'
          }}>
            T{hero.is_on_team}
          </div>
        )}
        {hero.portrait_path && !imgError && !hero.portrait_path.includes('default_') ? (
          <img
            src={`http://localhost:8000/${hero.portrait_path}?t=${new Date().getTime()}`}
            alt={hero.name}
            className="hero-portrait"
            style={showFull ? { height: 'auto', maxHeight: '700px', objectFit: 'contain' } : {}}
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="hero-portrait-placeholder" style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center',
            background: `radial-gradient(circle at top, ${CLASS_COLORS[hero.hero_class] || '#444'}, #1a1a24)`,
            height: showFull ? '400px' : '100%',
            width: '100%',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <span style={{ fontSize: showFull ? '4em' : '2.5em', opacity: 0.5, marginBottom: '20px' }}>
              {CLASS_ICONS[hero.hero_class] || '⚔'}
            </span>
            <div style={{
              position: 'absolute', bottom: '15px', left: 0, right: 0,
              textAlign: 'center', background: 'rgba(200, 50, 50, 0.8)',
              color: 'white', fontSize: '0.65em', padding: '2px',
              fontWeight: 'bold', textTransform: 'uppercase'
            }}>
              Placeholder (Regenerate Profile)
            </div>
          </div>
        )}
        
        {showFull && !dead && !hero.portrait_path.includes('custom_') && (
          <button 
            className="btn btn-gold" 
            style={{ position: 'absolute', bottom: '5px', right: '5px', padding: '2px 6px', fontSize: '0.6em' }}
            onClick={handleRegenerateProfile}
            disabled={refreshing}
          >
            {refreshing ? '...' : 'Regenerate Profile'}
          </button>
        )}
      </div>

      <div className="hero-name">{hero.name}</div>
      <div className="hero-title">{hero.title}</div>
      {hero.synergy_group && (
        <div style={{ marginTop: '0.4em', marginBottom: '0.2em' }}>
          <span style={{ 
            fontSize: '0.65em', 
            background: 'rgba(200, 160, 48, 0.2)', 
            color: '#e8c050', 
            padding: '0.2rem 0.5em', 
            borderRadius: '4px', 
            fontFamily: 'Cinzel, serif', 
            fontWeight: 'bold',
            border: '1px solid rgba(200, 160, 48, 0.4)'
          }}>
            <span style={{ marginRight: '4px' }}>🛡️</span>
            {hero.synergy_group}
          </span>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.3em', marginTop: '0.3em' }}>
        <Stars count={hero.birth_star} />
        <LevelBadge level={hero.level || 1} ascensionStar={hero.ascension_star || 0} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.3em', marginTop: '0.3em' }}>
        <ClassBadge heroClass={hero.hero_class} />
        {hero.ego_type && (
          <span style={{
            display: 'inline-flex', alignItems: 'center',
            background: 'rgba(255,100,100,0.1)', border: '1px solid rgba(255,100,100,0.3)',
            color: '#ff8888', borderRadius: 3,
            padding: '1px 6px', fontSize: '0.7em',
            fontFamily: 'Cinzel, serif',
            marginTop: '0.3em',
          }}>
            dY` Ego: {hero.ego_type}
          </span>
        )}
      </div>

      {/* Ascension stars */}
      <AscensionStars count={hero.ascension_star || 0} />

      {dead && <div className="text-red text-sm" style={{ marginTop: '0.3em' }}>✦ Fallen</div>}

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
            <div style={{ marginTop: '0.75em', borderTop: '1px solid var(--border)', paddingTop: '0.75em' }}>
              <div className="text-sm text-dim" style={{ fontStyle: 'italic', lineHeight: 1.6 }}>
                <span>{unlockedStory}</span>
                {lockedStory && <span style={{ opacity: 0.3, letterSpacing: '2px' }}>{lockedStory}</span>}
                {unlockPct < 1 && (
                  <div style={{ fontSize: '0.65em', color: 'var(--gold)', marginTop: '0.3em', opacity: 0.8 }}>
                    [Story locked. Promote hero to reveal more.]
                  </div>
                )}
              </div>
              <div className="text-sm text-dim" style={{ marginTop: '0.4em', lineHeight: 1.5 }}>
                {hero.personality}
              </div>
              <div className="stats-row" style={{ marginTop: '0.5em' }}>
                <div className="stat">Kills <span>{hero.kills}</span></div>
                <div className="stat">Floors <span>{hero.floors_survived}</span></div>
                <div className="stat">Stress <span>{hero.stress}</span></div>
                <div className="stat">Trauma <span>{hero.trauma}</span></div>
              </div>
              {hero.can_pilot === 1 && (
                <div style={{ marginTop: '0.4em', color: 'var(--blue)', fontSize: '0.75em' }}>
                  ⚙ Can pilot vessels
                </div>
              )}

              {/* Aptitude display */}
              <AptitudeDisplay hero={hero} />

              {/* Equipment Display */}
              <div style={{ marginTop: '0.75em' }}>
                <div className="text-dim" style={{ fontSize: '0.7em', marginBottom: '0.3em', fontFamily: 'Cinzel, serif' }}>
                  Equipment
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3em' }}>
                  {['weapon', 'armor', 'accessory'].map(slot => {
                    const eq = hero.equipment ? hero.equipment.find(e => e.slot === slot) : null;
                    return (
                      <div key={slot} style={{ 
                        padding: '0.3rem 0.5em', 
                        background: 'rgba(255,255,255,0.02)', 
                        borderLeft: `2px solid ${
                          !eq ? '#444' :
                          eq.rarity >= 5 ? '#c9a84c' : 
                          eq.rarity >= 4 ? '#8030c8' : 
                          eq.rarity >= 3 ? '#4a7aaa' : 
                          eq.rarity >= 2 ? '#4a9a6a' : '#888'
                        }`,
                        borderRadius: '0 3px 3px 0',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <div style={{ flex: 1, marginRight: '0.5em' }}>
                          <div style={{ fontSize: '0.65em', color: 'var(--text-dim)', textTransform: 'capitalize', marginBottom: '0.1em' }}>{slot}</div>
                          {eq ? (
                            <>
                              <div style={{ fontSize: '0.75em', color: 'var(--text-hi)' }}>{eq.name}</div>
                              {eq.stats_json && (
                                <div style={{ display: 'flex', gap: '0.4em', flexWrap: 'wrap', marginTop: '0.1em' }}>
                                  {Object.entries(JSON.parse(eq.stats_json)).map(([k, v]) => (
                                    <span key={k} className="text-green" style={{ fontSize: '0.6em' }}>
                                      +{v} {k.toUpperCase()}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </>
                          ) : (
                            <div style={{ fontSize: '0.75em', color: 'var(--text-dim)', fontStyle: 'italic' }}>Empty</div>
                          )}
                        </div>
                        {onManageEquipment && (
                          <button 
                            onClick={() => onManageEquipment(hero, slot, eq)}
                            style={{ 
                              background: eq ? 'transparent' : 'rgba(201,168,76,0.1)', 
                              border: eq ? '1px solid var(--border)' : '1px solid var(--gold)', 
                              color: eq ? 'var(--text-dim)' : 'var(--gold)', 
                              padding: '0.2rem 0.4em', 
                              borderRadius: '3px', 
                              cursor: 'pointer',
                              fontSize: '0.7em'
                            }}
                          >
                            {eq ? 'Unequip' : 'Equip'}
                          </button>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Traits Display */}
              {hero.traits && (
                <div style={{ marginTop: '0.75em' }}>
                  <div className="text-dim" style={{ fontSize: '0.7em', marginBottom: '0.3em', fontFamily: 'Cinzel, serif' }}>
                    Traits
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3em' }}>
                    {(() => {
                      try {
                        const traits = JSON.parse(hero.traits)
                        if (traits.length === 0) return <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>No unique traits.</div>
                        return traits.map((t, idx) => (
                          <div key={idx} style={{ 
                            padding: '0.3rem 0.5em', 
                            background: 'rgba(255,255,255,0.02)', 
                            borderLeft: `2px solid var(--gold)`,
                            borderRadius: '0 3px 3px 0'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.1em' }}>
                              <span style={{ fontSize: '0.75em', color: 'var(--text-hi)' }}>{t.name}</span>
                            </div>
                            <div className="text-dim" style={{ fontSize: '0.65em' }}>{t.desc}</div>
                          </div>
                        ))
                      } catch {
                        return <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>Trait data corrupted.</div>
                      }
                    })()}
                  </div>
                </div>
              )}

              {/* Skills Display */}
              {hero.skills && (
                <div style={{ marginTop: '0.75em' }}>
                  <div className="text-dim" style={{ fontSize: '0.7em', marginBottom: '0.3em', fontFamily: 'Cinzel, serif' }}>
                    Skills
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3em' }}>
                    {(() => {
                      try {
                        const skills = JSON.parse(hero.skills)
                        if (skills.length === 0) return <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>No skills learned.</div>
                        return skills.map((s, idx) => (
                          <div key={idx} style={{ 
                            padding: '0.3rem 0.5em', 
                            background: 'rgba(255,255,255,0.02)', 
                            borderLeft: `2px solid ${SKILL_RARITY_COLORS[s.rarity] || '#888'}`,
                            borderRadius: '0 3px 3px 0'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.1em' }}>
                              <span style={{ fontSize: '0.75em', color: SKILL_RARITY_COLORS[s.rarity] || 'var(--text-hi)' }}>{s.name}</span>
                              <span className="text-dim" style={{ fontSize: '0.65em', textTransform: 'uppercase' }}>{s.type} {s.cooldown ? `(${s.cooldown} CD)` : ''}</span>
                            </div>
                            {s.tier && (
                              <div style={{ fontSize: '0.65em', color: 'var(--gold)', marginBottom: '0.2em' }}>
                                {s.tier} Lv.{s.level} ({s.xp}/{s.max_xp} XP)
                              </div>
                            )}
                            <div className="text-dim" style={{ fontSize: '0.65em' }}>{s.desc}</div>
                          </div>
                        ))
                      } catch {
                        return <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>Skill data corrupted.</div>
                      }
                    })()}
                  </div>
                </div>
              )}
              
              {actions && (
                <div style={{ marginTop: '1.2em', paddingTop: '0.8em', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                  {actions}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {selected && (
        <div style={{
          position: 'absolute', top: -6, right: -6,
          color: '#111', fontSize: '0.85em', background: 'var(--gold)',
          borderRadius: '50%', width: 22, height: 22,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 5px rgba(0,0,0,0.8)', zIndex: 20
        }}>✓</div>
      )}
    </div>
  )
}