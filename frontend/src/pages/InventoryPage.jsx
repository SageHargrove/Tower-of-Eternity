import React, { useState, useEffect } from 'react'
import { getInventory, listEquipment, getFacilities } from '../api/client'

export default function InventoryPage() {
  const [loading, setLoading] = useState(true)
  const [inventory, setInventory] = useState(null)
  const [equipment, setEquipment] = useState({ equipped: [], unequipped: [] })
  const [selectedItem, setSelectedItem] = useState(null)

  const [vaultCapacity, setVaultCapacity] = useState(20)

  useEffect(() => { refresh() }, [])

  async function refresh() {
    setLoading(true)
    try {
      const [inv, eq, facs] = await Promise.all([
        getInventory(),
        listEquipment(),
        getFacilities().catch(() => null)
      ])
      setInventory(inv || [])
      setEquipment(eq || { equipped: [], unequipped: [] })
      
      let capacity = 20
      if (facs && facs.built) {
        const vault = facs.built.find(f => f.type === 'Vault')
        if (vault) {
          capacity = 20 + (vault.slots_unlocked * 16) // Scales: 36, 52, 68, 84, 100
        }
      }
      setVaultCapacity(capacity)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  // Combine items for grid display
  const allItems = []
  if (Array.isArray(inventory)) {
    inventory.forEach(mat => allItems.push({ ...mat, typeId: 'mat_' + mat.item_name, itemType: 'material' }))
  }
  if (equipment.unequipped) {
    equipment.unequipped.forEach(eq => allItems.push({ ...eq, typeId: 'eq_' + eq.id, itemType: 'equipment', isEquipped: false }))
  }
  if (equipment.equipped) {
    equipment.equipped.forEach(eq => allItems.push({ ...eq, typeId: 'eq_' + eq.id, itemType: 'equipment', isEquipped: true }))
  }

  // Select first item by default if none selected
  useEffect(() => {
    if (!loading && !selectedItem && allItems.length > 0) {
      setSelectedItem(allItems[0])
    }
  }, [loading, allItems.length, selectedItem])

  if (loading) return <div className="page text-dim">Loading Vault...</div>

  // Pad the grid based on Vault capacity
  const minSlots = vaultCapacity
  const slots = [...allItems]
  while (slots.length < minSlots) {
    slots.push(null)
  }

  return (
    <div className="page" style={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      <div className="section-header" style={{ marginBottom: '1.5rem', fontFamily: 'Cinzel, serif', fontSize: '2rem', textShadow: '0 0 10px rgba(255,255,255,0.2)' }}>Vault</div>
      
      <div style={{ display: 'flex', gap: '2rem', flex: 1, minHeight: 0 }}>
        
        {/* Left Side: The Grid */}
        <div className="card" style={{ flex: 2, display: 'flex', flexDirection: 'column', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border)', padding: '1.5rem', overflowY: 'auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(64px, 1fr))', gap: '8px', alignContent: 'start' }}>
            {slots.map((item, index) => {
              const isSelected = item && selectedItem && item.typeId === selectedItem.typeId;
              const isEmpty = !item;
              let bgColor = 'rgba(255,255,255,0.02)'
              let borderColor = 'var(--border)'
              let content = null

              if (item) {
                if (item.itemType === 'material') {
                  borderColor = 'var(--border-hi)'
                  content = <span style={{ fontSize: '1.5rem' }}>📦</span>
                } else if (item.itemType === 'equipment') {
                  borderColor = `var(--star${item.rarity})`
                  bgColor = `rgba(255,255,255,0.05)`
                  content = <span style={{ fontSize: '1.5rem', filter: `drop-shadow(0 0 4px var(--star${item.rarity}))` }}>{item.slot === 'weapon' ? '⚔️' : '🛡️'}</span>
                }
              }

              return (
                <div 
                  key={index}
                  onClick={() => item && setSelectedItem(item)}
                  style={{ 
                    aspectRatio: '1/1', 
                    background: bgColor, 
                    border: `2px solid ${isSelected ? 'var(--gold)' : borderColor}`,
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    cursor: isEmpty ? 'default' : 'pointer',
                    boxShadow: isSelected ? '0 0 10px var(--gold)' : (item ? `inset 0 0 15px ${borderColor}20` : 'none'),
                    transition: 'all 0.1s ease',
                    opacity: isEmpty ? 0.3 : 1
                  }}
                  onMouseEnter={(e) => { if (item) e.currentTarget.style.transform = 'scale(1.05)'; }}
                  onMouseLeave={(e) => { if (item) e.currentTarget.style.transform = 'scale(1)'; }}
                >
                  {content}
                  
                  {/* Quantity Badge */}
                  {item && item.itemType === 'material' && (
                    <div style={{ position: 'absolute', bottom: -2, right: -2, background: 'var(--bg)', border: '1px solid var(--border-hi)', fontSize: '0.7rem', padding: '0 4px', borderRadius: 4, fontFamily: 'monospace', fontWeight: 'bold' }}>
                      {item.quantity}
                    </div>
                  )}

                  {/* Equipped Indicator */}
                  {item && item.isEquipped && (
                    <div style={{ position: 'absolute', top: -4, left: -4, fontSize: '1rem', filter: 'drop-shadow(0 0 2px black)' }}>
                      E
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Right Side: Details Panel */}
        <div className="card" style={{ flex: 1, minWidth: '300px', display: 'flex', flexDirection: 'column', padding: '2rem', background: 'rgba(0,0,0,0.6)', border: '1px solid var(--gold-dim)' }}>
          {!selectedItem ? (
            <div className="text-dim" style={{ margin: 'auto', textAlign: 'center', fontStyle: 'italic', fontSize: '1.1rem' }}>
              Select an item to view details.
            </div>
          ) : (
            <>
              {selectedItem.itemType === 'material' && (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <div style={{ fontSize: '4rem', textAlign: 'center', marginBottom: '1rem', filter: 'drop-shadow(0 0 20px rgba(255,255,255,0.2))' }}>📦</div>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', textAlign: 'center', color: 'var(--text-hi)', textTransform: 'capitalize', borderBottom: '1px solid var(--border)', paddingBottom: '1rem', marginBottom: '1rem' }}>
                    {selectedItem.item_name.replace('_', ' ')}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div className="text-dim" style={{ fontSize: '1.1rem', marginBottom: '1.5rem', textAlign: 'center', lineHeight: '1.5' }}>
                      A fundamental material used in the Hollow Spire.<br/>Can be used for crafting and base upgrades.
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="text-dim" style={{ fontSize: '1.2rem', textTransform: 'uppercase', letterSpacing: '2px' }}>Amount Owned</span>
                      <span className="text-gold" style={{ fontSize: '1.8rem', fontFamily: 'Cinzel, serif', fontWeight: 'bold' }}>{selectedItem.quantity}</span>
                    </div>
                  </div>
                </div>
              )}

              {selectedItem.itemType === 'equipment' && (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <div style={{ fontSize: '4rem', textAlign: 'center', marginBottom: '1rem', filter: `drop-shadow(0 0 20px var(--star${selectedItem.rarity}))` }}>
                    {selectedItem.slot === 'weapon' ? '⚔️' : '🛡️'}
                  </div>
                  
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', textAlign: 'center', color: `var(--star${selectedItem.rarity})`, borderBottom: `1px solid var(--star${selectedItem.rarity})`, paddingBottom: '0.5rem', marginBottom: '0.2rem', textShadow: `0 0 10px var(--star${selectedItem.rarity})` }}>
                    {selectedItem.name}
                  </div>
                  <div style={{ textAlign: 'center', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '3px', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                    {selectedItem.rarity}★ {selectedItem.type}
                  </div>

                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                    {selectedItem.base_atk > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(201,168,76,0.1)', padding: '0.8rem 1rem', borderRadius: 4 }}><span className="text-dim">Attack</span><span className="text-gold" style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem' }}>+{selectedItem.base_atk}</span></div>}
                    {selectedItem.base_def > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(201,168,76,0.1)', padding: '0.8rem 1rem', borderRadius: 4 }}><span className="text-dim">Defense</span><span className="text-gold" style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem' }}>+{selectedItem.base_def}</span></div>}
                    {selectedItem.base_hp > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(201,168,76,0.1)', padding: '0.8rem 1rem', borderRadius: 4 }}><span className="text-dim">Max HP</span><span className="text-gold" style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem' }}>+{selectedItem.base_hp}</span></div>}
                    {selectedItem.base_spd > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(201,168,76,0.1)', padding: '0.8rem 1rem', borderRadius: 4 }}><span className="text-dim">Speed</span><span className="text-gold" style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem' }}>+{selectedItem.base_spd}</span></div>}
                  </div>

                  <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                    {selectedItem.isEquipped ? (
                      <div style={{ textAlign: 'center', color: 'var(--green)', padding: '1rem', background: 'rgba(74,154,106,0.1)', borderRadius: 4 }}>
                        Equipped to Hero #{selectedItem.equipped_to}
                      </div>
                    ) : (
                      <div className="text-dim text-center" style={{ fontSize: '0.9rem', fontStyle: 'italic' }}>
                        Can be equipped from the Heroes menu.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
