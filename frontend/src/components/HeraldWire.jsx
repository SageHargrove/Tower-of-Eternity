/*
 * THE HERALD'S WIRE — the world-chat overlay behind the top bar's chat icon
 * (mockup "Chat - Illuminated", "The Herald's Wire"). Channel rail:
 * WORLD · GUILD · WHISPERS · TRADE & TRAINING. Live against the arena
 * server's /chat/* endpoints: since-id polling, per-channel slowmode
 * (world 5s · trade 5min), whisper threads with unread badges.
 */
import React, { useState, useEffect, useRef } from 'react'
import { getArenaToken, getArenaUsername, chatSend, chatFetch, chatWhispers, chatWhisperThread } from '../api/arenaServerClient'

const CHANNELS = [
  { id: 'world', label: 'WORLD', meta: 'FLOORS 1–100' },
  { id: 'guild', label: 'GUILD' },
  { id: 'whispers', label: 'WHISPERS' },
  { id: 'trade', label: 'TRADE & TRAINING' },
]
const POLL_MS = 5000
const SENDER_COLORS = ['#7ecfd8', '#e8a06a', '#c8a9f5', '#ffd88a', '#8fbf9f', '#e0a8b8']

function senderColor(name) {
  let h = 0
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0
  return SENDER_COLORS[h % SENDER_COLORS.length]
}

function fmtTime(at) {
  return new Date(at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function railStyle(active) {
  return {
    cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
    fontFamily: "'Cinzel',serif", fontWeight: active ? 700 : 500, letterSpacing: '.16em', fontSize: 11,
    color: active ? 'var(--gold-hi)' : 'var(--muted)',
    border: active ? '1px solid rgba(216,187,132,.55)' : '1px solid rgba(150,110,230,.25)',
    background: active ? 'linear-gradient(90deg,rgba(184,151,98,.14),rgba(12,7,24,.5))' : 'rgba(12,7,24,.4)',
    padding: '12px 14px',
    clipPath: active ? 'polygon(8px 0,100% 0,100% 100%,0 100%)' : undefined,
  }
}

function QuietState({ lines }) {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10, padding: 24, textAlign: 'center' }}>
      <span style={{ width: 26, height: 26, transform: 'rotate(45deg)', border: '1px dashed rgba(150,110,230,.45)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ transform: 'rotate(-45deg)', color: 'var(--lavender)', fontFamily: "'Cinzel',serif", fontSize: 11 }}>✦</span>
      </span>
      {lines.map((l, i) => (
        <div key={i} style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 15, lineHeight: 1.5, maxWidth: 420 }}>{l}</div>
      ))}
    </div>
  )
}

// One spoken line — diamond monogram, name + floor/time, italic text.
function MessageRow({ m, isMine }) {
  const c = isMine ? '#8fbf9f' : senderColor(m.sender)
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', flexDirection: isMine ? 'row-reverse' : 'row' }}>
      <span style={{ width: 22, height: 22, transform: 'rotate(45deg)', border: `1px solid ${c}`, background: '#1c1030', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none', marginTop: 2 }}>
        <span style={{ transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontSize: 9, color: c }}>{isMine ? '✦' : m.sender[0].toUpperCase()}</span>
      </span>
      <div style={{ minWidth: 0, ...(isMine ? { border: '1px solid rgba(150,110,230,.35)', background: 'linear-gradient(90deg,transparent,rgba(124,58,214,.12))', padding: '6px 10px' } : {}) }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, justifyContent: isMine ? 'flex-end' : 'flex-start' }}>
          <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 10, letterSpacing: '.08em', color: c }}>{isMine ? 'YOU' : m.sender.toUpperCase()}</span>
          <span style={{ fontFamily: "'Cinzel',serif", fontSize: 7, letterSpacing: '.14em', color: 'var(--muted)' }}>
            {m.floor > 0 ? `FLOOR ${m.floor} · ` : ''}{fmtTime(m.at)}
          </span>
        </div>
        <div style={{ fontSize: 14, fontStyle: 'italic', color: '#d8cfe6', marginTop: 2, textAlign: isMine ? 'right' : 'left', overflowWrap: 'anywhere' }}>{m.text}</div>
      </div>
    </div>
  )
}

