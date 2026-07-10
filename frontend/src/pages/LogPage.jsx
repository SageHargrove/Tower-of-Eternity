import React, { useState, useEffect } from 'react'
import PageTitle from '../components/PageTitle'
import { getEventLog, listRuns } from '../api/client'

export default function LogPage() {
  const [logs, setLogs] = useState([])
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)

  useEffect(() => {
    listRuns().then(setRuns)
    getEventLog(null, 100).then(setLogs)
  }, [])

  async function filterByRun(runId) {
    setSelectedRun(runId)
    const data = await getEventLog(runId, 100)
    setLogs(data)
  }

  const EVENT_COLORS = {
    hero_death: 'var(--red)',
    run_start: 'var(--green)',
    run_end: 'var(--blue)',
  }

  return (
    <div className="page">
      <PageTitle eyebrow="Chronicle" title="EVENT LOG" ghost="RECORD" compact />

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <button
          className={`btn ${!selectedRun ? 'btn-gold' : ''}`}
          onClick={() => { setSelectedRun(null); getEventLog(null, 100).then(setLogs) }}
          style={{ fontSize: '0.72rem', padding: '0.3rem 0.8rem' }}
        >
          All
        </button>
        {runs.slice(0, 10).map(r => (
          <button
            key={r.id}
            className={`btn ${selectedRun === r.id ? 'btn-gold' : ''}`}
            onClick={() => filterByRun(r.id)}
            style={{ fontSize: '0.72rem', padding: '0.3rem 0.8rem' }}
          >
            Run #{r.id} · F{r.highest_floor} · {r.status}
          </button>
        ))}
      </div>

      {logs.length === 0 && (
        <div className="text-dim">No events recorded yet.</div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
        {logs.map(log => (
          <div key={log.id} style={{
            display: 'flex', gap: '1rem', alignItems: 'flex-start',
            padding: '0.5rem 0.75rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 3,
            fontSize: '0.82rem',
          }}>
            <span className="text-dim" style={{ whiteSpace: 'nowrap', minWidth: 60 }}>F{log.floor_number || 0}</span>
            <span style={{ color: EVENT_COLORS[log.event_type] || 'var(--text-dim)', minWidth: 90 }}>
              {log.event_type}
            </span>
            <span className="text-dim">{log.description}</span>
            <span className="text-dim" style={{ marginLeft: 'auto', whiteSpace: 'nowrap', fontSize: '0.72rem' }}>
              {new Date(log.created_at).toLocaleTimeString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
