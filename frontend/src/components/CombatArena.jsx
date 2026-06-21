import React, { useState, useEffect } from 'react'

const TEAM_POSITIONS = {
  hero: [
    { x: '35%', y: '40%' }, // Front Top
    { x: '35%', y: '60%' }, // Front Bottom
    { x: '20%', y: '30%' }, // Back Top
    { x: '20%', y: '50%' }, // Back Mid
    { x: '20%', y: '70%' }, // Back Bottom
  ],
  enemy: [
    { x: '65%', y: '40%' }, // Front Top
    { x: '65%', y: '60%' }, // Front Bottom
    { x: '80%', y: '30%' }, // Back Top
    { x: '80%', y: '50%' }, // Back Mid
    { x: '80%', y: '70%' }, // Back Bottom
  ]
}

function FloatingDamage({ number, isCrit, onComplete }) {
  const [active, setActive] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setActive(false)
      if (onComplete) onComplete()
    }, 800)
    return () => clearTimeout(timer)
  }, [onComplete])

  if (!active) return null

  return (
    <div style={{
      position: 'absolute',
      top: '-20px',
      left: '50%',
      transform: 'translate(-50%, -100%)',
      color: isCrit ? '#ff4444' : '#fff',
      fontWeight: 'bold',
      fontSize: isCrit ? '1.8rem' : '1.2rem',
      textShadow: '0 2px 4px rgba(0,0,0,0.8)',
      animation: 'floatUpAndFade 0.8s ease-out forwards',
      zIndex: 100,
      pointerEvents: 'none'
    }}>
      -{number}
      {isCrit && <span style={{ fontSize: '0.8rem', display: 'block' }}>CRIT!</span>}
    </div>
  )
}

