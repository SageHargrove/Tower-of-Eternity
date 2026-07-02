import React, { useState, useEffect, useCallback } from 'react'
import HeroCard from './HeroCard'
import { EquipmentTypeIcon } from './EquipmentTypeIcon'
import { playClick } from '../audio'

// Star rarity -> glow color (mirrors index.css --star*; 7★ gets white-hot
// since the rainbow lives on the card itself).
const STAR_GLOW = {
  1: '#ffffff', 2: '#4dff4d', 3: '#1e90ff', 4: '#b84dff',
  5: '#ffb300', 6: '#ff3333', 7: '#f0f0ff',
}

// Equipment letter grades bucketed onto the same 1-7 "impact" scale so
// equipment pulls reuse the hero glow/tarot tiers.
function equipStarEquivalent(rarity) {
  const r = rarity || 'D'
  if (r === 'Z' || r.startsWith('SS')) return 7
  if (r.startsWith('S')) return 6
  if (r.startsWith('A')) return 5
  if (r.startsWith('B')) return 4
  if (r.startsWith('C')) return 3
  return 1
}

function itemStar(item) {
  return item.is_equipment ? equipStarEquivalent(item.rarity) : (item.birth_star || 1)
}

// Star tier -> tarot card-back art. Equipment gets its own back if
// tarot_equipment.png exists (art hook), falling back to the tiered backs.
function tarotBack(star) {
  if (star >= 7) return 'tarot_transcendent'
  if (star >= 6) return 'tarot_mythic'
  if (star >= 4) return 'tarot_epic'
  if (star >= 3) return 'tarot_rare'
  return 'tarot_common'
}

// The face-down side of a card: tarot art with an ornate CSS fallback.
function CardBack({ item }) {
  const star = itemStar(item)
  const backs = item.is_equipment ? ['tarot_equipment', tarotBack(star)] : [tarotBack(star)]
  const [idx, setIdx] = useState(0)
  return (
    <div className="tarot-back-art">
      <div className="tarot-back-fallback">
        <div className="tarot-back-border" />
        <img src="/icons/magic_synthesis.png" alt="" draggable={false} style={{ width: '55%', opacity: 0.9 }}
          onError={(e) => { e.target.style.display = 'none' }} />
      </div>
      {idx < backs.length && (
        <img
          src={`/icons/${backs[idx]}.png`}
          alt=""
          draggable={false}
          onError={() => setIdx(i => i + 1)}
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', borderRadius: 10 }}
        />
      )}
    </div>
  )
}

// The revealed face for an equipment pull (heroes use their composited
// card image / HeroCard instead).
function EquipmentFace({ item, glow }) {
  return (
    <div style={{
      width: '100%', height: '100%', borderRadius: 8, border: `1px solid ${glow}`,
      background: 'linear-gradient(160deg, var(--bg-card), var(--bg-panel))',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 8, padding: 8, textAlign: 'center',
    }}>
      <EquipmentTypeIcon item={item} fontSize="3rem" />
      <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.78rem', color: 'var(--text-hi)', lineHeight: 1.3 }}>{item.name}</div>
      <div style={{ color: glow, fontSize: '0.72rem', fontFamily: 'Cinzel, serif', letterSpacing: '0.1em' }}>{item.rarity} RANK</div>
    </div>
  )
}

// NOTE on structure: the glow drop-shadow lives on a WRAPPER around the 3D
// card, never on the card itself — a CSS filter on the transformed element
// forces transform-style back to flat, which breaks backface-visibility and
// with it the entire flip (confirmed bug: cards wobbled but never revealed).
function FlipCard({ item, flipped, onFlip, width, height, revealed }) {
  const glow = STAR_GLOW[itemStar(item)] || '#ffffff'
  return (
    <div
      className={`tarot-glow ${flipped ? 'tarot-glow-flipped' : ''}`}
      style={{ '--glow': glow, cursor: flipped ? 'default' : 'pointer', position: 'relative' }}
      onClick={!flipped ? onFlip : undefined}
    >
      <div style={{ perspective: '1200px' }}>
        <div className={`tarot-card ${flipped ? 'tarot-flipped' : ''}`} style={{ width, height }}>
          <div className="tarot-face tarot-front">
            <CardBack item={item} />
          </div>
          <div className="tarot-face tarot-backside">
            {revealed}
          </div>
        </div>
      </div>
      {flipped && <div className="tarot-burst" style={{ '--glow': glow }} />}
    </div>
  )
}

// Single-pull reveal: one large card, click to flip into the full HeroCard
// (or equipment face).
function SingleReveal({ item, onDone }) {
  const [flipped, setFlipped] = useState(false)
  const high = itemStar(item) >= 4

  const flip = useCallback(() => {
    setFlipped(f => {
      if (!f) playClick()
      return true
    })
  }, [])

  useEffect(() => {
    if (!flipped) {
      const t = setTimeout(flip, 2800)
      return () => clearTimeout(t)
    }
    const t = setTimeout(onDone, high ? 3400 : 2400)
    return () => clearTimeout(t)
  }, [flipped, flip, onDone, high])

  const glow = STAR_GLOW[itemStar(item)] || '#ffffff'

  return (
    <div style={{ margin: 'auto' }}>
      <FlipCard
        item={item}
        flipped={flipped}
        onFlip={flip}
        width={300}
        height={item.is_equipment ? 440 : undefined}
        revealed={item.is_equipment
          ? <div style={{ position: 'absolute', inset: 0 }}><EquipmentFace item={item} glow={glow} /></div>
          : <HeroCard hero={item} showFull={false} />}
      />
      {!flipped && (
        <div className="tarot-hint" style={{ position: 'static', marginTop: '0.8rem' }}>Click to reveal</div>
      )}
    </div>
  )
}

