import React, { useState, useEffect } from 'react'
import { getBase, restHeroes } from '../api/client'

export default function BasePage({ onGoldChange }) {
  const [base, setBase] = useState(null)
  const [resting, setResting] = useState(false)
  const [msg, setMsg] = useState(null)

  useEffect(() => { load() }, [])

  async function load() {
    const data = await getBase()
    setBase(data)
  }

  async function handleRest() {
    setResting(true)
    setMsg(null)
    try {
      const result = await restHeroes()
      setMsg(`${result.rested} hero${result.rested !== 1 ? 'es' : ''} rested. Morale and stress recovered.`)
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setMsg(e.message)
    } finally {
      setResting(false)
    }
  }

  if (!base) return <div className="page text-dim">Loading...</div>

  let materials = {}
  try { materials = JSON.parse(base.materials || '{}') } catch {}

  return (
    <div className="page">
      <div className="section-header">Home Base</div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.1rem', color: 'var(--text-hi)', marginBottom: '0.5rem' }}>
            {base.name}
          </div>
          <div className="text-dim text-sm" style={{ marginBottom: '1rem' }}>Base Level {base.level}</div>
          <div style={{ marginBottom: '0.5rem' }}>
            <span className="text-dim text-sm">Gold: </span>
            <span className="text-gold" style={{ fontFamily: 'Cinzel, serif' }}>{base.gold.toLocaleString()}</span>
          </div>
          {Object.keys(materials).length > 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              <div className="text-dim text-sm" style={{ marginBottom: '0.3rem' }}>Materials:</div>
              {Object.entries(materials).map(([k, v]) => (
                <div key={k} className="text-sm">
                  <span className="text-dim">{k}: </span><span>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.9rem', color: 'var(--text-hi)', marginBottom: '0.75rem' }}>
            Rest & Recovery
          </div>
          <div className="text-dim text-sm" style={{ lineHeight: 1.6, marginBottom: '1rem' }}>
            Resting at base recovers morale (+25), reduces stress (−20), and slowly heals trauma (−5) for all living heroes.
          </div>
          <button className="btn btn-gold" onClick={handleRest} disabled={resting}>
            {resting ? 'Resting...' : 'Rest All Heroes'}
          </button>
          {msg && (
            <div className={`text-sm ${msg.includes('rested') ? 'text-green' : 'text-red'}`}
                 style={{ marginTop: '0.5rem' }}>
              {msg}
            </div>
          )}
        </div>

        <div className="card">
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.9rem', color: 'var(--text-hi)', marginBottom: '0.75rem' }}>
            Upcoming Features
          </div>
          <div className="text-dim text-sm" style={{ lineHeight: 1.8 }}>
            ○ Ascension system<br />
            ○ Synthesis (hero sacrifice)<br />
            ○ Base upgrades<br />
            ○ Legacy system (fallen heroes)<br />
            ○ Skill unlocks
          </div>
        </div>
      </div>
    </div>
  )
}
