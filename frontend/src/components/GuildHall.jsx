/*
 * GUILD HALL — live (Guilds v1, arena server /guild/*). Header stats,
 * ROSTER · GUILD SHOP · DAILY BOSS · GUILD CHAT tabs, daily check-in,
 * shared-HP daily boss (3 strikes/day), guild-coin shop whose grants are
 * delivered through the local mailbox. Guildless players see the registry
 * (browse/apply) and the founding form. Design: docs/guild-social-design.md.
 */
import React, { useState, useEffect } from 'react'
import {
  getArenaToken, getArenaUsername, guildMine, guildRegistry, guildFound, guildApply,
  guildDecide, guildLeave, guildCheckin, guildBossStrike, guildShop, guildShopBuy,
  chatFetch, chatSend,
} from '../api/arenaServerClient'
import { receiveMail, payLocalFee, setGuildBoons } from '../api/client'
import { emitToast } from '../toastBus'
import { useBgmScene } from '../useBgmScene'
import CombatArena from './CombatArena'
import StakesBanner from './StakesBanner'
import { GuildPerks, GuildWar } from './GuildViews'

const RANK_COLOR = { MASTER: 'var(--gold-hi)', OFFICER: 'var(--lavender)', MEMBER: 'var(--text-dim)' }
const FOUNDING_FEE = 50000

function fmtReset(sec) {
  if (sec == null) return ''
  return `${Math.floor(sec / 3600)}H ${String(Math.floor((sec % 3600) / 60)).padStart(2, '0')}M`
}

