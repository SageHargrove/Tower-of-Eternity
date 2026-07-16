/*
 * THE HEARTH — the global hero-chatter drawer (mockup 1D).
 *
 * The top-right CHATTER toggle slides this in from the right on any screen,
 * so nobody has to walk to Base just to hear the company mutter. Rows are
 * each hero's single latest line (backend /chat/hearth), fronted by the
 * diamond portrait — the same DiamondPortrait the Base lobby feed uses, so
 * chatter reads identically everywhere. A shaken hero's diamond runs red.
 *
 * "A word to the company" sends one of three tones down (rally / reassure /
 * rest): a small real mood nudge roster-wide, plus an in-character reaction
 * that lands right back in the feed.
 */
import React, { useState, useEffect, useCallback } from 'react'
import { getHearth, sendHearthWord } from '../api/client'

/* Diamond-cropped hero face with letter fallback. Exported for the Base
 * lobby chatter feed — consistent hero chatter everywhere. */
export function DiamondPortrait({ heroId, name, size = 46, shaken = false }) {
  const [imgError, setImgError] = useState(false)
  const border = shaken ? 'rgba(217,106,106,.65)' : 'rgba(184,151,98,.55)'
  const inner = size * 1.42
  return (
    <span style={{
      width: size, height: size, transform: 'rotate(45deg)', overflow: 'hidden', flex: 'none',
      border: `1px solid ${border}`, background: 'rgba(12,7,24,.8)', display: 'inline-block',
      boxShadow: shaken ? '0 0 8px rgba(217,106,106,.25)' : 'none',
    }}>
      <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: inner, height: inner, transform: 'rotate(-45deg)', marginLeft: (size - inner) / 2, marginTop: (size - inner) / 2 }}>
        {heroId && !imgError ? (
          <img src={`/heroes/${heroId}/card-image?mini=true`} alt={name} draggable={false}
            onError={() => setImgError(true)}
            style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top' }} />
        ) : (
          <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: size * 0.4, color: 'var(--gold-hi)' }}>
            {(name || '?').charAt(0).toUpperCase()}
          </span>
        )}
      </span>
    </span>
  )
}

function timeAgo(ts) {
  if (!ts) return ''
  const then = new Date(ts.includes('T') || ts.endsWith('Z') ? ts : ts.replace(' ', 'T') + 'Z')
  const mins = Math.floor((Date.now() - then.getTime()) / 60000)
  if (mins < 1) return 'JUST NOW'
  if (mins < 60) return `${mins}M`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}H`
  return `${Math.floor(hrs / 24)}D`
}

const WORDS = [
  { tone: 'rally', label: 'RALLY THEM ⚔' },
  { tone: 'reassure', label: 'REASSURE ✦' },
  { tone: 'rest', label: 'LET THEM REST' },
]

export default function HearthDrawer({ onClose }) {
  const [conversations, setConversations] = useState([])
  const [cooldown, setCooldown] = useState(0)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const data = await getHearth()
      setConversations(data.conversations || [])
      setCooldown(data.cooldown_remaining || 0)
      if (data.newest_at) localStorage.setItem('hearthSeenAt', data.newest_at)
    } catch (e) { console.error(e) }
  }, [])

  useEffect(() => {
    load()
    const iv = setInterval(load, 15000)
    return () => clearInterval(iv)
  }, [load])

  // local cooldown countdown between polls
  useEffect(() => {
    if (cooldown <= 0) return
    const iv = setInterval(() => setCooldown(c => Math.max(0, c - 1)), 1000)
    return () => clearInterval(iv)
  }, [cooldown > 0])

  async function sendWord(tone) {
    setSending(true)
    setError(null)
    try {
      const res = await sendHearthWord(tone)
      setCooldown(res.cooldown || 300)
      await load()
    } catch (e) {
      setError(e.message)
    } finally { setSending(false) }
  }

  return (
    <div className="hearth-drawer">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 18px 0' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ width: 8, height: 8, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
          <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.24em', fontSize: '0.8rem', color: 'var(--text-hi)' }}>THE HEARTH</span>
        </span>
        <button className="ilm-close" onClick={onClose}>✕</button>
      </div>
      <div style={{ fontStyle: 'italic', fontSize: '0.78rem', color: 'var(--violet, #9a7fd8)', padding: '6px 18px 12px', borderBottom: '1px solid rgba(150,130,190,.25)' }}>
        What the company mutters between climbs.
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: 22 }}>
        {conversations.length === 0 && (
          <div className="text-dim" style={{ fontStyle: 'italic', fontSize: '0.85rem', padding: '1rem 0' }}>The hearth is quiet… someone will speak soon.</div>
        )}
        {/* Each conversation is a threaded exchange — the lines stay in
            spoken order so you read the actual back-and-forth, not detached
            one-liners from unrelated moments. */}
        {conversations.map((c, ci) => (
          <div key={`${c.created_at}-${ci}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 9 }}>
              <span style={{ width: 5, height: 5, transform: 'rotate(45deg)', background: 'var(--gold)', flex: 'none' }} />
              <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: '0.56rem', color: 'var(--gold)' }}>{(c.location || 'THE BASE').toUpperCase()}</span>
              <span style={{ height: 1, flex: 1, background: 'rgba(150,130,190,.2)' }} />
              <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.14em', fontSize: '0.54rem', color: 'var(--muted)', flex: 'none' }}>{timeAgo(c.created_at)}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {c.lines.map((l, li) => (
                <div key={li} style={{ display: 'flex', gap: 11, alignItems: 'flex-start' }}>
                  <div style={{ padding: 3, flex: 'none' }}>
                    <DiamondPortrait heroId={l.hero_id} name={l.speaker} size={34} shaken={l.mood === 'shaken'} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.12em', fontSize: '0.62rem', color: 'var(--text-hi)' }}>
                      {l.speaker.toUpperCase()}
                      {l.mood === 'shaken' && <span style={{ color: '#d96a6a', fontSize: '0.52rem', letterSpacing: '.16em' }}> · SHAKEN</span>}
                    </span>
                    <div style={{ marginTop: 3, border: '1px solid rgba(150,130,190,.3)', background: 'rgba(18,12,32,.55)', padding: '8px 11px', fontStyle: 'italic', fontSize: '0.82rem', color: '#cfc2e2', lineHeight: 1.4 }}>
                      “{l.message}”
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{ borderTop: '1px solid rgba(150,130,190,.25)', padding: '12px 18px 16px' }}>
        <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: '0.56rem', color: 'var(--gold)', marginBottom: 10 }}>
          A WORD TO THE COMPANY{cooldown > 0 && <span style={{ color: 'var(--muted)' }}> · {Math.floor(cooldown / 60)}:{String(cooldown % 60).padStart(2, '0')}</span>}
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {WORDS.map(w => (
            <button key={w.tone} disabled={sending || cooldown > 0} onClick={() => sendWord(w.tone)}
              style={{
                fontFamily: "'Cinzel',serif", letterSpacing: '.14em', fontSize: '0.62rem', cursor: cooldown > 0 ? 'not-allowed' : 'pointer',
                padding: '8px 12px', color: cooldown > 0 ? 'var(--muted)' : 'var(--text-hi)',
                border: '1px solid rgba(184,151,98,.4)', background: 'rgba(12,7,24,.6)', opacity: sending ? 0.6 : 1,
              }}>
              {w.label}
            </button>
          ))}
        </div>
        {error && <div style={{ fontSize: '0.68rem', color: '#d98a8a', marginTop: 8 }}>{error}</div>}
      </div>
    </div>
  )
}