function CombatUnitSprite({ unit, team, position, isActive, isHit, hp, maxHp, damageInfo }) {
  if (!unit) return null
  
  const isDead = hp <= 0
  const hpPercent = Math.max(0, (hp / maxHp) * 100)
  
  const pos = TEAM_POSITIONS[team][position] || TEAM_POSITIONS[team][0]

  return (
    <div style={{
      position: 'absolute',
      left: pos.x,
      top: pos.y,
      transform: `translate(-50%, -50%) ${isActive ? (team === 'hero' ? 'translateX(15px)' : 'translateX(-15px)') : ''}`,
      transition: 'transform 0.2s ease-out',
      opacity: isDead ? 0.3 : 1,
      filter: isDead ? 'grayscale(100%)' : isHit ? 'brightness(200%)' : 'none',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '0.5rem',
      width: '100px'
    }}>
      <div style={{ 
        width: '60px', 
        height: '60px', 
        borderRadius: '50%',
        border: `3px solid ${team === 'hero' ? 'var(--gold)' : '#a44'}`,
        overflow: 'hidden',
        position: 'relative',
        boxShadow: isActive ? `0 0 15px ${team === 'hero' ? 'var(--gold)' : '#a44'}` : '0 4px 8px rgba(0,0,0,0.5)'
      }}>
        {unit.portrait_path ? (
          <img src={`http://localhost:8000/${unit.portrait_path}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt={unit.name} />
        ) : (
          <div style={{ width: '100%', height: '100%', background: '#333' }} />
        )}
      </div>

      <div style={{
        width: '100%',
        background: '#111',
        height: '6px',
        borderRadius: '3px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${hpPercent}%`,
          height: '100%',
          background: team === 'hero' ? '#4a4' : '#e44',
          transition: 'width 0.3s ease-out'
        }} />
      </div>

      <div style={{ 
        fontSize: '0.7rem', 
        background: 'rgba(0,0,0,0.6)', 
        padding: '0.1rem 0.4rem', 
        borderRadius: '4px',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        maxWidth: '100%'
      }}>
        {unit.name}
      </div>

      {damageInfo && (
        <FloatingDamage number={damageInfo.amount} isCrit={damageInfo.crit} />
      )}
    </div>
  )
}

export default function CombatArena({ combatData, onComplete }) {
  const [currentTurnIndex, setCurrentTurnIndex] = useState(-1)
  const [playing, setPlaying] = useState(false)
  
  // Local state for HP tracking
  const [unitHPs, setUnitHPs] = useState({})
  
  const heroes = combatData?.initial_state?.heroes || []
  const enemies = combatData?.initial_state?.enemies || []
  const turns = combatData?.turns || []

  useEffect(() => {
    if (combatData) {
      // Initialize HPs
      const initialHps = {}
      heroes.forEach(h => initialHps[h.id] = h.hp)
      enemies.forEach(e => initialHps[e.id] = e.hp)
      setUnitHPs(initialHps)
      setCurrentTurnIndex(-1)
      setPlaying(true)
    }
  }, [combatData])

  useEffect(() => {
    if (!playing) return

    if (currentTurnIndex >= turns.length) {
      setPlaying(false)
      setTimeout(() => {
        if (onComplete) onComplete()
      }, 1500)
      return
    }

    if (currentTurnIndex >= 0) {
      const turn = turns[currentTurnIndex]
      if (turn && turn.target_id) {
        setUnitHPs(prev => ({
          ...prev,
          [turn.target_id]: turn.target_hp
        }))
      }
    }

    const timer = setTimeout(() => {
      setCurrentTurnIndex(c => c + 1)
    }, 800) // Delay between turns

    return () => clearTimeout(timer)
  }, [currentTurnIndex, playing, turns, onComplete])

  if (!combatData) return null

  const currentTurn = currentTurnIndex >= 0 && currentTurnIndex < turns.length ? turns[currentTurnIndex] : null

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      height: '400px',
      background: 'linear-gradient(to bottom, #1a1a24, #0a0a10)',
      border: '1px solid #333',
      borderRadius: '8px',
      overflow: 'hidden',
      marginBottom: '1rem',
      boxShadow: 'inset 0 0 50px rgba(0,0,0,0.8)'
    }}>
      {/* Background elements */}
      <div style={{ position: 'absolute', inset: 0, opacity: 0.1, backgroundImage: 'url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAABZJREFUeNpi2r9//38bIxsDB1AMBgwAE2gDG9mC9U8AAAAASUVORK5CYII=)', backgroundSize: '10px' }} />
      
      {/* Divider */}
      <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '2px', background: 'rgba(255,255,255,0.05)' }} />

      {/* Render Heroes */}
      {heroes.map((hero, idx) => {
        const isAttacker = currentTurn?.attacker_id === hero.id
        const isTarget = currentTurn?.target_id === hero.id
        const dmgInfo = isTarget ? { amount: currentTurn.damage, crit: currentTurn.is_crit } : null
        return (
          <CombatUnitSprite 
            key={hero.id} 
            unit={hero} 
            team="hero" 
            position={idx} 
            isActive={isAttacker}
            isHit={isTarget}
            hp={unitHPs[hero.id] ?? hero.hp}
            maxHp={hero.max_hp}
            damageInfo={dmgInfo}
          />
        )
      })}

      {/* Render Enemies */}
      {enemies.map((enemy, idx) => {
        const isAttacker = currentTurn?.attacker_id === enemy.id
        const isTarget = currentTurn?.target_id === enemy.id
        const dmgInfo = isTarget ? { amount: currentTurn.damage, crit: currentTurn.is_crit } : null
        return (
          <CombatUnitSprite 
            key={enemy.id} 
            unit={enemy} 
            team="enemy" 
            position={idx} 
            isActive={isAttacker}
            isHit={isTarget}
            hp={unitHPs[enemy.id] ?? enemy.hp}
            maxHp={enemy.max_hp}
            damageInfo={dmgInfo}
          />
        )
      })}

      {/* Turn Action Log Overlay */}
      {currentTurn && (
        <div style={{
          position: 'absolute',
          bottom: '10%',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(0,0,0,0.8)',
          border: '1px solid var(--gold)',
          padding: '0.5rem 1rem',
          borderRadius: '4px',
          color: '#fff',
          fontFamily: 'Cinzel, serif',
          animation: 'fadeIn 0.2s',
          whiteSpace: 'nowrap',
          zIndex: 50
        }}>
          {currentTurn.log}
        </div>
      )}

      <style>{`
        @keyframes floatUpAndFade {
          0% { transform: translate(-50%, 0) scale(0.5); opacity: 0; }
          20% { transform: translate(-50%, -20px) scale(1.2); opacity: 1; }
          100% { transform: translate(-50%, -40px) scale(1); opacity: 0; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translate(-50%, 10px); }
          to { opacity: 1; transform: translate(-50%, 0); }
        }
      `}</style>
    </div>
  )
}