/* ── guildless: registry + founding ── */
function Registry({ onJoined }) {
  const [reg, setReg] = useState(null)
  const [founding, setFounding] = useState(false)
  const [name, setName] = useState('')
  const [motto, setMotto] = useState('')
  const [busy, setBusy] = useState(null)

  useEffect(() => { guildRegistry().then(setReg).catch(e => emitToast(e.message, 'error')) }, [])

  async function found() {
    setBusy('found')
    try {
      // fee first (local economy), charter second — if the charter fails the
      // fee is refunded by mail so the gold isn't silently lost
      await payLocalFee(FOUNDING_FEE, 'guild founding')
      try {
        const res = await guildFound(name, motto)
        emitToast(res.message, 'success')
        onJoined()
      } catch (e) {
        await receiveMail('The Guild Charter Office', 'Founding fee refunded', 'The charter was refused — your gold is returned.', { gold: FOUNDING_FEE }).catch(() => {})
        throw e
      }
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  async function apply(g) {
    setBusy(g.id)
    try {
      const res = await guildApply(g.id, '')
      emitToast(res.message, 'success')
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  return (
    <div className="ilm-guild-body" style={{ paddingTop: 12 }}>
      <div className="ilm-guild-sec">
        <span className="ilm-guild-secdot" /><span className="ilm-guild-seclabel">FIND YOUR KIN</span>
        <span style={{ flex: 1 }} />
        <span className="ilm-micro" style={{ color: 'var(--gold-hi)', cursor: 'pointer' }} onClick={() => setFounding(f => !f)}>
          {founding ? '‹ BACK TO THE REGISTRY' : `FOUND A GUILD · ${FOUNDING_FEE.toLocaleString()}g ›`}
        </span>
      </div>

      {founding ? (
        <div style={{ maxWidth: 460, display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
          <input className="ilm-input" placeholder="Name the guild…" value={name} onChange={e => setName(e.target.value)} maxLength={32}
            style={{ background: 'rgba(12,7,24,.7)', border: '1px solid var(--gold-dim)', color: 'var(--text-hi)', padding: '10px 14px', fontFamily: "'Cinzel',serif", letterSpacing: '.08em' }} />
          <input className="ilm-input" placeholder="A motto for the banner…" value={motto} onChange={e => setMotto(e.target.value)} maxLength={120}
            style={{ background: 'rgba(12,7,24,.7)', border: '1px solid var(--border)', color: 'var(--text-dim)', padding: '10px 14px', fontStyle: 'italic' }} />
          <button className="ilm-btn ilm-btn-gold" disabled={busy === 'found' || name.trim().length < 3} onClick={found}>
            {busy === 'found' ? 'SEALING THE CHARTER…' : `FOUND THE GUILD · ${FOUNDING_FEE.toLocaleString()} g`}
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
          {(reg?.guilds || []).map(g => (
            <div key={g.id} className="ilm-guild-member">
              <span className="ilm-guild-badge">{g.name[0]}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.78rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{g.name.toUpperCase()}</div>
                <div style={{ fontStyle: 'italic', fontSize: '0.8rem', color: 'var(--text-dim)' }}>{g.motto || 'No motto carved yet.'}</div>
              </div>
              <span className="ilm-micro" style={{ color: 'var(--muted)' }}>{g.members}/{g.member_cap} · RENOWN {g.renown}</span>
              <button className="ilm-btn ilm-btn-violet" style={{ padding: '0.35rem 1rem' }} disabled={busy === g.id} onClick={() => apply(g)}>PETITION</button>
            </div>
          ))}
          {reg && reg.guilds.length === 0 && (
            <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', padding: '2rem 0', textAlign: 'center' }}>
              No guild flies a banner yet — found the first.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── guild channel — live against /chat (channel 'guild') ── */
function GuildChat({ kinCount }) {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [err, setErr] = useState(null)
  const scrollRef = React.useRef(null)
  const me = getArenaUsername()

  useEffect(() => {
    let live = true
    async function poll() {
      try {
        const d = await chatFetch('guild')
        if (live) { setMessages(d.messages || []); setErr(null) }
      } catch (e) { if (live) setErr(e.message) }
    }
    poll()
    const iv = setInterval(poll, 5000)
    return () => { live = false; clearInterval(iv) }
  }, [])

  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }) }, [messages])

  async function send(e) {
    e.preventDefault()
    const text = draft.trim()
    if (!text) return
    try {
      await chatSend('guild', text)
      setDraft('')
      const d = await chatFetch('guild')
      setMessages(d.messages || [])
    } catch (e2) { setErr(e2.message) }
  }

  return (
    <div style={{ border: '1px solid rgba(184,151,98,.35)', background: 'rgba(12,7,24,.5)', display: 'flex', flexDirection: 'column', minHeight: 380, maxHeight: 520 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '12px 16px', borderBottom: '1px solid rgba(184,151,98,.2)' }}>
        <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
        <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: 10, color: 'var(--gold)' }}>GUILD CHANNEL</span>
        <span style={{ flex: 1 }} />
        <span style={{ fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: '.14em', color: 'var(--muted)' }}>{kinCount} KIN</span>
      </div>
      <div ref={scrollRef} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 11, padding: '14px 18px', overflowY: 'auto' }}>
        {messages.length === 0 && (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', fontStyle: 'italic', color: 'var(--muted)', fontSize: 15 }}>
            The lodge keeps its counsel — break the silence.
          </div>
        )}
        {messages.map(m => {
          const mine = m.sender === me
          const c = mine ? '#8fbf9f' : '#ffd88a'
          return (
            <div key={m.id} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <span style={{ width: 22, height: 22, transform: 'rotate(45deg)', border: `1px solid ${c}`, background: '#1c1030', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none', marginTop: 2 }}>
                <span style={{ transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontSize: 9, color: c }}>{mine ? '✦' : m.sender[0].toUpperCase()}</span>
              </span>
              <div style={{ minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 10, letterSpacing: '.08em', color: c }}>{mine ? 'YOU' : m.sender.toUpperCase()}</span>
                  <span style={{ fontFamily: "'Cinzel',serif", fontSize: 7, letterSpacing: '.14em', color: 'var(--muted)' }}>{new Date(m.at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div style={{ fontSize: 14, fontStyle: 'italic', color: '#d8cfe6', marginTop: 2, overflowWrap: 'anywhere' }}>{m.text}</div>
              </div>
            </div>
          )
        })}
      </div>
      <form onSubmit={send} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderTop: '1px solid rgba(184,151,98,.2)' }}>
        <input value={draft} onChange={e => setDraft(e.target.value)} maxLength={300} placeholder="Speak to the lodge…"
          style={{ flex: 1, border: '1px solid rgba(184,151,98,.35)', background: 'rgba(8,6,14,.6)', padding: '9px 14px', fontSize: 14, fontStyle: 'italic', fontFamily: "'Cormorant Garamond',serif", color: 'var(--text-hi)', outline: 'none' }} />
        <button type="submit" disabled={!draft.trim()}
          style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 10, cursor: draft.trim() ? 'pointer' : 'default', color: draft.trim() ? '#0a0710' : '#6f628c', background: draft.trim() ? 'linear-gradient(120deg,#d8bb84,#b89762)' : 'none', border: draft.trim() ? 'none' : '1px solid rgba(138,123,176,.35)', padding: '10px 22px', clipPath: 'polygon(8px 0,100% 0,calc(100% - 8px) 100%,0 100%)' }}>
          SEND
        </button>
      </form>
      {err && <div style={{ padding: '6px 16px 10px', fontSize: 12, fontStyle: 'italic', color: '#e08585' }}>{err}</div>}
    </div>
  )
}

export default function GuildHall({ onClose }) {
  useBgmScene('tavern')  // the guild hall shares the tavern's convivial bed
  const [tab, setTab] = useState('roster')
  const [view, setView] = useState(null)     // null | 'perks' | 'war' — hall sub-screens
  const [data, setData] = useState(null)     // /guild/mine response
  const [shopData, setShopData] = useState(null)
  const [busy, setBusy] = useState(null)
  const [err, setErr] = useState(null)
  const [strikeFight, setStrikeFight] = useState(null)  // strike result while its battle animates

  async function load() {
    try {
      const d = await guildMine()
      setData(d); setErr(null)
      // Relay the lodge's client-applied boons (Mentorship XP, Skywright
      // refit discount) to the local save — 0/0 when guildless.
      const b = d?.boons || {}
      setGuildBoons(b.hero_exp_pct || 0, b.refit_discount_pct || 0).catch(() => {})
    } catch (e) { setErr(e.message) }
  }
  useEffect(() => { if (getArenaToken()) load() }, [])
  useEffect(() => { if (tab === 'shop' && data?.in_guild) guildShop().then(setShopData).catch(() => {}) }, [tab, data?.in_guild])

  async function act(name, fn, after = load) {
    setBusy(name)
    try {
      const res = await fn()
      if (res?.message) emitToast(res.message, res.ok === false ? 'error' : 'success')
      await after(res)
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  async function buy(item) {
    setBusy(item.id)
    try {
      const res = await guildShopBuy(item.id)
      await receiveMail('The Guild Quartermaster', item.name, res.message || 'Bought with guild coin.', res.grant || {}).catch(() => {})
      emitToast(`${item.name} — delivered to your Mailbox.`, 'success')
      guildShop().then(setShopData).catch(() => {})
      load()
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  if (!getArenaToken()) {
    return (
      <div className="ilm-guild">
        <div className="ilm-guild-head">
          <div><div className="ilm-guild-kicker">WORLD SERVER</div>
            <div className="ilm-guild-title"><span className="ghost">HALL</span><span className="solid">GUILD</span></div></div>
          <div className="ilm-guild-stats"><button className="ilm-close" onClick={onClose}>✕</button></div>
        </div>
        <div className="ilm-guild-placeholder">
          <div style={{ fontStyle: 'italic', color: 'var(--text-dim)' }}>Guilds live on the World Server — log in from the Arena screen first.</div>
        </div>
      </div>
    )
  }

  const g = data?.guild
  const me = data?.me
  const boss = data?.boss

  // Hall sub-screens — treasury chip opens Perks, the war badge opens the Lodge War.
  if (view === 'perks') return <GuildPerks onBack={() => setView(null)} />
  if (view === 'war') return <GuildWar onBack={() => setView(null)} />

  return (
    <div className="ilm-guild">
      {/* header band */}
      <div className="ilm-guild-head">
        <div className="ilm-guild-banner" title="Guild banner" />
        <div>
          <div className="ilm-guild-kicker">{g ? `${g.name.toUpperCase()} · RENOWN ${g.renown}` : 'THE GUILDLESS ROAD'}</div>
          <div className="ilm-guild-title">
            <span className="ghost">HALL</span>
            <span className="solid">GUILD</span>
          </div>
        </div>
        <div className="ilm-guild-stats">
          {data?.in_guild && (
            <>
              <div className="ilm-guild-stat"><span className="ilm-micro">KIN</span><b>{data.members.length} <span className="text-dim" style={{ fontSize: '0.8rem' }}>/ {g.member_cap}</span></b></div>
              <button className="ilm-guild-stat gold" onClick={() => setView('perks')} title="Spend treasury on lodge boons">
                <span className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>TREASURY</span><b style={{ color: 'var(--gold-hi)' }}>◆ {g.treasury.toLocaleString()} ›</b>
              </button>
              <button className="ilm-guild-war" onClick={() => setView('war')} title="The Lodge War">
                <span className="ilm-livedot" />
                <span className="ilm-micro" style={{ color: 'var(--red-hi)' }}>LODGE WAR ›</span>
              </button>
              {me?.checked_in
                ? <div className="ilm-guild-stat"><span className="ilm-micro" style={{ color: 'var(--green-hi)' }}>LEDGER</span><b style={{ color: 'var(--green-hi)' }}>SIGNED</b></div>
                : <button className="ilm-guild-stat gold" disabled={busy === 'checkin'} onClick={() => act('checkin', guildCheckin)} title="Daily check-in — guild coin + pledge">
                    <span className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>CHECK IN</span><b style={{ color: 'var(--gold-hi)' }}>+{5} ◈ ›</b>
                  </button>}
            </>
          )}
          <button className="ilm-close" onClick={onClose}>✕</button>
        </div>
      </div>

      {err && <div className="ilm-micro" style={{ color: 'var(--red-hi)', padding: '10px 24px' }}>{err}</div>}

      {data && !data.in_guild && <Registry onJoined={load} />}

      {data?.in_guild && (
        <>
          {/* tabs */}
          <div className="ilm-guild-tabs">
            {[['roster', 'ROSTER'], ['shop', 'GUILD SHOP'], ['boss', 'DAILY BOSS'], ['chat', 'GUILD CHAT']].map(([id, label]) => (
              <button key={id} className={`ilm-guild-tab ${tab === id ? 'active' : ''}`} onClick={() => setTab(id)}>{label}</button>
            ))}
            <span style={{ flex: 1 }} />
            {boss && !boss.killed && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="ilm-livedot" />
                <span className="ilm-micro" style={{ color: 'var(--red-hi)' }}>HUNT ACTIVE · RESETS {fmtReset(boss.resets_in_seconds)}</span>
              </span>
            )}
          </div>

          <div className="ilm-guild-body">
            {tab === 'roster' && (
              <>
                <div className="ilm-guild-sec">
                  <span className="ilm-guild-secdot" /><span className="ilm-guild-seclabel">THE ROSTER</span>
                  <span style={{ flex: 1 }} />
                  <span className="ilm-micro" style={{ color: 'var(--muted)', cursor: 'pointer' }} onClick={() => act('leave', async () => { if (window.confirm('Walk out from under the banner?')) return guildLeave(); return {} })}>LEAVE THE GUILD</span>
                </div>
                {/* spec: two-column roster grid, rank-accented diamond badges */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '7px 12px', alignContent: 'start' }}>
                  {data.members.map(m => {
                    const gm = m.rank === 'MASTER' || m.rank === 'GUILDMASTER'
                    const officer = m.rank === 'OFFICER'
                    const accent = m.you ? '#8fbf9f' : gm ? '#ffd88a' : officer ? '#c8a9f5' : 'var(--muted)'
                    return (
                      <div key={m.username} style={{
                        display: 'flex', alignItems: 'center', gap: 11, padding: '7px 12px',
                        border: m.you ? '1px solid rgba(150,110,230,.45)' : gm ? '1px solid rgba(255,216,138,.4)' : '1px solid rgba(184,151,98,.22)',
                        background: m.you ? 'linear-gradient(90deg,rgba(124,58,214,.14),transparent)' : gm ? 'linear-gradient(90deg,rgba(184,151,98,.1),transparent)' : 'rgba(12,7,24,.35)',
                      }}>
                        <span style={{ width: 24, height: 24, transform: 'rotate(45deg)', flex: 'none', border: `1px solid ${accent}`, background: '#1c1030', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <span style={{ transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontSize: 9, color: accent }}>{m.you ? '✦' : m.username[0].toUpperCase()}</span>
                        </span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 11, letterSpacing: '.06em', color: 'var(--text-hi)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {m.username.toUpperCase()}{m.you && <span style={{ color: '#8fbf9f', fontSize: 9 }}> · YOU</span>}
                          </div>
                          <div style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.16em', color: RANK_COLOR[m.rank] || 'var(--muted)' }}>{m.rank}</div>
                        </div>
                        <span style={{ fontSize: 12, fontStyle: 'italic', color: 'var(--muted)', whiteSpace: 'nowrap' }}>floor {m.highest_floor} · elo {m.elo}</span>
                      </div>
                    )
                  })}
                </div>

                {/* petitions (officers) */}
                {data.applications?.length > 0 && (
                  <>
                    <div className="ilm-guild-sec" style={{ marginTop: 14 }}>
                      <span className="ilm-guild-secdot" style={{ background: 'var(--lavender)' }} /><span className="ilm-guild-seclabel" style={{ color: 'var(--lavender)' }}>PETITIONS FOR KINSHIP</span>
                    </div>
                    {data.applications.map(a => (
                      <div key={a.id} className="ilm-guild-member">
                        <span className="ilm-guild-badge">{a.username[0].toUpperCase()}</span>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.72rem', color: 'var(--text-hi)' }}>{a.username.toUpperCase()}</div>
                          <div style={{ fontStyle: 'italic', fontSize: '0.78rem', color: 'var(--text-dim)' }}>{a.message || 'No word sent — just the knock.'}</div>
                        </div>
                        <button className="ilm-btn ilm-btn-gold" style={{ padding: '0.3rem 0.9rem' }} disabled={busy === `a${a.id}`} onClick={() => act(`a${a.id}`, () => guildDecide(a.id, true))}>ACCEPT</button>
                        <button className="ilm-btn ilm-btn-ghost" style={{ padding: '0.3rem 0.9rem' }} disabled={busy === `a${a.id}`} onClick={() => act(`a${a.id}`, () => guildDecide(a.id, false))}>DECLINE</button>
                      </div>
                    ))}
                  </>
                )}

                <div className="ilm-guild-pledge">
                  <span className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>WEEKLY PLEDGE · {data.pledge.week}</span>
                  <div className="ilm-guild-pledge-bar"><div style={{ width: `${Math.min(100, (data.pledge.floors / Math.max(1, data.members.length * 20)) * 100)}%` }} /></div>
                  <span className="ilm-micro" style={{ color: 'var(--green-hi)' }}>{data.pledge.floors} FLOORS PLEDGED</span>
                  <span style={{ fontStyle: 'italic', fontSize: '0.78rem', color: 'var(--muted)' }}>Check in daily — your climb pledges floors.</span>
                </div>
              </>
            )}

            {tab === 'shop' && (
              <>
                <div className="ilm-guild-sec">
                  <span className="ilm-guild-secdot" style={{ background: 'var(--gold-hi)' }} /><span className="ilm-guild-seclabel" style={{ color: 'var(--gold-hi)' }}>GUILD SHOP</span>
                  <span style={{ flex: 1 }} />
                  <span className="ilm-guild-coin">◈ YOUR GUILD COIN <b style={{ color: 'var(--gold-max)' }}>{shopData?.guild_coin ?? me?.guild_coin ?? 0}</b></span>
                  <span className="ilm-micro" style={{ color: 'var(--muted)' }}>RESTOCKS MONDAY</span>
                </div>
                <div className="ilm-guild-shop">
                  {(shopData?.items || []).map(it => {
                    const soldOut = it.bought >= it.weekly
                    return (
                      <div key={it.id} className="ilm-guild-shopcard" style={{ opacity: soldOut ? 0.55 : 1 }}>
                        <span className="ilm-guild-shopicon" />
                        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.78rem', color: 'var(--text-hi)', letterSpacing: '.04em' }}>{it.name}</div>
                        <div style={{ fontStyle: 'italic', fontSize: '0.85rem', color: 'var(--text-dim)', marginTop: 3, lineHeight: 1.3, flex: 1 }}>{it.desc}</div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 8 }}>
                          <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, color: 'var(--gold-hi)' }}>◈ {it.cost}</span>
                          <span className="ilm-micro" style={{ color: 'var(--muted)' }}>{it.bought}/{it.weekly} THIS WEEK</span>
                        </div>
                        <button className="ilm-btn ilm-btn-gold ilm-btn-block" style={{ marginTop: 8 }} disabled={soldOut || busy === it.id} onClick={() => buy(it)}>
                          {soldOut ? 'SOLD OUT · MONDAY' : busy === it.id ? 'BUYING…' : 'PURCHASE'}
                        </button>
                      </div>
                    )
                  })}
                </div>
              </>
            )}

            {tab === 'boss' && boss && (() => {
              const hpPct = Math.max(0, Math.min(100, (boss.hp / boss.max_hp) * 100))
              const maxDmg = Math.max(1, ...(boss.tribute || []).map(t => t.damage))
              return (
              /* spec: two columns — the beast's red panel, then tribute + spoils */
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 14, alignItems: 'stretch' }}>
                <div style={{ position: 'relative', border: '1px solid rgba(192,64,64,.45)', background: 'linear-gradient(160deg,rgba(80,22,22,.3),rgba(12,7,24,.65))', padding: '20px 24px', clipPath: 'polygon(0 0,100% 0,100% 100%,16px 100%)', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', inset: 0, background: 'repeating-linear-gradient(135deg,rgba(192,64,64,.06) 0 10px,rgba(12,7,24,.15) 10px 20px)', pointerEvents: 'none' }} />
                  <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                      <span className="ilm-livedot" />
                      <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: 10, color: '#e08585' }}>DAILY GUILD BOSS</span>
                    </div>
                    <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 40, lineHeight: 1, color: 'var(--text-hi)', marginTop: 14, textShadow: '0 4px 30px rgba(192,64,64,.5)' }}>
                      {boss.name.toUpperCase()}
                    </div>
                    <div style={{ fontSize: 15, fontStyle: 'italic', color: '#c9a3a3', marginTop: 9, lineHeight: 1.35 }}>
                      Rises from the ashfields each dawn. Every kin may strike {boss.strikes_per_day} times a day — the lodge shares the spoils.
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 18 }}>
                      <div style={{ flex: 1, height: 12, background: 'rgba(0,0,0,.5)', border: '1px solid rgba(192,64,64,.45)' }}>
                        <div style={{ width: `${hpPct}%`, height: '100%', background: 'linear-gradient(90deg,#7a3030,#c04040)' }} />
                      </div>
                      <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 20, color: '#e08585' }}>{hpPct.toFixed(0)}%</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: '.14em', color: 'var(--muted)', marginTop: 6 }}>
                      <span>HP {(boss.hp / 1e6).toFixed(1)}M / {(boss.max_hp / 1e6).toFixed(1)}M</span>
                      <span>{(boss.tribute || []).length} KIN ENGAGED · YOUR STRIKES {boss.my_strikes} / {boss.strikes_per_day}</span>
                    </div>
                    <StakesBanner variant="echo" compact note="the Leviathan claims no souls" style={{ marginTop: 12 }} />
                    <span style={{ flex: 1 }} />
                    {boss.killed ? (
                      <div style={{ textAlign: 'center', fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: 12, color: 'var(--gold-hi)', border: '1px solid rgba(216,187,132,.4)', padding: '13px 0', marginTop: 14 }}>
                        THE BEAST IS DOWN — SPOILS PAID. IT RISES AT DAWN.
                      </div>
                    ) : (
                      <button
                        disabled={busy === 'strike' || boss.my_strikes >= boss.strikes_per_day}
                        onClick={async () => {
                          setBusy('strike')
                          try {
                            const res = await guildBossStrike()
                            if (res.combat?.initial_state) setStrikeFight(res)
                            else { emitToast(res.message, 'success'); load() }
                          } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
                        }}
                        style={{ width: '100%', marginTop: 14, textAlign: 'center', cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.22em', fontSize: 14, color: '#0a0710', background: 'linear-gradient(120deg,#e8a06a,#c04040)', border: 'none', padding: '13px 0', clipPath: 'polygon(12px 0,100% 0,calc(100% - 12px) 100%,0 100%)', boxShadow: '0 8px 26px rgba(192,64,64,.45)', opacity: boss.my_strikes >= boss.strikes_per_day ? 0.5 : 1 }}>
                        {busy === 'strike' ? 'THE HUNT BEGINS…' : boss.my_strikes >= boss.strikes_per_day ? 'STRIKES SPENT · DAWN' : 'JOIN THE HUNT'}
                      </button>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minHeight: 0 }}>
                  <div style={{ flex: 1, border: '1px solid rgba(184,151,98,.35)', background: 'rgba(12,7,24,.5)', padding: '14px 16px', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                      <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold-hi)', display: 'inline-block' }} />
                      <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: 10, color: 'var(--gold-hi)' }}>TODAY'S TRIBUTE</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginTop: 12, overflowY: 'auto' }}>
                      {(boss.tribute || []).length === 0 && (
                        <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 13 }}>No kin has struck yet today — draw first blood.</div>
                      )}
                      {(boss.tribute || []).slice(0, 8).map((t, i) => {
                        const isYou = t.you || t.username === me?.username
                        const share = boss.max_hp ? (t.damage / boss.max_hp) * 100 : 0
                        const accent = isYou ? '#8fbf9f' : i === 0 ? '#ffd88a' : i === 1 ? '#c8a9f5' : 'var(--gold)'
                        return (
                          <div key={t.username} style={{ display: 'flex', alignItems: 'center', gap: 10, ...(isYou ? { border: '1px solid rgba(150,110,230,.4)', background: 'linear-gradient(90deg,rgba(124,58,214,.14),transparent)', padding: '4px 6px', margin: '0 -6px' } : {}) }}>
                            <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, color: i === 0 ? '#ffd88a' : isYou ? '#c8a9f5' : '#c9bfa8', width: 16 }}>{i + 1}</span>
                            <span style={{ width: 22, height: 22, transform: 'rotate(45deg)', border: `1px solid ${accent}`, background: '#1c1030', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none' }}>
                              <span style={{ transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontSize: 9, color: accent }}>{isYou ? '✦' : t.username[0].toUpperCase()}</span>
                            </span>
                            <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.06em', color: 'var(--text-hi)', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{isYou ? 'YOU' : t.username.toUpperCase()}</span>
                            <div style={{ width: 90, height: 6, background: 'rgba(0,0,0,.4)', border: '1px solid rgba(184,151,98,.3)', flex: 'none' }}>
                              <div style={{ width: `${Math.max(4, (t.damage / maxDmg) * 100)}%`, height: '100%', background: `linear-gradient(90deg,#8b46d6,${accent})` }} />
                            </div>
                            <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 12, color: accent, width: 44, textAlign: 'right' }}>{share >= 0.1 ? `${share.toFixed(1)}%` : t.damage.toLocaleString()}</span>
                          </div>
                        )
                      })}
                    </div>
                    <span style={{ flex: 1 }} />
                    {(boss.tribute || []).length > 8 && (
                      <div style={{ textAlign: 'center', fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: '.2em', color: 'var(--muted)', marginTop: 8 }}>
                        FULL LEADERBOARD · {(boss.tribute || []).length} KIN ›
                      </div>
                    )}
                  </div>
                  <div style={{ border: '1px solid rgba(216,187,132,.4)', background: 'linear-gradient(150deg,rgba(184,151,98,.1),rgba(12,7,24,.5))', padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                      <span style={{ width: 6, height: 6, transform: 'rotate(45deg)', background: 'var(--gold-hi)', display: 'inline-block' }} />
                      <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: 9, color: 'var(--gold-hi)' }}>SLAYER'S SPOILS</span>
                    </div>
                    <div style={{ fontSize: 13, fontStyle: 'italic', color: 'var(--muted)', marginTop: 5, lineHeight: 1.35 }}>
                      Fell it before dusk: guild coin for all kin, and the top blade claims the richest share.
                    </div>
                  </div>
                </div>
              </div>
              )
            })()}

            {tab === 'chat' && <GuildChat kinCount={data.members.length} />}
          </div>
        </>
      )}

      {/* the strike's battle, animated like any arena fight */}
      {strikeFight && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 400, background: 'rgba(5,4,10,.94)', overflowY: 'auto', padding: '30px 20px' }}>
          <div style={{ maxWidth: 1100, margin: '0 auto' }}>
            <div className="ilm-micro" style={{ color: 'var(--red-hi)', textAlign: 'center', marginBottom: 10 }}>THE DAILY HUNT · {data?.boss?.name?.toUpperCase()}</div>
            <CombatArena
              combatData={strikeFight.combat}
              onComplete={() => {
                emitToast(strikeFight.message || `Your strike lands for ${strikeFight.damage?.toLocaleString()}.`, strikeFight.killed ? 'success' : 'success')
                setStrikeFight(null)
                load()
              }}
            />
            <div style={{ textAlign: 'center', marginTop: 12 }}>
              <button className="ilm-btn ilm-btn-ghost" onClick={() => { emitToast(strikeFight.message, 'success'); setStrikeFight(null); load() }}>SKIP THE TALE</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
