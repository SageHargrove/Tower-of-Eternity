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
    } finally {
      setDungeoning(false)
    }
  }

  async function handleAssignFloor(heroId, floorNumber) {
    setAssigning(true)
    try {
      await assignBaseFloor(heroId, floorNumber)
      await loadAll()
    } catch (e) {
      alert(e.message)
    } finally {
      setAssigning(false)
    }
  }

  async function handleCraft(slot) {
    if (!confirm(`Craft a new ${slot}? This will cost 500 Gold.`)) return
    setCrafting(true)
    setCraftMsg(null)
    try {
      const res = await craftEquipment(slot)
      setCraftMsg(`Crafted ${res.equipment.name}! (Forged by: ${res.blacksmith_used})`)
      loadAll()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setCraftMsg(typeof e.message === 'string' ? e.message : JSON.stringify(e.message))
    } finally {
      setCrafting(false)
    }
  }

  async function handleBuildFacility(type) {
    setFacilityLoading(true)
    try {
      await buildFacility(type)
      loadAll()
      if (onGoldChange) onGoldChange()
    } catch(e) {
      alert("Error: " + (e.message || JSON.stringify(e)))
    } finally {
      setFacilityLoading(false)
    }
  }

  async function handleAssignFacility(facId, heroId) {
    setFacilityLoading(true)
    try {
      await assignFacility(facId, heroId)
      loadAll()
    } catch(e) {
      alert("Error: " + (e.message || JSON.stringify(e)))
    } finally {
      setFacilityLoading(false)
    }
  }

  async function handleRemoveFacility(heroId) {
    setFacilityLoading(true)
    try {
      await removeFacility(heroId)
      loadAll()
    } catch(e) {
      alert("Error: " + (e.message || JSON.stringify(e)))
    } finally {
      setFacilityLoading(false)
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
          <div style={{ marginBottom: '0.25rem' }}>
            <span className="text-dim text-sm">Gold: </span>
            <span className="text-gold" style={{ fontFamily: 'Cinzel, serif' }}>{base.gold.toLocaleString()}</span>
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            <span className="text-dim text-sm">Supplies: </span>
            <span style={{ fontFamily: 'Cinzel, serif', color: '#c8a030' }}>{base.supplies || 0} 🍖</span>
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
  async function handleCraft(crafterId) {
    if (!confirm(`Craft equipment using this hero? This will cost 500 Gold.`)) return
    setCrafting(true)
    try {
      const res = await craftEquipment(crafterId)
      alert(`Crafted [${res.rarity}] ${res.name}!`)
      loadAll()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      alert(typeof e.message === 'string' ? e.message : JSON.stringify(e.message))
    } finally {
      setCrafting(false)
    }
  }
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card" style={{ marginBottom: '1rem' }}>
            <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.1rem', color: 'var(--text-hi)', marginBottom: '0.5rem' }}>
              Base Hierarchy
            </div>
            <div className="text-dim text-sm" style={{ lineHeight: 1.6 }}>
              Heroes assigned to lower floors receive a share of the floor's Luxury Points (LP). LP increases max HP, Attack, Defense, and Speed, and also provides bonus fatigue recovery per tick!
            </div>
            <div className="text-dim text-sm" style={{ lineHeight: 1.6, marginTop: '0.5rem' }}>
              Max Floor Unlocked: <span className="text-gold">{floorsData?.unlocked || 1}</span> (Clear higher tower floors to unlock more base floors).
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {floorsData?.floors?.map(f => (
              <div key={f.floor_number} className="card" style={{ flex: '1 1 300px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.1rem', color: 'var(--gold)' }}>
                    Floor {f.floor_number}
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div className="text-hi text-sm">{f.total_lp} LP Pool</div>
                    <div className="text-dim" style={{ fontSize: '0.75rem' }}>
                      {f.lp_per_hero} LP/Hero (+{f.stat_bonus_pct}% Stats)
                    </div>
                  </div>
                </div>
                
                {f.heroes.length === 0 ? (
                  <div className="text-dim text-sm">No heroes assigned.</div>
                ) : (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {f.heroes.map(h => (
                      <div key={h.id} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', padding: '0.2rem 0.4rem', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                        <span style={{ fontSize: '0.8rem', fontFamily: 'Cinzel, serif' }}>{h.name}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
                  <div className="text-dim text-sm" style={{ marginBottom: '0.5rem' }}>Assign Hero to Floor:</div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <select id={`assign-hero-${f.floor_number}`} className="input" style={{ flex: 1, padding: '0.2rem' }}>
                      {allHeroes.map(h => {
                         if (h.base_floor === f.floor_number) return null;
                         return <option key={h.id} value={h.id}>{h.name}</option>
                      })}
                    </select>
                    <button 
                      className="btn btn-primary" 
                      disabled={assigning}
                      style={{ padding: '0.2rem 0.5rem' }}
                      onClick={() => {
                        const sel = document.getElementById(`assign-hero-${f.floor_number}`);
                        if (sel && sel.value) {
                          handleAssignFloor(parseInt(sel.value), f.floor_number)
                        }
                      }}>
                      Move
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        </>
      )}
    </div>
  )
}

                        {fac.type === 'Forge' && (
                          <button onClick={() => handleCraft(h.id)} disabled={crafting} style={{ background: 'var(--gold)', color: 'black', border: 'none', borderRadius: 4, padding: '0.2rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer', marginLeft: '0.5rem' }}>
                            Craft (500g)
                          </button>
                        )}