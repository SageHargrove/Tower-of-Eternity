import React, { useState, useEffect, useRef } from 'react'
import { getActiveRun, startRun, advanceFloor, abandonRun, getTeam } from '../api/client'
import HeroCard from '../components/HeroCard'

function FloorBadge({ type }) {
  const colors = {
    combat: 'var(--red)',
    miniboss: '#c87030',
    boss: 'var(--star7)',
    event: 'var(--blue)',
    resource: 'var(--green)',
  }
  return (
    <span style={{
      background: colors[type] || 'var(--border)',
      color: '#fff',
      fontSize: '0.65rem',
      fontFamily: 'Cinzel, serif',
      letterSpacing: '0.08em',
      padding: '0.15rem 0.5rem',
      borderRadius: 2,
      textTransform: 'uppercase',
    }}>
      {type}
    </span>
  )
}

function CombatLog({ lines }) {
  const ref = useRef(null)
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [lines])

  return (
    <div className="combat-log" ref={ref}>
      {lines.map((line, i) => {
        let cls = ''
        if (line.includes('✦') && line.includes('fallen')) cls = 'log-death'
        else if (line.includes('✓ Victory')) cls = 'log-victory'
        else if (line.includes('CRITICAL')) cls = 'log-crit'
        return <div key={i} className={cls}>{line}</div>
      })}
    </div>
  )
}

export default function TowerPage() {
  const [run, setRun] = useState(null)
  const [team, setTeam] = useState([])
  const [loading, setLoading] = useState(true)
  const [advancing, setAdvancing] = useState(false)
  const [lastResult, setLastResult] = useState(null)
  const [allLogs, setAllLogs] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => { refresh() }, [])

  async function refresh() {
    setLoading(true)
    try {
      const [runData, teamData] = await Promise.all([getActiveRun(), getTeam()])
      setRun(runData.run)
      setTeam(teamData)
    } finally {
      setLoading(false)
    }
  }

  async function handleStartRun() {
    setError(null)
    try {
      await startRun()
      setLastResult(null)
      setAllLogs([])
      await refresh()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleAdvance() {
    setAdvancing(true)
    setError(null)
    try {
      const result = await advanceFloor()
      setLastResult(result)

      // Accumulate combat logs
      if (result.combat?.log) {
        setAllLogs(prev => [
          ...prev,
          `\n── Floor ${result.floor} (${result.floor_type}) ──`,
          ...result.combat.log,
        ])
      } else if (result.message) {
        setAllLogs(prev => [...prev, `\n── Floor ${result.floor} ──`, result.message])
      }

      await refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setAdvancing(false)
    }
  }

  async function handleAbandon() {
    if (!confirm('Abandon this run? Heroes will survive but progress is lost.')) return
    await abandonRun()
    setRun(null)
    setLastResult(null)
    setAllLogs([])
    await refresh()
  }

  if (loading) return <div className="page text-dim">Loading...</div>

  const runOver = lastResult?.run_over
  const checkpoint = lastResult?.checkpoint

  return (
    <div className="page">
      <div className="section-header">The Tower</div>

      {/* No active run */}
      {!run && (
        <div>
          {team.length === 0 ? (
            <div className="card" style={{ maxWidth: 400 }}>
              <div className="text-dim" style={{ marginBottom: '1rem' }}>
                No team selected. Go to Heroes and select up to 5 heroes for your team.
              </div>
            </div>
          ) : (
            <div>
              <div className="card" style={{ maxWidth: 400, marginBottom: '1.5rem' }}>
                <div className="text-dim text-sm" style={{ marginBottom: '0.75rem' }}>
                  Current team: {team.length} hero{team.length !== 1 ? 'es' : ''}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                  {team.map(h => (
                    <div key={h.id} style={{ fontSize: '0.8rem' }}>
                      <span className="text-gold" style={{ fontFamily: 'Cinzel, serif' }}>{h.name}</span>
                      <span className="text-dim"> {h.birth_star}★</span>
                    </div>
                  ))}
                </div>
                <button className="btn btn-primary" onClick={handleStartRun}>
                  Enter the Tower
                </button>
                {error && <div className="text-red text-sm" style={{ marginTop: '0.5rem' }}>{error}</div>}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Active run */}
      {run && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          {/* Left: status + controls */}
          <div>
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <div>
                  <div className="text-dim text-sm">Current Floor</div>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '2rem', color: 'var(--text-hi)' }}>
                    {run.current_floor}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  {lastResult && <FloorBadge type={lastResult.floor_type} />}
                  <div className="text-dim text-sm" style={{ marginTop: '0.3rem' }}>
                    Next: Floor {run.current_floor + 1}
                  </div>
                  {(() => {
                    const next = run.current_floor + 1
                    const mod = next % 10
                    if (mod === 0) return <div className="text-sm" style={{ color: 'var(--star7)' }}>⚠ BOSS FLOOR</div>
                    if (mod === 5) return <div className="text-sm" style={{ color: '#c87030' }}>⚠ Mini-boss</div>
                    return null
                  })()}
                </div>
              </div>

              {checkpoint && (
                <div className="text-green text-sm" style={{ marginBottom: '0.75rem', padding: '0.5rem', background: 'rgba(74,154,106,0.1)', borderRadius: 3 }}>
                  ✓ Checkpoint reached! Rest at Base to recover.
                </div>
              )}

              {runOver && (
                <div className="text-red" style={{ marginBottom: '0.75rem', padding: '0.5rem', background: 'rgba(192,64,64,0.1)', borderRadius: 3 }}>
                  ✦ All heroes have fallen. Run ended.
                </div>
              )}

              {error && <div className="text-red text-sm" style={{ marginBottom: '0.5rem' }}>{error}</div>}

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {!runOver && !checkpoint && (
                  <button className="btn btn-primary" onClick={handleAdvance} disabled={advancing}>
                    {advancing ? 'Advancing...' : `Advance to Floor ${run.current_floor + 1}`}
                  </button>
                )}
                {(runOver || checkpoint) && (
                  <button className="btn btn-gold" onClick={() => { setRun(null); setLastResult(null); refresh() }}>
                    Return to Base
                  </button>
                )}
                {!runOver && (
                  <button className="btn btn-danger" onClick={handleAbandon}>
                    Abandon
                  </button>
                )}
              </div>
            </div>

            {/* Narrative */}
            {lastResult?.narrative && (
              <div className="narrative">{lastResult.narrative}</div>
            )}

            {/* Resource / event result */}
            {lastResult?.floor_type === 'resource' && (
              <div className="card text-green text-sm">{lastResult.message}</div>
            )}

            {/* Team status */}
            <div className="section-header" style={{ marginTop: '1.5rem' }}>Team Status</div>
            <div className="hero-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))' }}>
              {run.heroes?.map(h => <HeroCard key={h.id} hero={h} />)}
              {run.heroes?.length === 0 && (
                <div className="text-red text-sm">No heroes remaining.</div>
              )}
            </div>
          </div>

          {/* Right: combat log */}
          <div>
            <div className="section-header">Combat Log</div>
            {allLogs.length > 0
              ? <CombatLog lines={allLogs} />
              : <div className="text-dim text-sm">Advance to begin.</div>
            }
          </div>
        </div>
      )}
    </div>
  )
}
