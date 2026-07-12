/*
 * THE TAVERN — live (/base/tavern). Patrons are the most stressed living
 * heroes; hosts assigned to the facility drive the passive hearth relief.
 * Rounds are a daily-capped gold sink: one per patron, one for the house.
 */
import React, { useState, useEffect } from 'react'
import { getTavern, buyTavernRound, tavernDice } from '../api/client'
import { emitToast } from '../toastBus'
import MinigameShell, { AUTO_RESOLVE_MULT } from './minigames/MinigameShell'
import DiceKnuckle from './minigames/DiceKnuckle'

export default function Tavern({ onClose }) {
  const [tav, setTav] = useState(null)
  const [busy, setBusy] = useState(null)
  // Knuckle & Bone dice table
  const [wager, setWager] = useState(100)
  const [showDice, setShowDice] = useState(false)
  const [diceMsg, setDiceMsg] = useState(null)

  async function load() {
    try { setTav(await getTavern()) } catch { /* backend older than /tavern */ }
  }
  useEffect(() => { load() }, [])

  async function resolveDice(mult) {
    setShowDice(false)
    try {
      const res = await tavernDice(wager, mult)
      setDiceMsg({ text: `${res.message} (${res.delta >= 0 ? '+' : ''}${res.delta.toLocaleString()}g · ${res.throws_left} throw${res.throws_left === 1 ? '' : 's'} left tonight)` })
    } catch (e) {
      setDiceMsg({ text: e.message, err: true })
    }
  }

  async function round(heroId = null) {
    setBusy(heroId ?? 'house')
    try {
      const res = await buyTavernRound(heroId)
      emitToast(res.message, 'success')
      await load()
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  if (tav && !tav.built) {
    return (
      <div className="ilm-tavern">
        <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>
        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.6rem', color: 'var(--text-hi)' }}>THE TAVERN</div>
        <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 12 }}>No tavern stands in this base yet — raise one, and give the weary somewhere to put the Tower down for a night.</div>
      </div>
    )
  }

  const patrons = tav?.patrons || []

  return (
    <div className="ilm-tavern">
      <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>
      <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>FACILITY{tav ? ` · LV ${tav.level}` : ''}</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.6rem', color: 'var(--text-hi)', letterSpacing: '.04em', textShadow: '0 6px 40px rgba(232,163,76,.35)' }}>THE TAVERN</div>
      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 2 }}>Ale mends what bandages cannot.</div>

      <div style={{ display: 'flex', gap: 12, margin: '16px 0', flexWrap: 'wrap' }}>
        <div className="ilm-guild-stat" style={{ borderColor: 'rgba(232,163,76,.4)' }}>
          <span className="ilm-micro" style={{ color: 'var(--ember)' }}>HEARTH WARMTH</span>
          <b>{tav?.relief_per_hour ? `−${tav.relief_per_hour} stress / hr` : 'cold — assign a host'}</b>
        </div>
        {tav?.bard && (
          <div className="ilm-guild-stat" style={{ borderColor: 'rgba(150,110,230,.4)' }}>
            <span className="ilm-micro" style={{ color: 'var(--lavender)' }}>{tav.bard.name.toUpperCase()} · {tav.bard.hero_class.toUpperCase()}</span>
            <b>keeping the room warm</b>
          </div>
        )}
      </div>

      <div className="ilm-tavern-grid">
        {/* tables */}
        <div>
          <div className="ilm-guild-sec"><span className="ilm-guild-secdot" style={{ background: 'var(--ember)' }} /><span className="ilm-guild-seclabel" style={{ color: 'var(--ember)' }}>AT THE TABLES</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {patrons.map(p => (
              <div key={p.id} className="ilm-tavern-patron">
                <span className="ilm-guild-badge">{p.name[0]}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.8rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{p.name.toUpperCase()}</div>
                  <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.84rem' }}>
                    {p.doing} · stress {p.stress}
                    {p.round_bought && <span style={{ color: 'var(--green-hi)' }}> → falling</span>}
                  </div>
                </div>
                {p.round_bought
                  ? <span className="ilm-micro" style={{ color: 'var(--muted)' }}>SERVED</span>
                  : <button className="ilm-btn ilm-btn-gold" disabled={busy === p.id} onClick={() => round(p.id)}>BUY A ROUND · {tav?.hero_round_cost}g</button>}
              </div>
            ))}
            {patrons.length === 0 && (
              <div className="ilm-tavern-empty">
                <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: '0.62rem', color: 'var(--muted)' }}>EMPTY STOOLS</span>
                <span style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.82rem' }}>No one carries stress tonight — the Tower has been kind.</span>
              </div>
            )}
          </div>
        </div>

        {/* tonight */}
        <div className="ilm-tavern-tonight">
          <span className="ilm-corner" />
          <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>TONIGHT</div>
          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.3rem', color: 'var(--text-hi)', marginTop: 4 }}>ROUND FOR THE HOUSE</div>
          <div style={{ fontStyle: 'italic', color: '#c8b8dd', marginTop: 8, lineHeight: 1.5 }}>Gold buys forgetting, for a while. Every hero in the tavern sheds stress and gains a night's morale.</div>
          <div style={{ display: 'flex', gap: 9, marginTop: 14, fontSize: '0.82rem', fontStyle: 'italic', color: 'var(--text-dim)', lineHeight: 1.4 }}>
            <span style={{ color: 'var(--ember)', fontStyle: 'normal' }}>⚠</span>
            <span>Beware: a hero who drinks every night grows fond of the stool. One round each, per night.</span>
          </div>
          {tav?.house_round_bought
            ? <button className="ilm-btn ilm-btn-ghost ilm-btn-block" style={{ marginTop: 16 }} disabled>THE HOUSE HAS DRUNK · UNTIL DAWN</button>
            : <button className="ilm-btn ilm-btn-gold ilm-btn-block" style={{ marginTop: 16 }} disabled={busy === 'house'} onClick={() => round(null)}>POUR THE ROUND · {(tav?.house_round_cost ?? 2000).toLocaleString()} g</button>}

          {/* KNUCKLE & BONE — the dice table (5 throws a night, house limit) */}
          <div style={{ marginTop: 18, borderTop: '1px solid rgba(184,151,98,.25)', paddingTop: 12 }}>
            <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.05rem', color: 'var(--text-hi)' }}>KNUCKLE &amp; BONE</div>
            <div style={{ fontStyle: 'italic', color: '#c8b8dd', fontSize: '0.85rem', marginTop: 4 }}>Three bones against the house. The stake rides on your nerve.</div>
            <div style={{ display: 'flex', gap: 8, marginTop: 10, alignItems: 'center' }}>
              <span className="ilm-micro" style={{ color: 'var(--muted)' }}>STAKE</span>
              {[100, 500, 2000].map(w => (
                <button key={w} className={`ilm-fac-chip ${wager === w ? 'active' : ''}`} onClick={() => setWager(w)}>{w.toLocaleString()}g</button>
              ))}
              <span style={{ flex: 1 }} />
              <button className="ilm-btn ilm-btn-gold" onClick={() => setShowDice(true)}>SIT AT THE TABLE</button>
            </div>
            {diceMsg && <div style={{ fontSize: 12.5, fontStyle: 'italic', color: diceMsg.err ? '#d98a8a' : '#a8dfb8', marginTop: 8 }}>{diceMsg.text}</div>}
          </div>
        </div>
      </div>

      {showDice && (
        <MinigameShell
          title="KNUCKLE & BONE"
          flavor={`${wager.toLocaleString()}g rides on three bones. The tier sets how lucky the house gets to be.`}
          onSkip={() => resolveDice(AUTO_RESOLVE_MULT)}
          onResolve={(mult) => resolveDice(mult)}
          game={(difficulty, onDone) => <DiceKnuckle difficulty={difficulty} onDone={onDone} />}
        />
      )}
    </div>
  )
}
