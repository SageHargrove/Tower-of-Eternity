import React, { useState, useEffect } from 'react'
import { getBase, restHeroes, listUpgrades, purchaseUpgrade, listHeroes, getLegacies, runDailyDungeon, getBaseFloors, assignBaseFloor, craftEquipment } from '../api/client'

const BASE_CLASS_BONUSES = {
  'Blacksmith': { label: 'Forge Bonus', desc: 'Improves crafted item rarity', icon: '🔨' },
  'Chef': { label: 'Kitchen Bonus', desc: '+HP recovery when resting', icon: '🍲' },
  'Medic': { label: 'Infirmary Bonus', desc: '+Trauma healing', icon: '🩺' },
  'Quartermaster': { label: 'Supply Bonus', desc: '+Gold from runs', icon: '🎒' },
  'Alchemist': { label: 'Lab Bonus', desc: '+Material drops', icon: '🧪' },
  'Priest': { label: 'Sanctum Bonus', desc: '+Morale recovery', icon: '📿' },
}
    } finally {
      setResting(false)
    }
  }
  const [base, setBase] = useState(null)
  const [resting, setResting] = useState(false)
  const [restMsg, setRestMsg] = useState(null)
  const [facilityMsg, setFacilityMsg] = useState(null)
  const [equipment, setEquipment] = useState(null)
  const [baseHeroes, setBaseHeroes] = useState([])
  const [crafting, setCrafting] = useState(false)
  const [craftMsg, setCraftMsg] = useState(null)

  useEffect(() => {
    loadAll()
  
  // Floors state
  const [activeTab, setActiveTab] = useState('overview')
  const [floorsData, setFloorsData] = useState(null)
  const [assigning, setAssigning] = useState(false)

  useEffect(() => { loadAll() }, [])

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
    try {
      const [baseData, upgradesData, heroesData, inventoryData, equipmentData, floorsRes] = await Promise.all([
        getBase(),
  async function loadAll() {
    try {
      const [baseData, upgradesData, heroesData, inventoryData, equipmentData, floorsRes, facilitiesRes] = await Promise.all([
        getBase(),
        listUpgrades().catch(() => []),
        listHeroes(true).catch(() => []),
        import('../api/client').then(m => m.getInventory ? m.getInventory().catch(()=>[]) : []),
        import('../api/client').then(m => m.listEquipment ? m.listEquipment().catch(()=>null) : null),
        getBaseFloors().catch(() => null),
        getFacilities().catch(() => null)
      ])
      setBase(baseData)
      setFloorsData(floorsRes)
      setFacilitiesData(facilitiesRes)
      setUpgrades(Array.isArray(upgradesData) ? upgradesData : upgradesData?.upgrades || [])
      setInventory(inventoryData)
      setEquipment(equipmentData)
      setAllHeroes(heroesData || [])
            <div style={{ marginTop: '0.5rem' }}>
              <div className="text-dim text-sm" style={{ marginBottom: '0.3rem' }}>Materials:</div>
              {Object.entries(materials).map(([k, v]) => (
                <div key={k} className="text-sm">
                  <span className="text-dim">{k}: </span><span>{v}</span>
                </div>
              ))}
            </div>
          )}
  async function handleRest() {
    setResting(true)
    setRestMsg(null)
    try {
      const result = await restHeroes()
      setRestMsg(`${result.rested} hero${result.rested !== 1 ? 'es' : ''} rested. Morale and stress recovered.`)
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setRestMsg(typeof e.message === 'string' ? e.message : JSON.stringify(e.message))
    } finally {
      setResting(false)
    }
  }

  async function handlePurchase(facilityId) {
    setPurchasing(facilityId)
    setFacilityMsg(null)
    try {
      await purchaseUpgrade(facilityId)
      setFacilityMsg('Upgrade purchased!')
      if (onGoldChange) onGoldChange()
      await loadAll()
    } catch (e) {
      setFacilityMsg(typeof e.message === 'string' ? e.message : JSON.stringify(e.message))
    } finally {
      setPurchasing(null)
    }
  }

  async function handleDailyDungeon(type) {
    } finally {
      setDungeoning(false)
    }
  }
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setRestMsg(typeof e.message === 'string' ? e.message : JSON.stringify(e.message))
    } finally {
      setDungeoning(false)
    }
    } catch (e) {
      setRestMsg(typeof e.message === 'string' ? e.message : JSON.stringify(e.message))
    } finally {
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

  async function handleCraft(slot) {
    if (!confirm(`Craft a new ${slot}? This will cost 500 Gold.`)) return
    setCrafting(true)
    setCraftMsg(null)
  async function handleCraft(slot) {
    if (!confirm(`Craft a new ${slot}? This will cost 500 Gold.`)) return
    setCrafting(true)
    setCraftMsg(null)
    try {
      const res = await craftEquipment(slot)
      setCraftMsg(`Crafted ${res.equipment.name}! (Forged by: ${res.blacksmith_used})`)
      loadAll()
          <button className={`tab-btn ${activeTab === 'floors' ? 'active' : ''}`} onClick={() => setActiveTab('floors')} style={{ background: 'none', border: 'none', padding: '0.5rem 1rem', cursor: 'pointer', color: activeTab === 'floors' ? 'var(--gold)' : 'var(--text-dim)', borderBottom: activeTab === 'floors' ? '2px solid var(--gold)' : '2px solid transparent', fontFamily: 'Cinzel, serif', fontSize: '1.1rem' }}>
            Base Hierarchy
          </button>
        </div>
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

          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.9rem', color: 'var(--text-hi)', marginBottom: '0.75rem' }}>
            Inventory
          </div>
          {!inventory || inventory.length === 0 ? (
            <div className="text-dim text-sm">No items in inventory.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {inventory.map(item => (
                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                  <span>{item.item_name}</span>
                  <span className="text-dim">x{item.quantity}</span>
                </div>
              ))}
            </div>
      {activeTab === 'overview' && (
        <>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)' }}>
        <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')} style={{ background: 'none', border: 'none', padding: '0.5rem 1rem', cursor: 'pointer', color: activeTab === 'overview' ? 'var(--gold)' : 'var(--text-dim)', borderBottom: activeTab === 'overview' ? '2px solid var(--gold)' : '2px solid transparent', fontFamily: 'Cinzel, serif', fontSize: '1.1rem' }}>
          Overview
        </button>
        <button className={`tab-btn ${activeTab === 'facilities' ? 'active' : ''}`} onClick={() => setActiveTab('facilities')} style={{ background: 'none', border: 'none', padding: '0.5rem 1rem', cursor: 'pointer', color: activeTab === 'facilities' ? 'var(--gold)' : 'var(--text-dim)', borderBottom: activeTab === 'facilities' ? '2px solid var(--gold)' : '2px solid transparent', fontFamily: 'Cinzel, serif', fontSize: '1.1rem' }}>
          Facilities
        </button>
        <button className={`tab-btn ${activeTab === 'legacy' ? 'active' : ''}`} onClick={() => setActiveTab('legacy')} style={{ background: 'none', border: 'none', padding: '0.5rem 1rem', cursor: 'pointer', color: activeTab === 'legacy' ? 'var(--gold)' : 'var(--text-dim)', borderBottom: activeTab === 'legacy' ? '2px solid var(--gold)' : '2px solid transparent', fontFamily: 'Cinzel, serif', fontSize: '1.1rem' }}>
          Legacies
        </button>
        <button className={`tab-btn ${activeTab === 'floors' ? 'active' : ''}`} onClick={() => setActiveTab('floors')} style={{ background: 'none', border: 'none', padding: '0.5rem 1rem', cursor: 'pointer', color: activeTab === 'floors' ? 'var(--gold)' : 'var(--text-dim)', borderBottom: activeTab === 'floors' ? '2px solid var(--gold)' : '2px solid transparent', fontFamily: 'Cinzel, serif', fontSize: '1.1rem' }}>
          Base Floors
        </button>
        <button className={`tab-btn ${activeTab === 'forge' ? 'active' : ''}`} onClick={() => setActiveTab('forge')} style={{ background: 'none', border: 'none', padding: '0.5rem 1rem', cursor: 'pointer', color: activeTab === 'forge' ? 'var(--gold)' : 'var(--text-dim)', borderBottom: activeTab === 'forge' ? '2px solid var(--gold)' : '2px solid transparent', fontFamily: 'Cinzel, serif', fontSize: '1.1rem' }}>
          Forge
        </button>
      </div>
          Base Hierarchy
        </button>
      </div>

      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.9rem', color: 'var(--text-hi)', marginBottom: '0.75rem' }}>
            Equipment
          </div>
          {!equipment || (!equipment.equipped?.length && !equipment.unequipped?.length) ? (
            <div className="text-dim text-sm">No equipment found.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <div style={{ marginBottom: '0.25rem' }}>
            <span className="text-dim text-sm">Gold: </span>
            <span className="text-gold" style={{ fontFamily: 'Cinzel, serif' }}>{base.gold.toLocaleString()}</span>
          </div>
          <div style={{ marginBottom: '0.5rem' }}>
            <span className="text-dim text-sm">Supplies: </span>
            <span style={{ fontFamily: 'Cinzel, serif', color: '#c8a030' }}>{base.supplies || 0} 🍖</span>
          </div>
                </div>
              ))}
              {equipment.unequipped?.map(e => (
                <div key={e.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                  <span>{e.name}</span>
                  <span className="text-dim">In Storage</span>
                </div>
              ))}
            </div>
          )}
        </div>
                        <div key={h.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.3rem 0.6rem', borderRadius: 4 }}>
                          <img src={`http://localhost:8000${h.portrait_path}`} alt={h.name} style={{ width: 24, height: 24, borderRadius: '50%' }} />
                          <span style={{ fontSize: '0.85rem' }}>{h.name}</span>
                          <button onClick={() => handleRemoveFacility(h.id)} style={{ background: 'none', border: 'none', color: 'var(--red)', cursor: 'pointer', marginLeft: '0.5rem' }}>&times;</button>
                          {fac.type === 'Forge' && (
                            <button onClick={() => handleCraft(h.id)} disabled={crafting} style={{ background: 'var(--gold)', color: 'black', border: 'none', borderRadius: 4, padding: '0.2rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer', marginLeft: '0.5rem' }}>
                              Craft (500g)
                            </button>
                          )}
                        </div>
            </button>
            <div className="text-dim" style={{ fontSize: '0.7rem', marginTop: '0.3rem' }}>
              Restores HP and Morale. Clears Fatigue.
            </div>
            <span>Facilities</span>
            {facilityMsg && (
              <span className={`text-sm ${facilityMsg.includes('purchased') ? 'text-green' : 'text-red'}`} style={{ whiteSpace: 'pre-wrap' }}>
          <button className="btn btn-gold" onClick={handleRest} disabled={resting}>
            {resting ? 'Resting...' : 'Rest All Heroes'}
          </button>
          {restMsg && (
            <div className={`text-sm ${restMsg.includes('rested') || restMsg.includes('cleared') ? 'text-green' : 'text-red'}`}
                 style={{ marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
              {restMsg}
            </div>
          )}
        </div>
              return (
                <div key={facilityId} className="card" style={{
                  padding: 0,
                  overflow: 'hidden',
                  border: isMaxed ? '1px solid var(--gold)' : '1px solid var(--border)',
                  position: 'relative'
                }}>
                  {/* Facility Image */}
                  <div style={{ position: 'relative', width: '100%', height: '180px' }}>
                    <img 
                      src={`/facilities/${upgrade.name}.png`} 
                      alt={upgrade.name} 
                      style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'cover',
                        filter: isLocked ? 'grayscale(80%) brightness(40%)' : 'brightness(80%)'
                      }}
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    {isLocked && (
                      <div style={{
                        position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        background: 'rgba(0,0,0,0.5)', zIndex: 1
                      }}>
                        <span style={{ fontSize: '3rem' }}>🔒</span>
                        <span style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: '#fff', letterSpacing: '2px', marginTop: '0.5rem' }}>LOCKED</span>
                      </div>
                    )}
                    <div style={{
                      position: 'absolute', bottom: 0, left: 0, width: '100%',
                      background: 'linear-gradient(transparent, rgba(0,0,0,0.9))',
        )}
      </div>
    </div>
  )
}
            })}
          </div>
        </>
      )}
      </div>
      )}

      {activeTab === 'floors' && (
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
                      {baseHeroes.concat(heroesList).map(h => {
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
      )}
    </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <select id={`assign-hero-${f.floor_number}`} className="input" style={{ flex: 1, padding: '0.2rem' }}>
                      {allHeroes.map(h => {
                         if (h.base_floor === f.floor_number) return null;
                         return <option key={h.id} value={h.id}>{h.name}</option>
                      })}
                    </select>
      </div>
        </>
      )}
        </div>
      )}

      {activeTab === 'forge' && (
        <div className="section">
          <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <h2 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', marginBottom: '1rem' }}>The Forge</h2>
            <div className="text-dim" style={{ marginBottom: '2rem', maxWidth: '500px', margin: '0 auto 2rem' }}>
              Craft new equipment to strengthen your heroes. You must have a living Blacksmith in your base to use the Forge.
              The quality of crafted equipment scales with your best Blacksmith's level and aptitude.
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              {['weapon', 'armor', 'accessory'].map(slot => (
                <button
                  key={slot}
                  className="btn"
                  style={{
                    padding: '1rem 2rem',
                    fontSize: '1.2rem',
                    background: 'rgba(201,168,76,0.1)',
                    border: '1px solid var(--gold)',
                    color: 'var(--gold)',
                    fontFamily: 'Cinzel, serif',
                    minWidth: '200px'
                  }}
                  onClick={() => handleCraft(slot)}
                  disabled={crafting}
                >
                  {crafting ? 'Forging...' : `Craft ${slot.charAt(0).toUpperCase() + slot.slice(1)}`}
                  <div style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '0.5rem' }}>Cost: 500 Gold</div>
                </button>
              ))}
            </div>

            {craftMsg && (
              <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', borderRadius: '4px', color: craftMsg.includes('Error') || craftMsg.includes('need') || craftMsg.includes('Not enough') ? 'var(--red)' : 'var(--gold)' }}>
                {craftMsg}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
                        {fac.type === 'Forge' && (
                          <button onClick={() => handleCraft(h.id)} disabled={crafting} style={{ background: 'var(--gold)', color: 'black', border: 'none', borderRadius: 4, padding: '0.2rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer', marginLeft: '0.5rem' }}>
                            Craft (500g)
                          </button>
                        )}