/*
 * GUILD sub-screens: Perks (LIVE — /guild/perks) · Registry · War · Apply.
 * All share GuildFrame (RANK banner + stacked title + back). Registry/War/
 * Apply remain static shells until their systems land server-side.
 */
import React, { useState, useEffect } from 'react'
import { guildPerks, guildPerkBuy, guildWar } from '../api/arenaServerClient'
import { emitToast } from '../toastBus'

export function GuildFrame({ ghost, solid, right, onBack, children }) {
  return (
    <div className="ilm-guild">
      <div className="ilm-guild-head">
        <div className="ilm-guild-banner" />
        <div>
          <div className="ilm-guild-kicker">IRONVEIL LODGE · RANK 7</div>
          <div className="ilm-guild-title">
            <span className="ghost">{ghost}</span>
            <span className="solid">{solid}</span>
          </div>
        </div>
        <div className="ilm-guild-stats">
          {right}
          <button className="ilm-btn ilm-btn-ghost" onClick={onBack}>‹ HALL</button>
        </div>
      </div>
      {children}
    </div>
  )
}

/* ─────────────────────────── PERKS (live) ─────────────────────────── */
const PERK_LOOK = {
  muster:    { glyph: '⚑', accent: 'var(--gold-hi)' },
  coffers:   { glyph: '◆', accent: 'var(--gold-max)' },
  warband:   { glyph: '⚔', accent: 'var(--red-hi)' },
  quarter:   { glyph: '⚖', accent: 'var(--lavender)' },
  mentor:    { glyph: '✦', accent: 'var(--green-hi)' },
  skywright: { glyph: '➤', accent: 'var(--cyan, #7ecfd8)' },
}

export function GuildPerks({ onBack }) {
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(null)
  const [err, setErr] = useState(null)

  function load() {
    guildPerks().then(setData).catch(e => setErr(e.message))
  }
  useEffect(() => { load() }, [])

  async function buy(p) {
    setBusy(p.id)
    try {
      const res = await guildPerkBuy(p.id)
      emitToast(res.message, 'success')
      load()
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  return (
    <GuildFrame ghost="BOONS" solid="PERKS" onBack={onBack}
      right={<div className="ilm-guild-stat gold"><span className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>GUILD TREASURY</span><b style={{ color: 'var(--gold-max)' }}>◈ {(data?.treasury ?? 0).toLocaleString()}</b></div>}>
      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginBottom: '1.1rem' }}>
        Officers spend the lodge treasury on boons that lift every kin. Renown unlocks deeper boons.
        {data && !data.can_spend && <span style={{ color: 'var(--gold-hi)' }}> You may look, but only officers spend.</span>}
      </div>
      {err && <div style={{ fontStyle: 'italic', color: '#e08585', marginBottom: 12 }}>{err}</div>}
      <div className="ilm-guild-perkgrid">
        {(data?.perks || []).map(p => {
          const look = PERK_LOOK[p.id] || { glyph: '✦', accent: 'var(--gold-hi)' }
          const maxed = p.level >= p.max
          const canBuy = data?.can_spend && !p.locked && !maxed
          return (
            <div key={p.id} className={`ilm-guild-perk ${p.locked ? 'locked' : ''}`}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="ilm-guild-perk-badge" style={{ borderColor: look.accent, color: look.accent }}><span>{look.glyph}</span></span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.82rem', letterSpacing: '.08em', color: 'var(--text-hi)' }}>{p.name}</div>
                  <div className="ilm-micro" style={{ marginTop: 1 }}>{p.locked ? `LOCKED · RENOWN ${p.renown_req}` : `TIER ${p.level} / ${p.max}`}</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 4, marginTop: 12, flexWrap: 'wrap' }}>
                {Array.from({ length: p.max }).map((_, i) => (
                  <span key={i} style={{ width: 11, height: 11, transform: 'rotate(45deg)', background: i < p.level ? look.accent : 'transparent', border: `1px solid ${i < p.level ? look.accent : 'rgba(184,151,98,.3)'}` }} />
                ))}
              </div>
              <div style={{ fontStyle: 'italic', color: '#c9bfa8', marginTop: 10, lineHeight: 1.35, fontSize: '0.86rem' }}>{p.desc}</div>
              <span style={{ flex: 1 }} />
              <button className={`ilm-btn ${canBuy ? 'ilm-btn-gold' : 'ilm-btn-ghost'}`} disabled={!canBuy || busy === p.id}
                onClick={() => buy(p)} style={{ marginTop: 12, padding: '0.5rem 0' }}>
                {p.locked ? `RENOWN ${p.renown_req}` : maxed ? 'FINAL TIER' : busy === p.id ? 'RAISING…' : `UPGRADE · ◈ ${p.cost}`}
              </button>
            </div>
          )
        })}
      </div>
    </GuildFrame>
  )
}

