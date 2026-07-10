import { useState, useEffect } from 'react'
import { getChatLogs } from '../api/client'

export default function HeroChat() {
  const [logs, setLogs] = useState([])
  const [isOpen, setIsOpen] = useState(true)

  useEffect(() => {
    fetchLogs()
    const intv = setInterval(fetchLogs, 15000) // Poll every 15s
    return () => clearInterval(intv)
  }, [])

  async function fetchLogs() {
    try {
      const data = await getChatLogs(5)
      setLogs(data)
    } catch (e) {
      console.error("Failed to fetch chat logs", e)
    }
  }

  if (!isOpen) {
    return (
      <div className="hero-chat-collapsed" onClick={() => setIsOpen(true)} title="Open Hero Chatter">
        <span style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', fontFamily: "'Cinzel',serif", letterSpacing: '.3em', fontSize: '0.66rem', color: 'var(--gold-hi)' }}>
          CHATTER
        </span>
      </div>
    )
  }

  return (
    <div className="hero-chat-panel">
      <span className="ilm-corner" />
      <div className="chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
          <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.24em', fontSize: '0.78rem', color: 'var(--text-hi)' }}>CHATTER</span>
        </div>
        <button className="ilm-close" onClick={() => setIsOpen(false)}>✕</button>
      </div>

      <div className="chat-scroll">
        {logs.length === 0 ? (
          <div className="text-dim text-center" style={{ padding: '1.5rem', fontStyle: 'italic' }}>The halls are quiet… too quiet.</div>
        ) : (
          logs.map(log => (
            <div key={log.id} className="chat-block">
              <div className="chat-meta">
                <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.16em', fontSize: '0.56rem', color: 'var(--gold-hi)' }}>{log.location?.toUpperCase()}</span>
                <span className="text-dim" style={{ fontSize: '0.66rem' }}>{new Date(log.created_at + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <div className="chat-messages">
                {log.messages.map((msg, i) => (
                  <div key={i} className="chat-message">
                    <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.72rem', letterSpacing: '.06em', color: 'var(--gold-hi)' }}>{msg.speaker}</span>
                    <span style={{ color: '#c8b8dd', fontStyle: 'italic' }}> — {msg.message}</span>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
