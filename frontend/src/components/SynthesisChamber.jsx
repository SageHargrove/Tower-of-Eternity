import React, { useState } from 'react'
import { synthesizeHero } from '../api/client'
import { playRiteHum } from '../audio'
import { useBgmScene } from '../useBgmScene'
import { CLASS_FAMILIES } from './HeroCard'

/*
 * SYNTHESIS CHAMBER — full-screen ritual (mockup "Tavern - Illuminated.dc.html",
 * screen label "Synthesis Chamber"). Center: the Vessel with XP projection.
 * Left: Ego Resonance + Inheritance. Right: The Roster Watches (morale/stress/
 * trauma costs). Bottom: the offerings rail (no soul limit) and the rite
 * actions. The rite grants the vessel XP through the normal leveling
 * pipeline, never raw stats.
 */

// Mirrors routers/heroes.py synthesize_hero's XP formula so the preview
// matches what the rite actually grants.
function previewXp(sacrifice, resonant) {
  const base = Math.floor((sacrifice.xp || 0) * 0.5) + 30 * sacrifice.birth_star * sacrifice.level
  return resonant ? base * 2 : base
}

function familyColor(cls) {
  for (const fam of Object.values(CLASS_FAMILIES)) {
    if (fam.members.includes(cls)) return fam.color
  }
  return '#c8a9f5'
}