/* ─────────────────────────── REGISTRY ─────────────────────────── */
const GUILDS = [
  { name: 'THE SUNDERED CHOIR', rank: 9, kin: '28/30', tag: 'Elite · Invite-only', motto: 'We sing the Tower down.', hot: true },
  { name: 'DAWN COVENANT', rank: 7, kin: '22/30', tag: 'Open · Casual', motto: 'Every dawn, one floor higher.' },
  { name: "KAEL'S VANGUARD", rank: 6, kin: '19/30', tag: 'Apply · Active', motto: 'Forward, always.' },
  { name: 'HOLLOW CHOIR', rank: 5, kin: '14/30', tag: 'Open · Growing', motto: 'From the hollow, we rise.' },
]

export function GuildRegistry({ onBack, onApply }) {
  return (
    <GuildFrame ghost="GUILDS" solid="REGISTRY" onBack={onBack}
      right={<div className="ilm-guild-stat"><span className="ilm-micro">SEASON</span><b>III</b></div>}>
      <div style={{ display: 'flex', gap: 8, marginBottom: '1.2rem', maxWidth: 520 }}>
        <input className="ilm-social-search" placeholder="FIND YOUR KIN BY NAME…" />
        <button className="ilm-btn ilm-btn-violet">SEARCH</button>
        <button className="ilm-btn ilm-btn-gold">FOUND A LODGE</button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {GUILDS.map(g => (
          <div key={g.name} className="ilm-guild-regrow">
            <div className="ilm-guild-banner" style={{ width: 40, height: 54 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.95rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{g.name}</span>
                <span className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>RANK {g.rank}</span>
                {g.hot && <span className="ilm-chip red" style={{ padding: '1px 8px' }}>RECRUITING</span>}
              </div>
              <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.86rem', marginTop: 2 }}>“{g.motto}” · <span style={{ fontStyle: 'normal', fontFamily: "'Cinzel',serif", fontSize: '0.6rem', letterSpacing: '.12em', color: 'var(--lavender)' }}>{g.tag}</span></div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="ilm-micro">KIN</div>
              <div style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, color: 'var(--text-hi)' }}>{g.kin}</div>
            </div>
            <button className="ilm-btn ilm-btn-violet" onClick={() => onApply && onApply(g)}>VIEW ›</button>
          </div>
        ))}
      </div>
    </GuildFrame>
  )
}

/* ─────────────────────────── WAR (live) ─────────────────────────── */
function fmtEnds(sec) {
  if (sec == null) return ''
  const d = Math.floor(sec / 86400), h = Math.floor((sec % 86400) / 3600), m = Math.floor((sec % 3600) / 60)
  return d > 0 ? `${d}D ${h}H` : `${h}H ${String(m).padStart(2, '0')}M`
}

