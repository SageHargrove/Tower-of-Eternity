import React, { useState, useEffect, useCallback } from 'react'
import HeroCard from './HeroCard'
import { playClick } from '../audio'

// Star rarity -> glow color for the card back / burst (mirrors index.css
// --star* vars; 7★ gets white-hot since the rainbow lives on the card itself).
const STAR_GLOW = {
  1: '#ffffff', 2: '#4dff4d', 3: '#1e90ff', 4: '#b84dff',
  5: '#ffb300', 6: '#ff3333', 7: '#f0f0ff',
}

// One hero's tarot-flip reveal: a face-down card floats and sways in 3D,
// then flips (click, or auto after a beat) with a star-colored burst to
// reveal the real HeroCard. Static art + CSS transforms only.
// Card-back art hook: drop frontend/public/icons/card_back.png and it
// replaces the CSS-drawn ornate back automatically.
function TarotReveal({ hero, onDone }) {
  const [flipped, setFlipped] = useState(false)
  const glow = STAR_GLOW[hero.birth_star] || '#ffffff'
  const high = hero.birth_star >= 4

  const flip = useCallback(() => {
    setFlipped(f => {
      if (!f) playClick()
      return true
    })
  }, [])

  // Auto-flip if the player doesn't click, then advance after a viewing beat.
  useEffect(() => {
    if (!flipped) {
      const t = setTimeout(flip, 2600)
      return () => clearTimeout(t)
    }
    const t = setTimeout(onDone, high ? 3200 : 2200)
    return () => clearTimeout(t)
  }, [flipped, flip, onDone, high])

  return (
    <div style={{ perspective: '1400px', margin: 'auto', cursor: flipped ? 'default' : 'pointer' }} onClick={flip}>
      <div
        className={`tarot-card ${flipped ? 'tarot-flipped' : ''}`}
        style={{ '--glow': glow }}
      >
        {/* Back face (what you see before the flip) */}
        <div className="tarot-face tarot-front">
          <div className="tarot-back-art">
            <img
              src="/icons/card_back.png"
              alt=""
              draggable={false}
              onError={(e) => { e.target.style.display = 'none' }}
              style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', borderRadius: 10 }}
            />
            {/* CSS-drawn ornate fallback beneath the (optional) art */}
            <div className="tarot-back-fallback">
              <div className="tarot-back-border" />
              <img src="/icons/magic_synthesis.png" alt="" draggable={false} style={{ width: 110, height: 110, opacity: 0.9 }}
                onError={(e) => { e.target.style.display = 'none' }} />
            </div>
          </div>
          {!flipped && <div className="tarot-hint">Click to reveal</div>}
        </div>

        {/* Front face (the hero) */}
        <div className="tarot-face tarot-backside">
          <HeroCard hero={hero} showFull={false} />
        </div>
      </div>

      {flipped && <div className="tarot-burst" style={{ '--glow': glow }} />}
    </div>
  )
}

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
    if (phase === 'reveal' && currentIndex >= results.length) {
      const timer = setTimeout(onComplete, 400)
      return () => clearTimeout(timer)
    }
  }, [phase, currentIndex, results.length, onComplete])

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

      {phase === 'reveal' && results.length > 1 && (
        <div style={{ position: 'absolute', top: 24, left: 24, zIndex: 10000, fontFamily: 'Cinzel, serif', color: 'var(--text-dim)', letterSpacing: '0.15em' }}>
          {Math.min(currentIndex + 1, results.length)} / {results.length}
        </div>
      )}

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

      {phase === 'reveal' && currentIndex < results.length && (
        <TarotReveal
          key={results[currentIndex].id ?? currentIndex}
          hero={results[currentIndex]}
          onDone={() => setCurrentIndex(c => c + 1)}
        />
      )}

      {/* Global styles for rift + tarot animations */}
      <style>{`
        @keyframes zoomIn {
          from { transform: scale(0.5); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }

        /* ── Tarot flip ─────────────────────────────────────────── */
        @keyframes tarot-idle {
          0%   { transform: rotateY(-14deg) translateY(0); }
          25%  { transform: rotateY(0deg) translateY(-8px); }
          50%  { transform: rotateY(14deg) translateY(0); }
          75%  { transform: rotateY(0deg) translateY(8px); }
          100% { transform: rotateY(-14deg) translateY(0); }
        }
        @keyframes tarot-burst-anim {
          0%   { opacity: 0.9; transform: scale(0.3); }
          100% { opacity: 0; transform: scale(3.2); }
        }
        @keyframes tarot-hint-pulse {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }

        .tarot-card {
          position: relative;
          width: 300px;
          transform-style: preserve-3d;
          animation: tarot-idle 4.5s ease-in-out infinite;
          transition: transform 0.75s cubic-bezier(0.3, 0, 0.2, 1);
          filter: drop-shadow(0 0 25px var(--glow));
        }
        .tarot-card.tarot-flipped {
          animation: none;
          transform: rotateY(180deg);
          filter: drop-shadow(0 0 18px var(--glow));
        }

        .tarot-face {
          backface-visibility: hidden;
          -webkit-backface-visibility: hidden;
        }
        .tarot-front {
          position: absolute;
          inset: 0;
          z-index: 2;
          border-radius: 10px;
          overflow: hidden;
        }
        .tarot-backside {
          transform: rotateY(180deg);
        }

        .tarot-back-art {
          position: absolute;
          inset: 0;
          border-radius: 10px;
        }
        .tarot-back-fallback {
          position: absolute;
          inset: 0;
          border-radius: 10px;
          background:
            radial-gradient(ellipse 80% 60% at 50% 40%, rgba(80, 30, 130, 0.55), transparent 75%),
            linear-gradient(160deg, #14101e 0%, #0a0812 60%, #16112a 100%);
          border: 2px solid var(--glow);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .tarot-back-border {
          position: absolute;
          inset: 10px;
          border: 1px solid rgba(201, 168, 76, 0.5);
          border-radius: 6px;
          pointer-events: none;
        }

        .tarot-hint {
          position: absolute;
          bottom: 14px;
          left: 0; right: 0;
          text-align: center;
          font-family: 'Cinzel', serif;
          font-size: 0.75rem;
          letter-spacing: 0.2em;
          color: rgba(255, 255, 255, 0.75);
          animation: tarot-hint-pulse 1.6s ease-in-out infinite;
          z-index: 3;
        }

        .tarot-burst {
          position: absolute;
          inset: -40px;
          border-radius: 50%;
          pointer-events: none;
          background: radial-gradient(circle, var(--glow) 0%, transparent 65%);
          animation: tarot-burst-anim 0.8s ease-out forwards;
          z-index: 1;
        }

        /* ── Rift (pre-reveal buildup) ──────────────────────────── */
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
