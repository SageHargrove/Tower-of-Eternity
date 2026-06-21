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
      <div className="hero-chat-collapsed" onClick={() => setIsOpen(true)}>
        <span style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
          "? Hero Chat
        </span>
      </div>
    )
  }

  return (
    <div className="hero-chat-panel panel">
      <div className="chat-header">
        <h3 style={{ margin: 0 }}>Hero Chatter</h3>
        <button className="btn" onClick={() => setIsOpen(false)} style={{ padding: '0.2rem 0.5rem' }}>x~</button>
      </div>
      
      <div className="chat-scroll">
        {logs.length === 0 ? (
          <div className="text-dim text-center" style={{ padding: '1rem' }}>It's quiet... too quiet.</div>
        ) : (
          logs.map(log => (
            <div key={log.id} className="chat-block">
              <div className="chat-meta text-dim text-xs">
                <span>{new Date(log.created_at + 'Z').toLocaleTimeString()}</span>
                <span> @ {log.location}</span>
              </div>
              <div className="chat-messages">
                {log.messages.map((msg, i) => (
                  <div key={i} className="chat-message">
                    <strong className="text-gold">{msg.speaker}:</strong> {msg.message}
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
