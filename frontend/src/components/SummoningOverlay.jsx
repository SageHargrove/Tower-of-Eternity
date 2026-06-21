import React, { useState, useEffect } from 'react'
import HeroCard from './HeroCard'
import { playClick } from '../audio'

export default function SummoningOverlay({ results, onComplete }) {
  const [phase, setPhase] = useState('rift') // 'rift' -> 'reveal'
  const [currentIndex, setCurrentIndex] = useState(0)

  const maxStar = results.length > 0 ? Math.max(...results.map(h => h.birth_star)) : 1

  let riftType = 'standard'
  if (maxStar >= 6) riftType = 'apocalyptic'
  else if (maxStar >= 4) riftType = 'epic'

  useEffect(() => {
    // Play rift animation for a few seconds, then transition to reveal
    const timer = setTimeout(() => {
      setPhase('reveal')
    }, riftType === 'apocalyptic' ? 4000 : riftType === 'epic' ? 3000 : 2000)
    return () => clearTimeout(timer)
  }, [riftType])

  useEffect(() => {
    if (phase === 'reveal' && currentIndex < results.length) {
      const hero = results[currentIndex]
      const isHighRarity = hero.birth_star >= 4
      
      playClick() // Click sound on reveal

      const timer = setTimeout(() => {
        setCurrentIndex(c => c + 1)
      }, isHighRarity ? 2500 : 2000) // Pause longer on high rarity
      return () => clearTimeout(timer)
    } else if (phase === 'reveal' && currentIndex >= results.length) {
      // Done revealing
      const timer = setTimeout(() => {
        onComplete()
      }, 2500)
      return () => clearTimeout(timer)
    }
  }, [phase, currentIndex, results, onComplete])

  const handleSkip = () => {
    onComplete()
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: '#000', zIndex: 9999,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start',
      overflowY: 'auto',
      padding: '2rem 0'
    }}>
      {/* Skip Button */}
      <button 
        className="btn" 
        onClick={handleSkip}
        style={{ position: 'absolute', top: 20, right: 20, zIndex: 10000, background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border)' }}
      >
        Skip All ⏭
      </button>

      {phase === 'rift' && (
        <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {/* Base Rift Container */}
          <div className={`rift-container ${riftType}`}>
            <div className="rift-core" />
            <div className="rift-aura" />
            {riftType === 'epic' && <div className="rift-lightning-gold" />}
            {riftType === 'apocalyptic' && <div className="rift-lightning-red" />}
          </div>
          
          <div style={{ position: 'absolute', bottom: '20%', fontFamily: 'Cinzel, serif', fontSize: '2rem', letterSpacing: '8px', color: '#fff', animation: 'pulse 1s infinite' }}>
            {riftType === 'apocalyptic' ? 'A CALAMITY APPROACHES...' : riftType === 'epic' ? 'A GREAT POWER STIRS...' : 'SUMMONING...'}
          </div>
        </div>
      )}

      {phase === 'reveal' && (
        <div style={{ animation: 'zoomIn 0.3s ease-out', margin: 'auto' }} key={Math.min(currentIndex, results.length - 1)}>
          <HeroCard 
            hero={results[Math.min(currentIndex, results.length - 1)]} 
            showFull={results[Math.min(currentIndex, results.length - 1)].birth_star >= 4} 
          />
        </div>
      )}

      {/* Global styles for rift animations */}
      <style>{`
        @keyframes zoomIn {
          from { transform: scale(0.5); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
        @keyframes shakeEpic {
          0% { transform: translate(1px, 1px) rotate(0deg); }
          10% { transform: translate(-1px, -2px) rotate(-1deg); }
          20% { transform: translate(-3px, 0px) rotate(1deg); }
          30% { transform: translate(3px, 2px) rotate(0deg); }
          40% { transform: translate(1px, -1px) rotate(1deg); }
          50% { transform: translate(-1px, 2px) rotate(-1deg); }
          60% { transform: translate(-3px, 1px) rotate(0deg); }
          70% { transform: translate(3px, 1px) rotate(-1deg); }
          80% { transform: translate(-1px, -1px) rotate(1deg); }
          90% { transform: translate(1px, 2px) rotate(0deg); }
          100% { transform: translate(1px, -2px) rotate(-1deg); }
        }
        @keyframes shakeApocalyptic {
          0% { transform: translate(3px, 3px) rotate(0deg); }
          10% { transform: translate(-3px, -4px) rotate(-2deg); }
          20% { transform: translate(-6px, 0px) rotate(2deg); }
          30% { transform: translate(6px, 4px) rotate(0deg); }
          40% { transform: translate(3px, -3px) rotate(2deg); }
          50% { transform: translate(-3px, 4px) rotate(-2deg); }
          60% { transform: translate(-6px, 3px) rotate(0deg); }
          70% { transform: translate(6px, 3px) rotate(-2deg); }
          80% { transform: translate(-3px, -3px) rotate(2deg); }
          90% { transform: translate(3px, 4px) rotate(0deg); }
          100% { transform: translate(3px, -4px) rotate(-2deg); }
        }
        @keyframes spinRift {
          0% { transform: rotate(0deg) scale(1); }
          50% { transform: rotate(180deg) scale(1.2); }
          100% { transform: rotate(360deg) scale(1); }
        }
        @keyframes pulseRift {
          0% { box-shadow: 0 0 50px currentColor; }
          50% { box-shadow: 0 0 150px currentColor; }
          100% { box-shadow: 0 0 50px currentColor; }
        }

        .rift-container {
          position: relative;
          width: 300px;
          height: 300px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .rift-container.epic {
          animation: shakeEpic 0.2s infinite;
        }

        .rift-container.apocalyptic {
          animation: shakeApocalyptic 0.1s infinite;
        }

        .rift-core {
          position: absolute;
          width: 50%;
          height: 50%;
          background: #fff;
          border-radius: 50%;
          filter: blur(20px);
        }

        .rift-aura {
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          animation: spinRift 4s linear infinite, pulseRift 2s ease-in-out infinite;
          opacity: 0.8;
        }

        .standard .rift-aura {
          background: radial-gradient(circle, rgba(157,78,221,0.8) 0%, rgba(64,96,200,0.4) 50%, transparent 100%);
          color: #9d4edd;
        }

        .epic .rift-aura {
          background: radial-gradient(circle, rgba(201,168,76,0.8) 0%, rgba(157,78,221,0.4) 50%, transparent 100%);
          color: #c9a84c;
        }

        .apocalyptic .rift-aura {
          background: radial-gradient(circle, rgba(255,0,0,0.8) 0%, rgba(100,0,0,0.6) 50%, transparent 100%);
          color: #ff0000;
        }

        .rift-lightning-gold {
          position: absolute;
          width: 150%;
          height: 150%;
          background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M50,0 L40,40 L90,30 L50,100 L60,60 L10,70 Z" fill="none" stroke="%23c9a84c" stroke-width="2" filter="blur(2px)"/></svg>');
          animation: spinRift 1s linear infinite reverse;
          opacity: 0.6;
        }

        .rift-lightning-red {
          position: absolute;
          width: 200%;
          height: 200%;
          background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M50,0 L40,40 L90,30 L50,100 L60,60 L10,70 Z" fill="none" stroke="%23ff0000" stroke-width="4" filter="blur(3px)"/></svg>');
          animation: spinRift 0.5s linear infinite reverse;
          opacity: 0.8;
        }
      `}</style>
    </div>
  )
}
