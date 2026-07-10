/*
 * ALLIES / Social — live (arena server /social/*). FELLOWSHIP title +
 * invite + pending (left), allies list ranked by climb (center).
 * The mockup's Hero Exchange rail was scrapped by design decision
 * (docs/guild-social-design.md) — allies are fellowship + leaderboard.
 */
import React, { useState, useEffect } from 'react'
import {
  getArenaToken, socialAllies, socialInvite, socialDecide, socialRemove,
} from '../api/arenaServerClient'
import Pennant from './Pennant'
import { emitToast } from '../toastBus'

function AllyPennant({ banner }) {
  return banner?.cloth
    ? <Pennant cloth={banner.cloth} cut={banner.cut || 'swallow'} frameTier={banner.frame_tier || 1} sigil={banner.sigil} emblem={banner.emblem} paint={banner.paint} width={16} />
    : <span className="ilm-social-pennant" />
}

export default function Social({ onClose }) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [invite, setInvite] = useState('')
  const [busy, setBusy] = useState(null)

  async function load() {
    try { setData(await socialAllies()); setErr(null) } catch (e) { setErr(e.message) }
  }
  useEffect(() => { if (getArenaToken()) load() }, [])

  async function act(key, fn) {
    setBusy(key)
    try {
      const res = await fn()
      if (res?.message) emitToast(res.message, 'success')
      await load()
    } catch (e) { emitToast(e.message, 'error') } finally { setBusy(null) }
  }

  if (!getArenaToken()) {
    return (
      <div className="ilm-social">
        <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24 }} onClick={onClose}>✕</button>
        <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>FELLOWSHIP</div>
        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.4rem', color: 'var(--text-hi)' }}>ALLIES</div>
        <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 12 }}>
          Fellowship lives on the World Server — log in from the Arena screen first.
        </div>
      </div>
    )
  }

  return (
    <div className="ilm-social">
      <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>
      <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>FELLOWSHIP</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.4rem', color: 'var(--text-hi)', letterSpacing: '.04em', textShadow: '0 6px 40px rgba(124,58,214,.4)' }}>ALLIES</div>
      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 2 }}>The Tower is climbed alone — but never survived alone.</div>
      {err && <div className="ilm-micro" style={{ color: 'var(--red-hi)', marginTop: 8 }}>{err}</div>}

      <div style={{ display: 'flex', gap: 20, marginTop: 18, flexWrap: 'wrap' }}>
        {/* left: invite + pending */}
        <div style={{ flex: '1 1 260px', minWidth: 250 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              placeholder="SEEK AN ALLY BY NAME…" value={invite} onChange={e => setInvite(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && invite.trim()) { act('invite', () => socialInvite(invite.trim())); setInvite('') } }}
              style={{ flex: 1, background: 'rgba(12,7,24,.7)', border: '1px solid var(--border)', color: 'var(--text-hi)', padding: '9px 12px', fontFamily: "'Cinzel',serif", fontSize: '0.66rem', letterSpacing: '.12em' }} />
            <button className="ilm-btn ilm-btn-violet" disabled={!invite.trim() || busy === 'invite'}
              onClick={() => { act('invite', () => socialInvite(invite.trim())); setInvite('') }}>INVITE</button>
          </div>

          {data?.incoming?.length > 0 && (
            <>
              <div className="ilm-guild-sec" style={{ marginTop: 16 }}>
                <span className="ilm-guild-secdot" style={{ background: 'var(--gold-hi)' }} />
                <span className="ilm-guild-seclabel" style={{ color: 'var(--gold-hi)' }}>PENDING · {data.incoming.length}</span>
              </div>
              {data.incoming.map(a => (
                <div key={a.username} className="ilm-guild-member" style={{ marginTop: 6 }}>
                  <AllyPennant banner={a.banner} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.72rem', color: 'var(--text-hi)' }}>{a.username.toUpperCase()}</div>
                    <div style={{ fontStyle: 'italic', fontSize: '0.76rem', color: 'var(--text-dim)' }}>{a.guild || 'guildless'} · floor {a.highest_floor}</div>
                  </div>
                  <button className="ilm-btn ilm-btn-gold" style={{ padding: '0.25rem 0.7rem' }} disabled={busy === a.username} onClick={() => act(a.username, () => socialDecide(a.username, true))}>ACCEPT</button>
                  <button className="ilm-btn ilm-btn-ghost" style={{ padding: '0.25rem 0.7rem' }} disabled={busy === a.username} onClick={() => act(a.username, () => socialDecide(a.username, false))}>DECLINE</button>
                </div>
              ))}
            </>
          )}

          {data?.outgoing?.length > 0 && (
            <>
              <div className="ilm-guild-sec" style={{ marginTop: 16 }}>
                <span className="ilm-guild-secdot" style={{ background: 'var(--muted)' }} />
                <span className="ilm-guild-seclabel" style={{ color: 'var(--muted)' }}>AWAITING WORD</span>
              </div>
              {data.outgoing.map(a => (
                <div key={a.username} className="ilm-guild-member" style={{ marginTop: 6, opacity: 0.7 }}>
                  <AllyPennant banner={a.banner} />
                  <span style={{ flex: 1, fontFamily: "'Cinzel',serif", fontSize: '0.72rem', color: 'var(--text-dim)' }}>{a.username.toUpperCase()}</span>
                  <span className="ilm-micro" style={{ color: 'var(--muted)' }}>SENT</span>
                </div>
              ))}
            </>
          )}
        </div>

        {/* center: allies ranked by climb */}
        <div style={{ flex: '2 1 380px', minWidth: 300 }}>
          <div className="ilm-guild-sec">
            <span className="ilm-guild-secdot" />
            <span className="ilm-guild-seclabel">ALLIES · {data?.allies?.length ?? 0}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
            {(data?.allies || []).map((a, i) => (
              <div key={a.username} className="ilm-guild-member">
                <span className="ilm-micro" style={{ width: 20, color: i < 3 ? 'var(--gold-hi)' : 'var(--muted)' }}>#{i + 1}</span>
                <AllyPennant banner={a.banner} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.76rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{a.username.toUpperCase()}</div>
                  <div style={{ fontStyle: 'italic', fontSize: '0.78rem', color: 'var(--text-dim)' }}>{a.guild ? `${a.guild} · ` : ''}elo {a.elo}</div>
                </div>
                <span style={{ fontFamily: "'Cinzel',serif", fontSize: '0.78rem', color: 'var(--gold-hi)' }}>FLOOR {a.highest_floor}</span>
                <button className="ilm-btn ilm-btn-ghost" style={{ padding: '0.2rem 0.6rem', fontSize: '0.52rem' }} disabled={busy === `rm${a.username}`}
                  onClick={() => { if (window.confirm(`Strike ${a.username} from your fellowship?`)) act(`rm${a.username}`, () => socialRemove(a.username)) }}>✕</button>
              </div>
            ))}
            {data && data.allies.length === 0 && (
              <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', padding: '2rem 0', textAlign: 'center' }}>
                No allies yet — seek a name, send word.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