// Multi-pull spread: every card dealt face-down at once in a 3-4-3 layout
// over the summoning array. Click each to flip, or Reveal All.
function TarotSpread({ results, onComplete }) {
  const [flipped, setFlipped] = useState(() => new Set())

  const keyOf = (item, i) => item.id ?? `i${i}`
  const columns = results.length >= 8
    ? [results.slice(0, 3), results.slice(3, 7), results.slice(7, 10)]
    : [results]
  const allFlipped = flipped.size >= results.length

  function flipOne(key) {
    playClick()
    setFlipped(prev => new Set(prev).add(key))
  }

  function revealAll() {
    playClick()
    setFlipped(new Set(results.map((item, i) => keyOf(item, i))))
  }

  let flatIndex = -1

  return (
    <div style={{ position: 'relative', width: '100%', minHeight: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
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

      {/* 3-4-3 spread: three vertical columns; the middle holds 4 cards so
          it's naturally taller — cards sized so a 4-card column fits. */}
      <div style={{ display: 'flex', gap: '1.4rem', alignItems: 'center', justifyContent: 'center', position: 'relative', zIndex: 2, padding: '1rem', flexWrap: 'wrap' }}>
        {columns.map((col, ci) => (
          <div key={ci} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', justifyContent: 'center', flexWrap: columns.length === 1 ? 'wrap' : 'nowrap', ...(columns.length === 1 ? { flexDirection: 'row', maxWidth: 900 } : {}) }}>
            {col.map((item) => {
              flatIndex += 1
              const key = keyOf(item, flatIndex)
              const glow = STAR_GLOW[itemStar(item)] || '#ffffff'
              return (
                <FlipCard
                  key={key}
                  item={item}
                  flipped={flipped.has(key)}
                  onFlip={() => flipOne(key)}
                  width={132}
                  height={198}
                  revealed={
                    <div style={{ position: 'absolute', inset: 0 }}>
                      {item.is_equipment ? (
                        <EquipmentFace item={item} glow={glow} />
                      ) : item.portrait_path ? (
                        <img
                          src={`/heroes/${item.id}/card-image?mini=true`}
                          onError={(e) => { e.target.onerror = null; e.target.src = `/${item.portrait_path}` }}
                          draggable={false}
                          style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center top', borderRadius: 8, border: `1px solid ${glow}` }}
                          alt={item.name}
                        />
                      ) : (
                        <div style={{
                          width: '100%', height: '100%', borderRadius: 8, border: `1px solid ${glow}`,
                          background: 'var(--bg-card)', display: 'flex', flexDirection: 'column',
                          alignItems: 'center', justifyContent: 'center', gap: 6, padding: 6, textAlign: 'center',
                        }}>
                          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.8rem', color: 'var(--text-hi)' }}>{item.name}</div>
                          <div style={{ color: glow, fontSize: '0.7rem' }}>{'★'.repeat(item.birth_star || 1)}</div>
                        </div>
                      )}
                    </div>
                  }
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
  // No pre-reveal buildup phase — straight to the cards.
  const isSpread = results.length > 1

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: '#000', zIndex: 9999,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
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

      {isSpread ? (
        <TarotSpread results={results} onComplete={onComplete} />
      ) : results.length === 1 ? (
        <SingleReveal item={results[0]} onDone={onComplete} />
      ) : null}

      <style>{`
        @keyframes tarot-idle {
          0%   { transform: rotateY(-14deg) translateY(0); }
          25%  { transform: rotateY(0deg) translateY(-7px); }
          50%  { transform: rotateY(14deg) translateY(0); }
          75%  { transform: rotateY(0deg) translateY(7px); }
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
        @keyframes array-spin {
          from { transform: translate(-50%, -50%) rotate(0deg); }
          to   { transform: translate(-50%, -50%) rotate(360deg); }
        }

        /* Glow lives HERE (a plain wrapper), never on .tarot-card — a filter
           on the 3D element flattens preserve-3d and breaks the flip. */
        .tarot-glow {
          filter: drop-shadow(0 0 16px var(--glow));
        }
        .tarot-glow-flipped {
          filter: drop-shadow(0 0 10px var(--glow));
        }

        .tarot-card {
          position: relative;
          transform-style: preserve-3d;
          animation: tarot-idle 4.5s ease-in-out infinite;
          transition: transform 0.75s cubic-bezier(0.3, 0, 0.2, 1);
        }
        .tarot-card.tarot-flipped {
          animation: none;
          transform: rotateY(180deg);
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
          transform: rotateY(0deg);
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
          text-align: center;
          font-family: 'Cinzel', serif;
          font-size: 0.75rem;
          letter-spacing: 0.2em;
          color: rgba(255, 255, 255, 0.75);
          animation: tarot-hint-pulse 1.6s ease-in-out infinite;
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
      `}</style>
    </div>
  )
}
