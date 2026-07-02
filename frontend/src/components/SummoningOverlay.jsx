import React, { useState, useEffect, useCallback } from 'react'
import HeroCard from './HeroCard'
import { playClick } from '../audio'

// Star rarity -> glow color for card glow / burst (mirrors index.css --star*;
// 7★ gets white-hot since the rainbow lives on the card itself).
const STAR_GLOW = {
  1: '#ffffff', 2: '#4dff4d', 3: '#1e90ff', 4: '#b84dff',
  5: '#ffb300', 6: '#ff3333', 7: '#f0f0ff',
}

// Star rarity -> tarot card-back art (frontend/public/icons/tarot_*.png).
// The back subtly telegraphs the pull's tier before the flip.
function tarotBack(star) {
  if (star >= 7) return 'tarot_transcendent'
  if (star >= 6) return 'tarot_mythic'
  if (star >= 4) return 'tarot_epic'
  if (star >= 3) return 'tarot_rare'
  return 'tarot_common'
}

// The face-down side of a card: tarot art with an ornate CSS fallback.
function CardBack({ hero }) {
  return (
    <div className="tarot-back-art">
      <div className="tarot-back-fallback">
        <div className="tarot-back-border" />
        <img src="/icons/magic_synthesis.png" alt="" draggable={false} style={{ width: '55%', opacity: 0.9 }}
          onError={(e) => { e.target.style.display = 'none' }} />
      </div>
      <img
        src={`/icons/${tarotBack(hero.birth_star)}.png`}
        alt=""
        draggable={false}
        onError={(e) => { e.target.style.display = 'none' }}
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', borderRadius: 10 }}
      />
    </div>
  )
}

// Single-pull reveal: one large floating card, click (or auto) to flip into
// the full HeroCard.
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

  useEffect(() => {
    if (!flipped) {
      const t = setTimeout(flip, 2600)
      return () => clearTimeout(t)
    }
    const t = setTimeout(onDone, high ? 3200 : 2200)
    return () => clearTimeout(t)
  }, [flipped, flip, onDone, high])

  return (
    <div style={{ perspective: '1400px', margin: 'auto', cursor: flipped ? 'default' : 'pointer', position: 'relative' }} onClick={flip}>
      <div className={`tarot-card ${flipped ? 'tarot-flipped' : ''}`} style={{ '--glow': glow, width: 300 }}>
        <div className="tarot-face tarot-front">
          <CardBack hero={hero} />
          {!flipped && <div className="tarot-hint">Click to reveal</div>}
        </div>
        <div className="tarot-face tarot-backside">
          <HeroCard hero={hero} showFull={false} />
        </div>
      </div>
      {flipped && <div className="tarot-burst" style={{ '--glow': glow }} />}
    </div>
  )
}