export default function HeraldWire({ onClose, onOpenGuild }) {
  const [channel, setChannel] = useState('world')
  const [messages, setMessages] = useState([])
  const [listeners, setListeners] = useState(null)
  const [threads, setThreads] = useState([])
  const [thread, setThread] = useState(null)      // active whisper partner
  const [newWhisper, setNewWhisper] = useState('')
  const [draft, setDraft] = useState('')
  const [cooldown, setCooldown] = useState(0)
  const [slowmode, setSlowmode] = useState(0)
  const [err, setErr] = useState(null)
  const [offline, setOffline] = useState(false)
  const scrollRef = useRef(null)
  const connected = !!getArenaToken()
  const me = getArenaUsername()

  // Poll the active channel.
  useEffect(() => {
    if (!connected) return
    let live = true
    setMessages([]); setErr(null)
    async function poll() {
      try {
        if (channel === 'whispers') {
          const t = await chatWhispers()
          if (!live) return
          setThreads(t.threads || [])
          setOffline(false)
          if (thread) {
            const d = await chatWhisperThread(thread)
            if (live) setMessages(d.messages || [])
          }
        } else {
          const d = await chatFetch(channel)
          if (!live) return
          setMessages(d.messages || [])
          setSlowmode(d.slowmode || 0)
          setCooldown(d.cooldown_remaining || 0)
          if (d.listeners != null) setListeners(d.listeners)
          setOffline(false)
        }
      } catch (e) {
        if (live) setOffline(true)
      }
    }
    poll()
    const iv = setInterval(poll, POLL_MS)
    return () => { live = false; clearInterval(iv) }
  }, [channel, thread, connected])

  // Cooldown countdown tick.
  useEffect(() => {
    if (cooldown <= 0) return
    const iv = setInterval(() => setCooldown(c => Math.max(0, c - 1)), 1000)
    return () => clearInterval(iv)
  }, [cooldown > 0])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages])

  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  async function send() {
    const text = draft.trim()
    if (!text || cooldown > 0) return
    setErr(null)
    try {
      if (channel === 'whispers') {
        if (!thread) { setErr('Open a thread first — whisper a name.'); return }
        await chatSend('whisper', text, thread)
        const d = await chatWhisperThread(thread)
        setMessages(d.messages || [])
      } else {
        const res = await chatSend(channel, text)
        setCooldown(res.cooldown || 0)
        const d = await chatFetch(channel)
        setMessages(d.messages || [])
      }
      setDraft('')
    } catch (e) {
      setErr(e.message)
      const m = String(e.message).match(/(\d+)s/)
      if (m) setCooldown(Number(m[1]))
    }
  }

  function openWhisper(name) {
    const clean = (name || '').trim()
    if (!clean) return
    setChannel('whispers')
    setThread(clean)
    setNewWhisper('')
  }

  const totalUnread = threads.reduce((s, t) => s + (t.unread || 0), 0)
  const paneTitle = channel === 'world' ? 'WORLD CHANNEL'
    : channel === 'guild' ? 'GUILD CHANNEL'
    : channel === 'whispers' ? (thread ? `WHISPER · ${thread.toUpperCase()}` : 'WHISPERS')
    : 'TRADE & TRAINING'
  const paneMeta = channel === 'world' && listeners != null ? `${listeners.toLocaleString()} CLIMBERS ON THE WIRE` : ''
  const inputHint = channel === 'world' ? 'Speak to the whole Tower…'
    : channel === 'guild' ? 'Speak to your lodge…'
    : channel === 'whispers' ? (thread ? `Whisper to ${thread}…` : 'Open a thread first…')
    : 'Post an offer — it fades after a day…'
  const canSend = connected && !offline && draft.trim() && cooldown <= 0 && (channel !== 'whispers' || thread)

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 400, background: '#08060e', overflowY: 'auto', fontFamily: "'Cormorant Garamond',serif", color: '#efe8da' }}>
      {/* ambient */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', background: 'radial-gradient(70% 60% at 20% 20%, rgba(96,42,168,.25), rgba(0,0,0,0) 60%), radial-gradient(140% 120% at 50% 120%, #0d0818, #08060e 72%)' }} />
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', background: 'repeating-linear-gradient(115deg, rgba(184,151,98,.05) 0 1px, transparent 1px 120px), repeating-linear-gradient(-65deg, rgba(150,110,230,.045) 0 1px, transparent 1px 120px)' }} />

      <div style={{ position: 'relative', maxWidth: 1280, margin: '0 auto', padding: '28px 40px 40px', minHeight: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 2 }}>
              <span style={{ width: 9, height: 9, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
              <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 600, letterSpacing: '.5em', fontSize: 13, color: 'var(--gold)' }}>THE HERALD'S WIRE</span>
            </div>
            <div className="ilm-title-stack">
              <div className="ghost">DISPATCH</div>
              <div className="solid">HERALD</div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: '.16em', color: 'var(--muted)', marginTop: 14 }}>ESC · CLOSE</button>
        </div>

        {/* chat frame */}
        <div style={{ flex: 1, display: 'flex', gap: 12, marginTop: 14, minHeight: 440 }}>
          {/* channel rail */}
          <div style={{ width: 212, flex: 'none', display: 'flex', flexDirection: 'column', gap: 7 }}>
            {CHANNELS.map(c => (
              <div key={c.id} onClick={() => { setChannel(c.id); if (c.id !== 'whispers') setThread(null); setErr(null) }} style={railStyle(channel === c.id)}>
                <span style={{ flex: 1 }}>{c.label}</span>
                {c.id === 'world' && <span style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.1em', color: 'var(--muted)' }}>{c.meta}</span>}
                {c.id === 'whispers' && totalUnread > 0 && (
                  <span style={{ width: 16, height: 16, borderRadius: '50%', background: '#c04040', boxShadow: '0 0 7px #c04040', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'Cinzel',serif", fontSize: 8, color: 'var(--text-hi)', flex: 'none' }}>{totalUnread}</span>
                )}
              </div>
            ))}
            <span style={{ flex: 1 }} />
            <div style={{ border: '1px solid rgba(184,151,98,.3)', background: 'rgba(12,7,24,.45)', padding: '10px 12px' }}>
              <div style={{ fontSize: 11.5, fontStyle: 'italic', color: 'var(--muted)', lineHeight: 1.4 }}>
                Guild speech also lives in the <span onClick={onOpenGuild} style={{ color: 'var(--gold-hi)', cursor: onOpenGuild ? 'pointer' : 'default' }}>Guild Hall</span>. Whisper any name to open a thread.
              </div>
            </div>
          </div>

          {/* message pane */}
          <div style={{ flex: 1, border: '1px solid rgba(184,151,98,.35)', background: 'rgba(12,7,24,.5)', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '11px 16px', borderBottom: '1px solid rgba(184,151,98,.2)' }}>
              <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
              <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: 10, color: 'var(--gold)' }}>{paneTitle}</span>
              <span style={{ flex: 1 }} />
              <span style={{ fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: '.14em', color: offline ? '#e08585' : 'var(--muted)' }}>
                {offline ? 'NO SIGNAL' : paneMeta}
              </span>
            </div>

            {/* whisper thread strip */}
            {channel === 'whispers' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 16px', borderBottom: '1px solid rgba(184,151,98,.15)', flexWrap: 'wrap' }}>
                <span style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.18em', color: 'var(--muted)', flex: 'none' }}>THREADS</span>
                {threads.map(t => (
                  <div key={t.with} onClick={() => setThread(t.with)}
                    style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: '.12em', padding: '5px 12px',
                      color: thread === t.with ? 'var(--gold-hi)' : '#c9bfa8',
                      border: thread === t.with ? '1px solid rgba(216,187,132,.55)' : '1px solid rgba(150,110,230,.3)',
                      background: thread === t.with ? 'rgba(184,151,98,.1)' : 'transparent' }}>
                    {t.with.toUpperCase()}
                    {t.unread > 0 && <span style={{ width: 14, height: 14, borderRadius: '50%', background: '#c04040', boxShadow: '0 0 6px #c04040', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 7, color: 'var(--text-hi)', marginLeft: 6 }}>{t.unread}</span>}
                  </div>
                ))}
                <span style={{ flex: 1 }} />
                <form onSubmit={e => { e.preventDefault(); openWhisper(newWhisper) }} style={{ display: 'flex', gap: 6 }}>
                  <input value={newWhisper} onChange={e => setNewWhisper(e.target.value)} placeholder="＋ whisper a name…"
                    style={{ width: 140, border: '1px dashed rgba(138,123,176,.4)', background: 'none', padding: '4px 10px', fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.14em', color: '#c9bfa8', outline: 'none' }} />
                </form>
              </div>
            )}

            {/* messages */}
            <div ref={scrollRef} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 11, padding: '14px 18px', overflowY: 'auto' }}>
              {!connected && <QuietState lines={['No signal from the world server. Connect on the World page and the wire will carry every climber\'s voice.']} />}
              {connected && offline && <QuietState lines={['The wire is down — no signal from the world server. It hums again the moment the server answers.']} />}
              {connected && !offline && channel === 'whispers' && !thread && threads.length === 0 && (
                <QuietState lines={['No whispers yet. Type a name above and send the first word.']} />
              )}
              {connected && !offline && channel === 'whispers' && !thread && threads.length > 0 && (
                <QuietState lines={['Pick a thread above to read it.']} />
              )}
              {connected && !offline && (channel !== 'whispers' || thread) && messages.length === 0 && (
                <QuietState lines={[
                  channel === 'world' ? 'The wire hums, but no climber is speaking. Say the first word.'
                    : channel === 'guild' ? 'The lodge keeps its counsel — break the silence.'
                    : channel === 'trade' ? 'The notice board is bare. Post an offer — it fades after a day.'
                    : 'The thread is empty — send the first whisper.',
                ]} />
              )}
              {connected && !offline && messages.map(m => (
                <MessageRow key={m.id} m={m} isMine={m.sender === me} />
              ))}
            </div>

            {/* input */}
            <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(184,151,98,.2)' }}>
              <form onSubmit={e => { e.preventDefault(); send() }} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <input value={draft} onChange={e => setDraft(e.target.value)} maxLength={300}
                  disabled={!connected || offline || (channel === 'whispers' && !thread)}
                  placeholder={inputHint}
                  style={{ flex: 1, border: '1px solid rgba(184,151,98,.35)', background: 'rgba(8,6,14,.6)', padding: '9px 14px', fontSize: 14, fontStyle: 'italic', fontFamily: "'Cormorant Garamond',serif", color: 'var(--text-hi)', outline: 'none' }} />
                <button type="submit" disabled={!canSend}
                  style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 11, cursor: canSend ? 'pointer' : 'default',
                    color: canSend ? '#0a0710' : '#6f628c',
                    background: canSend ? 'linear-gradient(120deg,#d8bb84,#b89762)' : 'none',
                    border: canSend ? 'none' : '1px solid rgba(138,123,176,.35)',
                    padding: '9px 22px', clipPath: 'polygon(8px 0,100% 0,calc(100% - 8px) 100%,0 100%)' }}>
                  {cooldown > 0 ? `${cooldown}S` : 'SEND'}
                </button>
              </form>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginTop: 8 }}>
                <span style={{ width: 5, height: 5, transform: 'rotate(45deg)', background: cooldown > 0 ? '#e08585' : 'var(--muted)', display: 'inline-block' }} />
                <span style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.16em', color: cooldown > 0 ? '#e08585' : 'var(--muted)' }}>
                  {err ? String(err).toUpperCase()
                    : slowmode > 0 && channel !== 'whispers'
                      ? `SLOWMODE · ONE MESSAGE EVERY ${slowmode >= 60 ? `${Math.round(slowmode / 60)} MIN` : `${slowmode}S`}`
                      : 'THE WIRE CARRIES PLAIN WORDS ONLY'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