// Diamond soul tile art — mini composite, falling back to a monogram.
function SoulDiamond({ hero, accent }) {
  const [failed, setFailed] = useState(false)
  const hasArt = hero.portrait_path && !hero.portrait_path.includes('default_')
  return (
    <span style={{ position: 'absolute', inset: 0, transform: 'rotate(45deg) scale(.72)', border: `1px solid ${accent}`, background: 'linear-gradient(135deg,#241018,#0c0710)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
      {hasArt && !failed ? (
        <img src={`/heroes/${hero.id}/card-image?mini=1`} alt={hero.name} draggable={false} onError={() => setFailed(true)}
          style={{ width: '142%', height: '142%', objectFit: 'cover', transform: 'rotate(-45deg)', flex: 'none' }} />
      ) : (
        <span style={{ transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 16, color: accent }}>{(hero.name || '?')[0]}</span>
      )}
    </span>
  )
}

const microStyle = { fontFamily: "'Cinzel',serif", letterSpacing: '.14em', fontSize: 9 }

export default function SynthesisChamber({ heroes, onClose, onComplete }) {
  useBgmScene('synthesis')  // ominous sacrifice bed while the rite is open
  const [vesselId, setVesselId] = useState(null)
  const [offerIds, setOfferIds] = useState([])
  const [picker, setPicker] = useState(null) // 'vessel' | 'offering' | null
  const [synthesizing, setSynthesizing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const alive = heroes.filter(h => h.is_alive)
  const vessel = alive.find(h => h.id === vesselId) || null
  const offerings = offerIds.map(id => alive.find(h => h.id === id)).filter(Boolean)

  const isResonant = s => vessel && s.hero_class === vessel.hero_class && vessel.hero_class !== 'Classless'
  const resonantCount = offerings.filter(isResonant).length
  const totalXp = vessel ? offerings.reduce((sum, s) => sum + previewXp(s, isResonant(s)), 0) : 0
  const count = offerings.length

  // Project the vessel's level after the rite (level cost mirrors level*100).
  let projLevel = vessel?.level || 1
  let projXp = (vessel?.xp || 0) + totalXp
  while (projXp >= projLevel * 100 && projLevel < 120) { projXp -= projLevel * 100; projLevel++ }
  const xpPct = Math.min(100, (projXp / Math.max(1, projLevel * 100)) * 100)

  const trauma = count === 0 ? 'NONE' : count <= 1 ? 'LOW' : count <= 3 ? 'MODERATE' : count <= 5 ? 'HIGH' : 'SEVERE'
  const traumaColor = count <= 1 ? '#8fbf9f' : count <= 3 ? '#d8bb84' : '#e06060'
  const canBegin = !!vessel && count > 0 && !synthesizing

  function addOffering(hero) {
    setError(null); setResult(null)
    // Favorites are protected — they can be the vessel, never the offering.
    if (hero.is_favorite) {
      setError(`${hero.name} is a Favorite — protected from being sacrificed. Unfavorite them first if you truly mean it.`)
      return
    }
    if (hero.id === vesselId) setVesselId(null)
    setOfferIds(ids => ids.includes(hero.id) ? ids : [...ids, hero.id])
  }

  function setVessel(hero) {
    setError(null); setResult(null)
    setOfferIds(ids => ids.filter(id => id !== hero.id))
    setVesselId(hero.id)
    setPicker(null)
  }

  async function beginRite() {
    if (!canBegin) return
    setSynthesizing(true)
    setError(null)
    playRiteHum()
    try {
      // Hold the rite for at least the animation's length — the consume/
      // empower keyframes are the whole ceremony; an instant response
      // made it feel dead.
      const [res] = await Promise.all([
        synthesizeHero(vessel.id, offerings.map(s => s.id)),
        new Promise(r => setTimeout(r, 2300)),
      ])
      setResult(res)
      setOfferIds([])
      if (onComplete) onComplete()
    } catch (e) {
      setError(e.message)
    } finally {
      setSynthesizing(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 900, background: '#070409', overflowY: 'auto', fontFamily: "'Cormorant Garamond',serif", color: '#efe8da' }}>
      <style>{`
        @keyframes rite-pulse2 { 0%,100% { opacity:.5 } 50% { opacity:1 } }
        @keyframes rite-spin2 { to { transform:translate(-50%,-50%) rotate(360deg) } }
        @keyframes synth-ember { 0% { transform:translateY(0); opacity:0 } 15% { opacity:.8 } 100% { transform:translateY(-150px); opacity:0 } }
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
          50% { filter: brightness(1.35) saturate(1.2) drop-shadow(0 0 18px rgba(224,96,128,0.9)); }
        }
        @keyframes synth-result-in { from { opacity: 0; transform: scale(0.85); } to { opacity: 1; transform: scale(1); } }
        .synth-rail::-webkit-scrollbar { height:0; width:0; }
        .synth-rail { scrollbar-width:none; -ms-overflow-style:none; }
      `}</style>

      {/* ambient: crimson-violet ritual gloom */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', background: 'radial-gradient(60% 70% at 50% 44%, rgba(120,30,60,.3), rgba(0,0,0,0) 62%), radial-gradient(80% 70% at 50% 100%, rgba(60,28,110,.28), rgba(0,0,0,0) 65%)' }} />
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', background: 'repeating-linear-gradient(115deg, rgba(184,151,98,.05) 0 1px, transparent 1px 120px), repeating-linear-gradient(-65deg, rgba(150,110,230,.045) 0 1px, transparent 1px 120px)' }} />
      <div style={{ position: 'fixed', left: '82%', top: '40%', width: 271, height: 271, transform: 'rotate(45deg)', border: '1px solid rgba(150,110,230,.1)', pointerEvents: 'none' }} />
      <div style={{ position: 'fixed', left: '6%', top: '44%', width: 252, height: 252, transform: 'rotate(45deg)', border: '1px solid rgba(150,110,230,.08)', pointerEvents: 'none' }} />
      <span style={{ position: 'fixed', left: '44%', top: '40%', width: 3, height: 3, borderRadius: '50%', background: '#e06080', boxShadow: '0 0 8px #e06080', animation: 'synth-ember 6s linear infinite', pointerEvents: 'none' }} />
      <span style={{ position: 'fixed', left: '57%', top: '44%', width: 3, height: 3, borderRadius: '50%', background: '#c8a9f5', boxShadow: '0 0 8px #c8a9f5', animation: 'synth-ember 7s linear 2s infinite', pointerEvents: 'none' }} />

      <div style={{ position: 'relative', maxWidth: 1280, margin: '0 auto', padding: '34px 40px 90px', minHeight: '100%' }}>
        {/* header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, position: 'relative', zIndex: 6 }}>
          <button onClick={onClose} disabled={synthesizing} title="Back to the roster"
            style={{ width: 24, height: 24, border: '1px solid rgba(184,151,98,.5)', background: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'Cinzel',serif", fontSize: 12, color: '#c9bfa8', cursor: 'pointer' }}>‹</button>
          <span onClick={onClose} style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: 12, color: 'var(--muted)', cursor: 'pointer' }}>ALL HEROES</span>
        </div>
        <div style={{ textAlign: 'center', marginTop: -24 }}>
          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 32, letterSpacing: '.1em', color: 'var(--text-hi)', textShadow: '0 0 30px rgba(192,64,96,.5)' }}>SYNTHESIS CHAMBER</div>
          <div style={{ fontSize: 15, fontStyle: 'italic', color: '#b58a9d', marginTop: 2 }}>What is given cannot be returned.</div>
        </div>

        {/* three-column ritual floor */}
        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', justifyContent: 'space-between', marginTop: 26, position: 'relative', zIndex: 5, flexWrap: 'wrap' }}>
          {/* LEFT: resonance + inheritance */}
          <div style={{ width: 220, flex: 'none' }}>
            <div style={{ border: '1px solid rgba(192,64,96,.5)', background: 'linear-gradient(160deg,rgba(80,20,40,.3),rgba(10,6,14,.7))', padding: '13px 15px', clipPath: 'polygon(0 0,100% 0,100% 100%,10px 100%)' }}>
              <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 11, color: '#e06080', textShadow: '0 0 10px rgba(224,96,128,.5)' }}>EGO RESONANCE</div>
              <div style={{ fontSize: 14, fontStyle: 'italic', color: '#c8a8b5', marginTop: 6, lineHeight: 1.45 }}>
                {resonantCount} of your souls share the vessel's class — their essence burns twice as bright. <span style={{ color: '#e06080', fontWeight: 600 }}>×2 XP</span>
              </div>
            </div>
            <div style={{ marginTop: 12, border: '1px solid rgba(150,110,230,.4)', background: 'rgba(12,7,24,.6)', padding: '13px 15px', clipPath: 'polygon(0 0,100% 0,100% 100%,10px 100%)' }}>
              <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 11, color: '#c8a9f5' }}>INHERITANCE</div>
              <div style={{ fontSize: 14, fontStyle: 'italic', color: '#b5a8c8', marginTop: 6, lineHeight: 1.45 }}>
                <span style={{ color: '#c8a9f5', fontWeight: 600 }}>{Math.min(85, count * 14)}%</span> chance the vessel learns a skill from the offered.
              </div>
            </div>
          </div>

          {/* CENTER: the vessel */}
          <div style={{ width: 220, flex: 'none', textAlign: 'center', position: 'relative', margin: '0 auto' }}>
            {/* ritual rings */}
            <div style={{ position: 'absolute', left: '50%', top: 92, width: 340, height: 340, transform: 'translate(-50%,-50%)', border: '1px dashed rgba(192,64,96,.4)', borderRadius: '50%', animation: 'rite-spin2 50s linear infinite', pointerEvents: 'none' }} />
            <div style={{ position: 'absolute', left: '50%', top: 92, width: 284, height: 284, transform: 'translate(-50%,-50%)', border: '1px solid rgba(150,110,230,.22)', borderRadius: '50%', pointerEvents: 'none' }} />

            <div style={{ position: 'relative', width: 150, height: 184, margin: '0 auto' }}>
              <div style={{ position: 'absolute', inset: -7, border: '1px solid rgba(184,151,98,.4)' }} />
              <div onClick={() => !synthesizing && setPicker('vessel')} title={vessel ? 'Change the vessel' : 'Choose the vessel'}
                style={{ position: 'absolute', inset: 0, border: vessel ? '1px solid rgba(184,151,98,.65)' : '1px dashed rgba(184,151,98,.5)', boxShadow: vessel ? '0 0 34px rgba(192,64,96,.35)' : 'none', cursor: 'pointer', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0c0710' }}>
                {vessel ? (
                  vessel.portrait_path && !vessel.portrait_path.includes('default_') ? (
                    <img src={`/heroes/${vessel.id}/card-image?mini=true`} alt={vessel.name} draggable={false}
                      onError={(e) => { e.target.onerror = null; e.target.src = `/${vessel.portrait_path}` }}
                      style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center top', animation: synthesizing ? 'synth-empower 1s ease-in-out infinite' : 'none' }} />
                  ) : (
                    <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 40, color: '#d8bb84' }}>{vessel.name[0]}</span>
                  )
                ) : (
                  <span style={{ ...microStyle, letterSpacing: '.2em', color: '#b58a9d', padding: '0 14px', lineHeight: 1.8 }}>CHOOSE<br />THE VESSEL</span>
                )}
              </div>
            </div>
            <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 22, color: 'var(--text-hi)', marginTop: 10 }}>{vessel ? vessel.name.toUpperCase() : '—'}</div>
            <div style={{ fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.26em', color: '#d8bb84', marginTop: 3 }}>
              THE VESSEL{vessel ? ` · ${vessel.hero_class.toUpperCase()}` : ''}
            </div>
            {vessel && (
              <div style={{ marginTop: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                  <span style={{ ...microStyle, letterSpacing: '.18em', color: 'var(--muted)' }}>
                    LV {vessel.level} {totalXp > 0 && <>→ <span style={{ color: '#ffd88a' }}>{projLevel}</span></>}
                  </span>
                  <span style={{ ...microStyle, color: '#8fbf9f' }}>{totalXp > 0 ? `+${totalXp.toLocaleString()} XP` : 'NO OFFERINGS'}</span>
                </div>
                <div style={{ height: 5, background: 'rgba(0,0,0,.55)', border: '1px solid rgba(184,151,98,.35)' }}>
                  <div style={{ width: `${xpPct}%`, height: '100%', background: 'linear-gradient(90deg,#8b46d6,#e06080,#ffd88a)', animation: totalXp > 0 ? 'rite-pulse2 3s ease-in-out infinite' : 'none' }} />
                </div>
              </div>
            )}
            {result && (
              <div style={{ marginTop: 12, border: '1px solid rgba(74,154,106,.5)', background: 'rgba(20,40,28,.4)', padding: '10px 12px', animation: 'synth-result-in .35s ease-out', clipPath: 'polygon(0 0,100% 0,100% 100%,10px 100%)' }}>
                <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.18em', fontSize: 10, color: '#8fbf9f' }}>THE RITE IS COMPLETE</div>
                <div style={{ fontSize: 13, fontStyle: 'italic', color: '#a8bfae', marginTop: 4, lineHeight: 1.4 }}>{result.message || 'The offerings have been consumed.'}</div>
                {result.xp_gained != null && <div style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 19, color: '#ffd88a', marginTop: 4 }}>+{result.xp_gained.toLocaleString()} XP</div>}
              </div>
            )}
            {error && <div style={{ marginTop: 10, fontSize: 13, fontStyle: 'italic', color: '#e08585' }}>{error}</div>}
          </div>

          {/* RIGHT: the rite's cost */}
          <div style={{ width: 220, flex: 'none' }}>
            <div style={{ border: '1px solid rgba(192,64,64,.55)', background: 'linear-gradient(160deg,rgba(80,16,20,.35),rgba(10,6,14,.7))', padding: '13px 15px', clipPath: 'polygon(0 0,100% 0,100% 100%,0 100%,10px 50%)' }}>
              <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 11, color: '#e08585' }}>THE ROSTER WATCHES</div>
              <div style={{ fontSize: 14, fontStyle: 'italic', color: '#c8a8a8', marginTop: 6, lineHeight: 1.45 }}>
                Offer as many souls as you dare — but every living hero witnesses the rite, and the horror lingers.
              </div>
              <div style={{ marginTop: 9, display: 'flex', flexDirection: 'column', gap: 5 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', ...microStyle }}>
                  <span style={{ color: 'var(--muted)' }}>MORALE · ALL HEROES</span><span style={{ color: '#e08585' }}>{count === 0 ? '—' : `−${count * 6}`}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', ...microStyle }}>
                  <span style={{ color: 'var(--muted)' }}>STRESS · ALL HEROES</span><span style={{ color: '#e08585' }}>{count === 0 ? '—' : `+${count * 9}`}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', ...microStyle }}>
                  <span style={{ color: 'var(--muted)' }}>TRAUMA RISK</span><span style={{ color: traumaColor }}>{trauma}</span>
                </div>
                <div style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.12em', color: '#8a5a6c' }}>THE MORE OFFERED, THE DEEPER THE SCARS</div>
              </div>
            </div>
          </div>
        </div>

        {/* offering rail */}
        <div style={{ maxWidth: 712, margin: '30px auto 0', position: 'relative', zIndex: 6 }}>
          <div style={{ border: '1px solid rgba(192,64,96,.4)', background: 'linear-gradient(180deg,rgba(40,12,24,.5),rgba(10,6,14,.7))', padding: '12px 14px', clipPath: 'polygon(0 0,100% 0,100% 100%,12px 100%)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 10 }}>
              <span style={{ width: 6, height: 6, transform: 'rotate(45deg)', background: '#e06080', display: 'inline-block' }} />
              <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: 10, color: '#e0a8b8' }}>OFFERINGS</span>
              <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.16em', fontSize: 9, color: '#8a5a6c' }}>{count} SOULS · NO LIMIT</span>
              <span style={{ flex: 1 }} />
              <button onClick={() => setOfferIds([])} disabled={count === 0 || synthesizing}
                style={{ cursor: count > 0 ? 'pointer' : 'default', background: 'none', fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.16em', color: count > 0 ? '#b58a9d' : '#5a4450', border: '1px solid rgba(150,110,230,.3)', padding: '4px 10px' }}>
                RELEASE ALL
              </button>
            </div>
            <div className="synth-rail" style={{ display: 'flex', alignItems: 'stretch', gap: 10, overflowX: 'auto', paddingBottom: 2 }}>
              {offerings.map(o => {
                const accent = familyColor(o.hero_class)
                const res = isResonant(o)
                const xp = previewXp(o, res)
                return (
                  <div key={o.id} onClick={() => !synthesizing && setOfferIds(ids => ids.filter(x => x !== o.id))} title="Release this soul"
                    style={{ cursor: 'pointer', flex: '0 0 auto', width: 86, padding: '8px 6px', border: '1px solid rgba(192,64,96,.3)', background: 'rgba(12,7,20,.5)', animation: synthesizing ? 'synth-consume 2.2s ease-in forwards' : 'none' }}>
                    <div style={{ position: 'relative', width: 52, height: 52, margin: '0 auto' }}>
                      <SoulDiamond hero={o} accent={accent} />
                      {res && <span title="Resonant · ×2 XP" style={{ position: 'absolute', right: -4, top: -4, width: 12, height: 12, transform: 'rotate(45deg)', background: '#e06080', boxShadow: '0 0 8px #e06080' }} />}
                    </div>
                    <div style={{ fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.06em', color: 'var(--text-hi)', marginTop: 6, textAlign: 'center', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{o.name.toUpperCase()}</div>
                    <div style={{ fontFamily: "'Cinzel',serif", fontSize: 7, letterSpacing: '.12em', color: '#b58a9d', marginTop: 1, textAlign: 'center' }}>{o.hero_class.toUpperCase()} · LV {o.level}</div>
                    <div style={{ fontFamily: "'Cinzel',serif", fontSize: 7, letterSpacing: '.1em', marginTop: 3, textAlign: 'center', color: res ? '#e06080' : 'var(--muted)' }}>+{xp.toLocaleString()} XP{res ? ' ×2' : ''}</div>
                  </div>
                )
              })}
              <div onClick={() => !synthesizing && setPicker('offering')}
                style={{ cursor: 'pointer', flex: '0 0 auto', width: 86, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '8px 6px', border: '1px dashed rgba(192,64,96,.55)', background: 'rgba(30,10,18,.35)' }}>
                <span style={{ fontSize: 22, color: '#e06080', lineHeight: 1 }}>＋</span>
                <span style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.14em', color: '#b58a9d', marginTop: 6 }}>ADD SOUL</span>
                <span style={{ fontFamily: "'Cinzel',serif", fontSize: 7, letterSpacing: '.1em', color: '#6f4a58', marginTop: 2 }}>FROM ROSTER</span>
              </div>
            </div>
          </div>
        </div>

        {/* actions */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 14, marginTop: 26, position: 'relative', zIndex: 6 }}>
          <button onClick={beginRite} disabled={!canBegin}
            style={{
              fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.26em', fontSize: 13,
              color: canBegin ? 'var(--text-hi)' : '#8a5a6c',
              background: canBegin ? 'linear-gradient(120deg,#7a2038,#4a1024)' : 'rgba(30,12,18,.5)',
              border: `1px solid ${canBegin ? 'rgba(224,96,128,.6)' : 'rgba(150,110,230,.25)'}`,
              padding: '12px 32px', clipPath: 'polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)',
              boxShadow: canBegin ? '0 0 26px rgba(192,64,96,.4)' : 'none',
              animation: canBegin ? 'rite-pulse2 4s ease-in-out infinite' : 'none',
              cursor: canBegin ? 'pointer' : 'default',
            }}>
            {synthesizing ? 'THE CHAMBER HUMS…' : canBegin ? 'BEGIN THE RITE' : vessel ? 'OFFER A SOUL' : 'CHOOSE A VESSEL'}
          </button>
          <button onClick={() => { setOfferIds([]); setVesselId(null); setResult(null); setError(null) }} disabled={synthesizing}
            style={{ fontFamily: "'Cinzel',serif", fontWeight: 600, letterSpacing: '.26em', fontSize: 12, color: 'var(--muted)', background: 'none', border: '1px solid rgba(150,110,230,.35)', padding: '12px 22px', clipPath: 'polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)', cursor: 'pointer' }}>
            RELEASE THEM
          </button>
        </div>

        {/* soul picker */}
        {picker && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 950, background: 'rgba(4,3,8,.75)', display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setPicker(null)}>
            <div onClick={e => e.stopPropagation()}
              style={{ width: 640, maxWidth: '94vw', maxHeight: '76vh', overflowY: 'auto', border: '1px solid rgba(192,64,96,.5)', background: 'linear-gradient(160deg,#1c0d18,#0b0710)', boxShadow: '0 30px 90px rgba(0,0,0,.78)', clipPath: 'polygon(0 0,100% 0,100% 100%,16px 100%)', padding: '18px 22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: '#e06080', display: 'inline-block' }} />
                <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: 10, color: '#e0a8b8' }}>
                  {picker === 'vessel' ? 'CHOOSE THE VESSEL' : 'OFFER SOULS'}
                </span>
                <span style={{ flex: 1 }} />
                <button onClick={() => setPicker(null)} style={{ width: 24, height: 24, border: '1px solid rgba(184,151,98,.5)', background: 'none', color: '#c9bfa8', cursor: 'pointer', fontFamily: "'Cinzel',serif" }}>✕</button>
              </div>
              {picker === 'offering' && (
                <div style={{ fontSize: 13, fontStyle: 'italic', color: '#b58a9d', marginBottom: 10 }}>Click to add — favorites (♥) are protected from the rite.</div>
              )}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 8 }}>
                {alive
                  .filter(h => h.id !== vesselId && !offerIds.includes(h.id))
                  .map(h => {
                    const accent = familyColor(h.hero_class)
                    const protectedFav = picker === 'offering' && !!h.is_favorite
                    return (
                      <div key={h.id}
                        onClick={() => { if (protectedFav) return; picker === 'vessel' ? setVessel(h) : addOffering(h) }}
                        style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 10px', border: '1px solid rgba(184,151,98,.25)', background: 'rgba(12,7,24,.45)', cursor: protectedFav ? 'not-allowed' : 'pointer', opacity: protectedFav ? .5 : 1 }}>
                        <div style={{ position: 'relative', width: 38, height: 38, flex: 'none' }}>
                          <SoulDiamond hero={h} accent={accent} />
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 11, letterSpacing: '.06em', color: 'var(--text-hi)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {!!h.is_favorite && <span style={{ color: '#e06080' }}>♥ </span>}{h.name.toUpperCase()}
                          </div>
                          <div style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.14em', color: 'var(--muted)', marginTop: 2 }}>
                            {h.hero_class.toUpperCase()} · LV {h.level} · {(h.current_star || h.birth_star)}★
                          </div>
                        </div>
                        {picker === 'offering' && !protectedFav && (
                          <span style={{ fontFamily: "'Cinzel',serif", fontSize: 9, color: '#8fbf9f' }}>+{previewXp(h, vessel ? h.hero_class === vessel.hero_class && vessel.hero_class !== 'Classless' : false).toLocaleString()} XP</span>
                        )}
                      </div>
                    )
                  })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