export function GuildWar({ onBack }) {
  const [war, setWar] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    guildWar().then(setWar).catch(e => setErr(e.message))
    const iv = setInterval(() => guildWar().then(setWar).catch(() => {}), 15000)
    return () => clearInterval(iv)
  }, [])

  const leading = war?.in_war && war.my_score >= war.their_score
  const lead = war?.in_war ? Math.abs(war.my_score - war.their_score) : 0

  return (
    <GuildFrame ghost="SIEGE" solid="LODGE WAR" onBack={onBack}
      right={<div className="ilm-guild-war" style={{ cursor: 'default' }}><span className="ilm-livedot" /><span className="ilm-micro" style={{ color: 'var(--red-hi)' }}>ENDS {fmtEnds(war?.ends_in_seconds)}</span></div>}>
      {err && <div style={{ fontStyle: 'italic', color: '#e08585', marginBottom: 12 }}>{err}</div>}
      {war && !war.in_war && (
        <div style={{ padding: '3rem 0', textAlign: 'center' }}>
          <span style={{ width: 26, height: 26, transform: 'rotate(45deg)', border: '1px dashed rgba(192,64,64,.5)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ transform: 'rotate(-45deg)', color: '#e08585', fontFamily: "'Cinzel',serif", fontSize: 11 }}>⚑</span>
          </span>
          <div style={{ fontStyle: 'italic', color: 'var(--muted)', marginTop: 14, fontSize: 15 }}>{war.message}</div>
          <div style={{ fontFamily: "'Cinzel',serif", fontSize: 10, letterSpacing: '.2em', color: 'var(--muted)', marginTop: 8 }}>NEW PAIRINGS AT WEEK'S TURN · {fmtEnds(war.ends_in_seconds)}</div>
        </div>
      )}
      {war?.in_war && (
        <>
          <div className="ilm-guild-warboard">
            <div className={`ilm-guild-warside ${leading ? 'win' : ''}`}>
              <div className="ilm-guild-banner" style={{ margin: '0 auto 10px' }} />
              <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.2rem', color: 'var(--text-hi)' }}>{war.guild.name.toUpperCase()}</div>
              <div style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: '2.6rem', color: leading ? 'var(--gold-max)' : 'var(--text-hi)' }}>{war.my_score.toLocaleString()}</div>
              <div className="ilm-micro" style={{ color: leading ? 'var(--green-hi)' : 'var(--muted)' }}>
                {war.my_score === war.their_score ? 'DEADLOCKED' : leading ? `LEADING · +${lead.toLocaleString()}` : 'TRAILING'}
              </div>
            </div>
            <div className="ilm-guild-warvs">VS</div>
            <div className={`ilm-guild-warside ${!leading && war.my_score !== war.their_score ? 'win' : ''}`}>
              <div className="ilm-guild-banner" style={{ margin: '0 auto 10px', filter: 'hue-rotate(160deg)' }} />
              <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.2rem', color: 'var(--text-hi)' }}>{war.rival.name.toUpperCase()}</div>
              <div style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: '2.6rem', color: !leading && war.my_score !== war.their_score ? 'var(--red-hi)' : 'var(--text-hi)' }}>{war.their_score.toLocaleString()}</div>
              <div className="ilm-micro" style={{ color: 'var(--muted)' }}>RENOWN {war.rival.renown}</div>
            </div>
          </div>

          <div className="ilm-guild-pledge" style={{ marginTop: 18 }}>
            <span className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>YOUR CONTRIBUTION</span>
            <div className="ilm-guild-pledge-bar">
              <div style={{ width: `${war.my_score > 0 ? Math.min(100, (war.my_contribution / war.my_score) * 100) : 0}%` }} />
            </div>
            <span className="ilm-micro" style={{ color: 'var(--green-hi)' }}>{war.my_contribution.toLocaleString()} WAR SCORE</span>
          </div>

          {/* vanguard */}
          {war.vanguard?.length > 0 && (
            <div style={{ marginTop: 16, maxWidth: 520 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--red)', display: 'inline-block' }} />
                <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: 10, color: '#e08585' }}>THE VANGUARD</span>
                <span style={{ height: 1, flex: 1, background: 'rgba(192,64,64,.25)' }} />
              </div>
              {war.vanguard.map((v, i) => (
                <div key={v.username} style={{ display: 'flex', alignItems: 'baseline', gap: 12, padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,.04)' }}>
                  <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, color: i === 0 ? '#ffd88a' : 'var(--muted)', width: 16 }}>{i + 1}</span>
                  <span style={{ flex: 1, fontFamily: "'Cinzel',serif", fontSize: 12, letterSpacing: '.06em', color: 'var(--text-hi)' }}>{v.username.toUpperCase()}</span>
                  <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 15, color: 'var(--gold-hi)' }}>{v.score.toLocaleString()}</span>
                </div>
              ))}
            </div>
          )}

          <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 14, lineHeight: 1.5, maxWidth: 640 }}>
            Every floor gained on the climb banks {war.scoring.per_floor} war score, every ranked bout won banks {war.scoring.per_bout}.
            The winning lodge takes {war.spoils.win_treasury} treasury and {war.spoils.win_coin} coin per kin at week's turn.
          </div>
        </>
      )}
    </GuildFrame>
  )
}

/* ─────────────────────────── APPLY (modal) ─────────────────────────── */
export function GuildApply({ guild, onClose }) {
  const g = guild || { name: 'THE SUNDERED CHOIR', rank: 9, kin: '28/30', motto: 'We sing the Tower down.', tag: 'Elite · Invite-only' }
  return (
    <div className="ilm-modal-scrim" style={{ zIndex: 320 }} onClick={onClose}>
      <div className="ilm-guild-applypanel" onClick={e => e.stopPropagation()}>
        <span className="ilm-corner" /><span className="ilm-corner ilm-corner-r" />
        <button className="ilm-close" style={{ position: 'absolute', top: 14, right: 14 }} onClick={onClose}>✕</button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="ilm-guild-banner" style={{ width: 60, height: 80 }} />
          <div>
            <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>RANK {g.rank} · {g.tag}</div>
            <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.5rem', color: 'var(--text-hi)', marginTop: 4 }}>{g.name}</div>
            <div style={{ fontStyle: 'italic', color: '#c8b8dd', marginTop: 4 }}>“{g.motto}”</div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, margin: '1.2rem 0' }}>
          <div className="ilm-guild-stat"><span className="ilm-micro">KIN</span><b>{g.kin}</b></div>
          <div className="ilm-guild-stat"><span className="ilm-micro">WEEKLY FLOORS</span><b>4,120</b></div>
          <div className="ilm-guild-stat"><span className="ilm-micro">WAR RECORD</span><b style={{ color: 'var(--green-hi)' }}>7–1</b></div>
        </div>
        <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: '0.58rem', color: 'var(--gold)', marginBottom: 8 }}>REQUIREMENTS</div>
        <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', lineHeight: 1.5, marginBottom: '1.2rem' }}>Deepest climb ≥ Floor 50 · a weekly pledge of 200 floors · officers review every petition.</div>
        <textarea className="ilm-guild-applynote" placeholder="A word to the officers (optional)…" rows={3} />
        <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
          <button className="ilm-btn ilm-btn-gold ilm-btn-block" onClick={onClose}>SUBMIT PETITION</button>
          <button className="ilm-btn ilm-btn-ghost" onClick={onClose}>NEVER MIND</button>
        </div>
      </div>
    </div>
  )
}
