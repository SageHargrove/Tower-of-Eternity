import React, { useState, useEffect } from 'react'
import { pullHeroes, getOdds, getBase } from '../api/client'
import HeroCard from '../components/HeroCard'

export default function SummonPage({ onGoldChange }) {
  const [gold, setGold] = useState(0)
  const [odds, setOdds] = useState(null)
  const [pulling, setPulling] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)
  const [usePortrait, setUsePortrait] = useState(false)

  useEffect(() => {
    getBase().then(b => setGold(b.gold))
    getOdds().then(setOdds)
  }, [])

  async function doPull(count) {
    setPulling(true)
    setError(null)
    try {
      const data = await pullHeroes(count, usePortrait)
      setResults(data.pulled)
      setGold(g => g - data.cost)
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setError(e.message)
    } finally {
      setPulling(false)
    }
  }

  return (
    <div className="page">
      <div className="section-header">Summoning Gate</div>

      <div style={{ display: 'flex', gap: '2rem', alignItems: 'flex-start', flexWrap: 'wrap' }}>
        {/* Pull panel */}
        <div className="card" style={{ minWidth: 260 }}>
          <div style={{ marginBottom: '1rem' }}>
            <div className="text-dim text-sm">Available Gold</div>
            <div className="text-gold" style={{ fontFamily: 'Cinzel, serif', fontSize: '1.4rem' }}>
              {gold.toLocaleString()} g
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <div className="text-dim text-sm" style={{ marginBottom: '0.3rem' }}>Cost</div>
            <div className="text-sm">Single pull: <span className="text-gold">100g</span></div>
            <div className="text-sm">10-pull: <span className="text-gold">1,000g</span></div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={usePortrait}
                onChange={e => setUsePortrait(e.target.checked)}
              />
              <span className="text-dim">Generate portrait (uses DALL-E API)</span>
            </label>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-gold" onClick={() => doPull(1)} disabled={pulling || gold < 100}>
              {pulling ? '...' : 'Pull ×1'}
            </button>
            <button className="btn btn-gold" onClick={() => doPull(10)} disabled={pulling || gold < 1000}>
              {pulling ? '...' : 'Pull ×10'}
            </button>
          </div>

          {error && (
            <div className="text-red text-sm" style={{ marginTop: '0.75rem' }}>{error}</div>
          )}
        </div>

        {/* Odds table */}
        {odds && (
          <div className="card" style={{ minWidth: 200 }}>
            <div className="section-header" style={{ marginBottom: '0.75rem' }}>Pull Rates</div>
            {Object.entries(odds).map(([star, data]) => (
              <div key={star} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '0.3rem' }}>
                <span className={`birth-star-${star}`} style={{ color: `var(--star${star})` }}>
                  {'★'.repeat(Number(star))}
                </span>
                <span className="text-dim">{data.percent}%</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <div className="section-header">Summoned</div>
          <div className="hero-grid">
            {results.map(hero => (
              <HeroCard key={hero.id} hero={hero} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
