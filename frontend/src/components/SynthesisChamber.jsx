import React, { useState } from 'react'
import { synthesizeHero } from '../api/client'

// Full-screen ritual chamber for hero synthesis. Fully opaque — the roster
// page shouldn't bleed through a rite. Drag heroes from the pool onto the
// pedestals; the rite grants the vessel XP (through the normal leveling
// pipeline), never raw stats.
//
// Background art hook: drop an image at
//   backend/static/facilities/Synthesis Chamber.png
// and it will render automatically behind the chamber (same convention as
// facility banners).

// Mirrors routers/heroes.py synthesize_hero's XP formula so the preview
// matches what the rite actually grants.
function previewXp(sacrifice, resonant) {
  const base = Math.floor((sacrifice.xp || 0) * 0.5) + 30 * sacrifice.birth_star * sacrifice.level
  return resonant ? base * 2 : base
}

function Pedestal({ hero, role, onClear, onDropHero, synthesizing }) {
  const isTarget = role === 'target'
  const accent = isTarget ? 'var(--gold)' : 'var(--red)'
  const label = isTarget ? 'The Vessel' : 'The Offering'
  const hint = isTarget ? 'Receives the power' : 'Consumed — permanently'
  const [dragOver, setDragOver] = useState(false)

  const anim = synthesizing ? (isTarget ? 'synth-empower 1s ease-in-out infinite' : 'synth-consume 2.2s ease-in forwards') : 'none'

  return (
    <div style={{ width: 250, textAlign: 'center' }}>
      <div style={{ fontFamily: 'Cinzel, serif', letterSpacing: '0.15em', textTransform: 'uppercase', fontSize: '0.85rem', color: accent, marginBottom: '0.6rem' }}>
        {label}
      </div>
      <div
        onClick={hero && !synthesizing ? onClear : undefined}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          const heroId = e.dataTransfer.getData('heroId')
          if (heroId && !synthesizing) onDropHero(Number(heroId))
        }}
        title={hero && !synthesizing ? 'Click to remove' : undefined}
        style={{
          width: 200, height: 290, margin: '0 auto', borderRadius: 8,
          border: hero ? `2px solid ${accent}` : `2px dashed ${dragOver ? accent : 'var(--border-hi)'}`,
          boxShadow: hero
            ? `0 0 30px ${isTarget ? 'rgba(201,168,76,0.45)' : 'rgba(192,64,64,0.45)'}`
            : dragOver ? `0 0 20px ${isTarget ? 'rgba(201,168,76,0.35)' : 'rgba(192,64,64,0.35)'}` : 'none',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: dragOver ? 'rgba(80,30,130,0.25)' : 'rgba(0,0,0,0.55)',
          cursor: hero && !synthesizing ? 'pointer' : 'default',
          overflow: 'hidden', position: 'relative',
          transition: 'box-shadow 0.3s, border-color 0.3s, background 0.2s',
        }}
      >
        {hero ? (
          hero.portrait_path ? (
            <img
              src={`/heroes/${hero.id}/card-image?mini=true`}
              onError={(e) => { e.target.onerror = null; e.target.src = `/${hero.portrait_path}` }}
              draggable={false}
              style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center top', animation: anim }}
              alt={hero.name}
            />
          ) : (
            <div style={{ fontFamily: 'Cinzel, serif', color: accent, padding: '1rem', animation: anim }}>{hero.name}</div>
          )
        ) : (
          <div className="text-dim" style={{ fontStyle: 'italic', fontSize: '0.85rem', padding: '1rem' }}>
            Drag a hero here
          </div>
        )}
      </div>
      <div style={{ marginTop: '0.6rem', minHeight: '2.6rem' }}>
        {hero ? (
          <>
            <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--text-hi)' }}>{hero.name}</div>
            <div className="text-dim" style={{ fontSize: '0.75rem' }}>
              Lv.{hero.level} {hero.hero_class} · {(hero.current_star || hero.birth_star)}★
            </div>
          </>
        ) : (
          <div className="text-dim" style={{ fontSize: '0.75rem', fontStyle: 'italic' }}>{hint}</div>
        )}
      </div>
    </div>
  )
}

