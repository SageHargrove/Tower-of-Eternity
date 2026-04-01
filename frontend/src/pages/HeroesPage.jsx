import React, { useState, useEffect } from 'react'
import { listHeroes, setTeam, dismissHero } from '../api/client'
import HeroCard from '../components/HeroCard'

export default function HeroesPage() {
  const [heroes, setHeroes] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [filter, setFilter] = useState('alive') // alive | all | dead
  const [expandedId, setExpandedId] = useState(null)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)

  useEffect(() => { load() }, [filter])

  async function load() {
    const data = await listHeroes(filter === 'alive')
    setHeroes(filter === 'dead' ? data.filter(h => !h.is_alive) : data)
    // Restore team selection state
    const teamIds = new Set(data.filter(h => h.is_on_team).map(h => h.id))
    setSelected(teamIds)
  }

  function toggleSelect(id) {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        if (next.size >= 5) {
          setMsg('Team is full (max 5 heroes)')
          return prev
        }
        next.add(id)
      }
      return next
    })
    setMsg(null)
  }

  async function saveTeam() {
    setSaving(true)
    try {
      await setTeam(Array.from(selected))
      setMsg(`Team saved (${selected.size} heroes)`)
    } catch (e) {
      setMsg(e.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDismiss(id, e) {
    e.stopPropagation()
    if (!confirm('Dismiss this hero permanently?')) return
    await dismissHero(id)
    setSelected(prev => { const n = new Set(prev); n.delete(id); return n })
    load()
  }

  const aliveHeroes = heroes.filter(h => h.is_alive)
  const deadHeroes = heroes.filter(h => !h.is_alive)
  const displayHeroes = filter === 'dead' ? deadHeroes : filter === 'alive' ? aliveHeroes : heroes

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div className="section-header" style={{ marginBottom: 0 }}>
          Heroes — {aliveHeroes.length} alive · {deadHeroes.length} fallen
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            {['alive', 'all', 'dead'].map(f => (
              <button
                key={f}
                className={`btn ${filter === f ? 'btn-gold' : ''}`}
                onClick={() => setFilter(f)}
                style={{ padding: '0.3rem 0.8rem', fontSize: '0.72rem' }}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <button className="btn btn-primary" onClick={saveTeam} disabled={saving}>
            {saving ? 'Saving...' : `Set Team (${selected.size}/5)`}
          </button>
        </div>
      </div>

      {msg && (
        <div className={`text-sm ${msg.includes('saved') ? 'text-green' : 'text-red'}`}
             style={{ marginBottom: '1rem' }}>
          {msg}
        </div>
      )}

      <div className="text-dim text-sm" style={{ marginBottom: '1rem' }}>
        Click heroes to add/remove from team. Max 5.
      </div>

      {displayHeroes.length === 0 && (
        <div className="text-dim" style={{ padding: '2rem 0' }}>
          No heroes here. Visit the Summoning Gate.
        </div>
      )}

      <div className="hero-grid">
        {displayHeroes.map(hero => (
          <div key={hero.id} style={{ position: 'relative' }}>
            <HeroCard
              hero={hero}
              selected={selected.has(hero.id)}
              onClick={() => {
                if (expandedId === hero.id) {
                  setExpandedId(null)
                } else {
                  setExpandedId(hero.id)
                  toggleSelect(hero.id)
                }
              }}
              showFull={expandedId === hero.id}
            />
            {hero.is_alive && (
              <button
                className="btn btn-danger"
                style={{ position: 'absolute', top: 6, left: 8, padding: '0.15rem 0.5rem', fontSize: '0.65rem' }}
                onClick={(e) => handleDismiss(hero.id, e)}
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