// One card in the 10-pull spread — smaller, flips to the hero's composited
// card image (name/stars/medallion baked in) instead of the full component.
function SpreadCard({ hero, flipped, onFlip }) {
  const glow = STAR_GLOW[hero.birth_star] || '#ffffff'
  return (
    <div style={{ perspective: '1000px', cursor: flipped ? 'default' : 'pointer', position: 'relative' }} onClick={!flipped ? onFlip : undefined}>
      <div
        className={`tarot-card tarot-spread ${flipped ? 'tarot-flipped' : ''}`}
        style={{ '--glow': glow, width: 148, height: 222, animationDelay: `${(hero.id || 0) % 7 * -0.6}s` }}
      >
        <div className="tarot-face tarot-front">
          <CardBack hero={hero} />
        </div>
        <div className="tarot-face tarot-backside" style={{ position: 'absolute', inset: 0 }}>
          {hero.portrait_path ? (
            <img
              src={`/heroes/${hero.id}/card-image?mini=true`}
              onError={(e) => { e.target.onerror = null; e.target.src = `/${hero.portrait_path}` }}
              draggable={false}
              style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center top', borderRadius: 8, border: `1px solid ${glow}` }}
              alt={hero.name}
            />
          ) : (
            <div style={{
              width: '100%', height: '100%', borderRadius: 8, border: `1px solid ${glow}`,
              background: 'var(--bg-card)', display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 6, padding: 6, textAlign: 'center',
            }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.8rem', color: 'var(--text-hi)' }}>{hero.name}</div>
              <div style={{ color: glow, fontSize: '0.7rem' }}>{'★'.repeat(hero.birth_star)}</div>
            </div>
          )}
        </div>
      </div>
      {flipped && <div className="tarot-burst" style={{ '--glow': glow, inset: -20 }} />}
    </div>
  )
}

// Full 10-pull spread: all cards on screen at once over a giant summoning
// array, arranged 3-4-3. Click cards individually, or Reveal All.
function TarotSpread({ results, onComplete }) {
  const [flipped, setFlipped] = useState(() => new Set())

  const columns = [results.slice(0, 3), results.slice(3, 7), results.slice(7, 10)]
  const allFlipped = flipped.size >= results.length

  function flipOne(id) {
    playClick()
    setFlipped(prev => new Set(prev).add(id))
  }

  function revealAll() {
    playClick()
    setFlipped(new Set(results.map((h, i) => h.id ?? i)))
  }

  return (
    <div style={{ position: 'relative', width: '100%', minHeight: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      {/* Summoning array looming behind the spread */}
      <img
        src="/icons/summoning_array.png"
        alt=""
        draggable={false}
        onError={(e) => { e.target.style.display = 'none' }}
        style={{
          position: 'fixed', top: '50%', left: '50%', width: '105vmin', height: '105vmin',
          transform: 'translate(-50%, -50%)', objectFit: 'contain', opacity: 0.4,
          pointerEvents: 'none', animation: 'array-spin 90s linear infinite',
        }}
      />

      <div style={{ display: 'flex', gap: '1.6rem', alignItems: 'center', justifyContent: 'center', position: 'relative', zIndex: 2, padding: '1rem' }}>
        {columns.map((col, ci) => (
          <div key={ci} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            {col.map((hero, i) => {
              const key = hero.id ?? `c${ci}-${i}`
              return (
                <SpreadCard
                  key={key}
                  hero={hero}
                  flipped={flipped.has(hero.id ?? results.indexOf(hero))}
                  onFlip={() => flipOne(hero.id ?? results.indexOf(hero))}
                />
              )
            })}
          </div>
        ))}
      </div>

      <div style={{ position: 'relative', zIndex: 2, marginTop: '1.2rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        {!allFlipped ? (
          <>
            <div className="text-dim" style={{ fontFamily: 'Cinzel, serif', letterSpacing: '0.1em', fontSize: '0.85rem' }}>
              {flipped.size} / {results.length} revealed — click a card
            </div>
            <button className="btn btn-gold" onClick={revealAll}>Reveal All</button>
          </>
        ) : (
          <button className="btn btn-gold" style={{ padding: '0.7rem 2.2rem', fontSize: '1rem', boxShadow: '0 0 15px rgba(201,168,76,0.4)' }} onClick={onComplete}>
            Continue
          </button>
        )}
      </div>
    </div>
  )
}

export default function SummoningOverlay({ results, onComplete }) {
  const [phase, setPhase] = useState('rift') // 'rift' -> 'reveal'
  const [currentIndex, setCurrentIndex] = useState(0)

  const maxStar = results.length > 0 ? Math.max(...results.map(h => h.birth_star)) : 1
  const isSpread = results.length > 1

  let riftType = 'standard'
  if (maxStar >= 6) riftType = 'apocalyptic'
  else if (maxStar >= 4) riftType = 'epic'

  useEffect(() => {
    const timer = setTimeout(() => {
      setPhase('reveal')
    }, riftType === 'apocalyptic' ? 4000 : riftType === 'epic' ? 3000 : 2000)
    return () => clearTimeout(timer)
  }, [riftType])

  useEffect(() => {
    if (!isSpread && phase === 'reveal' && currentIndex >= results.length) {
      const timer = setTimeout(onComplete, 400)
      return () => clearTimeout(timer)
    }
  }, [phase, currentIndex, results.length, onComplete, isSpread])

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: '#000', zIndex: 9999,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start',
      overflowY: 'auto',
      padding: '2rem 0'
    }}>
      <button
        className="btn"
        onClick={onComplete}
        style={{ position: 'absolute', top: 20, right: 20, zIndex: 10000, background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border)' }}
      >
        Skip All ⏭
      </button>

      {phase === 'rift' && (
        <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
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
        isSpread ? (
          <TarotSpread results={results} onComplete={onComplete} />
        ) : currentIndex < results.length ? (
          <TarotReveal
            key={results[currentIndex].id ?? currentIndex}
            hero={results[currentIndex]}
            onDone={() => setCurrentIndex(c => c + 1)}
          />
        ) : null
      )}

      {/* Global styles for rift + tarot animations */}
      <style>{`
        /* ── Tarot flip ─────────────────────────────────────────── */
        @keyframes tarot-idle {
          0%   { transform: rotateY(-14deg) translateY(0); }
          25%  { transform: rotateY(0deg) translateY(-8px); }
          50%  { transform: rotateY(14deg) translateY(0); }
          75%  { transform: rotateY(0deg) translateY(8px); }
          100% { transform: rotateY(-14deg) translateY(0); }
        }
        @keyframes tarot-idle-soft {
          0%   { transform: rotateY(-6deg) translateY(0); }
          50%  { transform: rotateY(6deg) translateY(-5px); }
          100% { transform: rotateY(-6deg) translateY(0); }
        }
        @keyframes tarot-burst-anim {
          0%   { opacity: 0.9; transform: scale(0.3); }
          100% { opacity: 0; transform: scale(3.2); }
        }
        @keyframes tarot-hint-pulse {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }
        @keyframes array-spin {
          from { transform: translate(-50%, -50%) rotate(0deg); }
          to   { transform: translate(-50%, -50%) rotate(360deg); }
        }

        .tarot-card {
          position: relative;
          transform-style: preserve-3d;
          animation: tarot-idle 4.5s ease-in-out infinite;
          transition: transform 0.75s cubic-bezier(0.3, 0, 0.2, 1);
          filter: drop-shadow(0 0 25px var(--glow));
        }
        .tarot-card.tarot-spread {
          animation: tarot-idle-soft 5s ease-in-out infinite;
          filter: drop-shadow(0 0 12px var(--glow));
        }
        .tarot-card.tarot-flipped {
          animation: none;
          transform: rotateY(180deg);
          filter: drop-shadow(0 0 14px var(--glow));
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
          25% { transform: translate(-3px, 0px) rotate(1deg); }
          50% { transform: translate(-1px, 2px) rotate(-1deg); }
          75% { transform: translate(3px, 1px) rotate(-1deg); }
          100% { transform: translate(1px, -2px) rotate(-1deg); }
        }
        @keyframes shakeApocalyptic {
          0% { transform: translate(3px, 3px) rotate(0deg); }
          25% { transform: translate(-6px, 0px) rotate(2deg); }
          50% { transform: translate(-3px, 4px) rotate(-2deg); }
          75% { transform: translate(6px, 3px) rotate(-2deg); }
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
        .rift-container.epic { animation: shakeEpic 0.2s infinite; }
        .rift-container.apocalyptic { animation: shakeApocalyptic 0.1s infinite; }

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