export default function SynthesisChamber({ heroes, onClose, onComplete }) {
  const [targetId, setTargetId] = useState(null)
  const [sacrificeId, setSacrificeId] = useState(null)
  const [synthesizing, setSynthesizing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const alive = heroes.filter(h => h.is_alive)
  const target = alive.find(h => h.id === targetId) || null
  const sacrifice = alive.find(h => h.id === sacrificeId) || null

  const resonant = target && sacrifice && target.hero_class === sacrifice.hero_class && target.hero_class !== 'Classless'
  const xpGain = sacrifice ? previewXp(sacrifice, resonant) : 0

  function placeOnPedestal(role, heroId) {
    setError(null)
    setResult(null)
    if (role === 'target') {
      if (heroId === sacrificeId) setSacrificeId(null)
      setTargetId(heroId)
    } else {
      if (heroId === targetId) setTargetId(null)
      setSacrificeId(heroId)
    }
  }

  async function beginRite() {
    if (!target || !sacrifice) return
    setSynthesizing(true)
    setError(null)
    try {
      // Hold the rite for at least the animation's length — the consume/
      // empower keyframes are the whole ceremony; an instant response
      // made it feel dead.
      const [res] = await Promise.all([
        synthesizeHero(target.id, sacrifice.id),
        new Promise(r => setTimeout(r, 2300)),
      ])
      setResult(res)
      setTargetId(null)
      setSacrificeId(null)
      if (onComplete) onComplete()
    } catch (e) {
      setError(e.message)
    } finally {
      setSynthesizing(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 900,
      background: '#060309',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      overflowY: 'auto', padding: '2rem 1rem',
    }}>
      <style>{`
        @keyframes synth-hum {
          0%   { opacity: 0.75; filter: drop-shadow(0 0 8px rgba(160, 80, 255, 0.5)); transform: rotate(0deg); }
          50%  { opacity: 1; filter: drop-shadow(0 0 30px rgba(160, 80, 255, 1)); transform: rotate(180deg); }
          100% { opacity: 0.75; filter: drop-shadow(0 0 8px rgba(160, 80, 255, 0.5)); transform: rotate(360deg); }
        }
        @keyframes synth-idle {
          0%, 100% { filter: drop-shadow(0 0 6px rgba(160, 80, 255, 0.4)); }
          50% { filter: drop-shadow(0 0 14px rgba(160, 80, 255, 0.7)); }
        }
        @keyframes synth-consume {
          0%   { filter: none; opacity: 1; transform: translateX(0); }
          20%  { transform: translateX(-3px); }
          30%  { transform: translateX(3px); }
          40%  { transform: translateX(-3px); }
          50%  { transform: translateX(3px); filter: saturate(0.6) brightness(1.1); }
          75%  { filter: saturate(0.2) brightness(1.6) hue-rotate(260deg); opacity: 0.7; }
          100% { filter: saturate(0) brightness(3); opacity: 0; transform: scale(0.92); }
        }
        @keyframes synth-empower {
          0%, 100% { filter: brightness(1); }
          50% { filter: brightness(1.35) saturate(1.2) drop-shadow(0 0 18px rgba(201,168,76,0.9)); }
        }
        @keyframes synth-result-in {
          from { opacity: 0; transform: scale(0.85); }
          to   { opacity: 1; transform: scale(1); }
        }
      `}</style>

      {/* Ambient glow layered over the opaque base */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none',
        background: 'radial-gradient(ellipse 70% 60% at 50% 38%, rgba(80, 30, 130, 0.4), transparent 70%)',
      }} />

      {/* Optional backdrop art — hidden until the file exists */}
      <img
        src="/static/facilities/Synthesis Chamber.png"
        alt=""
        onError={(e) => { e.target.style.display = 'none' }}
        style={{ position: 'fixed', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.25, pointerEvents: 'none' }}
      />

      <div style={{ width: '100%', maxWidth: 1200, position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.3rem' }}>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', color: '#b06aff', textShadow: '0 0 15px rgba(160,80,255,0.5)' }}>
            ⚗ Synthesis Chamber
          </div>
          <button className="btn" onClick={onClose} disabled={synthesizing}>Leave the Chamber</button>
        </div>
        <div className="text-dim" style={{ fontStyle: 'italic', marginBottom: '2rem' }}>
          Two souls enter. One leaves stronger. The Tower does not refund what it takes.
        </div>

        {/* Pedestals + rite summary */}
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-start', gap: '2.5rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
          <Pedestal hero={target} role="target" synthesizing={synthesizing}
            onClear={() => setTargetId(null)} onDropHero={(id) => placeOnPedestal('target', id)} />

          <div style={{ width: 300, textAlign: 'center', paddingTop: '2.2rem' }}>
            <img
              src="/icons/magic_synthesis.png"
              alt=""
              draggable={false}
              style={{
                width: 90, height: 90, display: 'inline-block',
                animation: synthesizing ? 'synth-hum 1.2s linear infinite' : 'synth-idle 3s ease-in-out infinite',
              }}
              onError={(e) => { e.target.outerHTML = '<div style="font-size:2.4rem;color:#b06aff">◈</div>' }}
            />

            {result ? (
              <div style={{ marginTop: '1rem', border: '1px solid var(--green)', background: 'rgba(74,154,106,0.12)', borderRadius: 8, padding: '1.1rem', animation: 'synth-result-in 0.35s ease-out' }}>
                <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--green)', marginBottom: '0.4rem' }}>The Rite Is Complete</div>
                <div className="text-sm" style={{ lineHeight: 1.5 }}>{result.message || 'The offering has been consumed.'}</div>
                {result.xp_gained != null && (
                  <div style={{ marginTop: '0.5rem', fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)' }}>
                    +{result.xp_gained.toLocaleString()} XP
                  </div>
                )}
                <button className="btn" style={{ marginTop: '0.8rem' }} onClick={() => setResult(null)}>Synthesize Again</button>
              </div>
            ) : (
              <>
                {sacrifice && target ? (
                  <div style={{ marginTop: '0.8rem', border: '1px solid rgba(160,80,255,0.4)', background: 'rgba(80,30,130,0.15)', borderRadius: 8, padding: '0.9rem' }}>
                    <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: '#b06aff', marginBottom: '0.5rem' }}>
                      {target.name} will absorb
                    </div>
                    <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.6rem', color: 'var(--gold)', textShadow: '0 0 10px rgba(201,168,76,0.5)' }}>
                      +{xpGain.toLocaleString()} XP
                    </div>
                    {resonant && (
                      <div style={{ marginTop: '0.5rem', color: '#b06aff', fontFamily: 'Cinzel, serif', fontSize: '0.8rem', textShadow: '0 0 8px rgba(160,80,255,0.7)' }}>
                        ✦ EGO RESONANCE — XP doubled ✦
                      </div>
                    )}
                    <div style={{ marginTop: '0.5rem', fontSize: '0.7rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                      May also inherit one of {sacrifice.name}'s skills or traits.
                    </div>
                  </div>
                ) : (
                  <div className="text-dim" style={{ marginTop: '1rem', fontSize: '0.85rem', fontStyle: 'italic' }}>
                    Drag a vessel and an offering onto the pedestals.
                  </div>
                )}

                <button
                  className="btn"
                  disabled={!target || !sacrifice || synthesizing}
                  onClick={beginRite}
                  style={{
                    marginTop: '1rem', width: '100%', padding: '0.9rem', fontSize: '1rem',
                    border: '2px solid #b06aff', color: '#d0a0ff', borderRadius: 8,
                    background: 'rgba(80,30,130,0.25)',
                    boxShadow: target && sacrifice ? '0 0 20px rgba(160,80,255,0.4)' : 'none',
                  }}
                >
                  {synthesizing ? 'The chamber hums…' : 'Begin the Rite'}
                </button>

                {target && sacrifice && !synthesizing && (
                  <div style={{ marginTop: '0.6rem', fontSize: '0.72rem', color: 'var(--red)', fontStyle: 'italic' }}>
                    {sacrifice.name} will be lost forever. Every living hero will witness the sacrifice — expect trauma, stress, and shaken morale across the roster.
                  </div>
                )}
                {error && <div className="text-red" style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>{error}</div>}
              </>
            )}
          </div>

          <Pedestal hero={sacrifice} role="sacrifice" synthesizing={synthesizing}
            onClear={() => setSacrificeId(null)} onDropHero={(id) => placeOnPedestal('sacrifice', id)} />
        </div>

        {/* Hero pool — drag from here onto a pedestal */}
        <div className="section-header">Living Heroes — drag onto a pedestal</div>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(132px, 1fr))', gap: '1rem',
          maxHeight: '36vh', overflowY: 'auto', padding: '0.5rem 0.2rem',
        }}>
          {alive.map(h => {
            const role = h.id === targetId ? 'target' : h.id === sacrificeId ? 'sacrifice' : null
            const ring = role === 'target' ? 'var(--gold)' : role === 'sacrifice' ? 'var(--red)' : 'var(--border)'
            return (
              <div
                key={h.id}
                draggable={!synthesizing}
                onDragStart={(e) => e.dataTransfer.setData('heroId', String(h.id))}
                style={{ textAlign: 'center', cursor: synthesizing ? 'default' : 'grab', opacity: role ? 1 : 0.9 }}
                title={role ? `On the ${role} pedestal` : 'Drag onto a pedestal'}
              >
                {h.portrait_path ? (
                  <img
                    src={`/${h.portrait_path}`}
                    alt={h.name}
                    draggable={false}
                    style={{
                      width: 110, height: 110, borderRadius: '50%', objectFit: 'cover', objectPosition: 'center 15%',
                      border: `2px solid ${ring}`,
                      boxShadow: role ? `0 0 14px ${ring}` : 'none',
                      pointerEvents: 'none',
                    }}
                  />
                ) : (
                  <div style={{ width: 110, height: 110, borderRadius: '50%', margin: '0 auto', background: 'var(--bg-card)', border: `2px solid ${ring}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>?</div>
                )}
                <div style={{ fontSize: '0.78rem', marginTop: '0.3rem', color: role ? ring : 'var(--text-hi)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{h.name}</div>
                <div className="text-dim" style={{ fontSize: '0.68rem' }}>Lv.{h.level} · {(h.current_star || h.birth_star)}★ · {h.hero_class}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
