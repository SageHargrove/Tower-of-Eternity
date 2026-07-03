import React, { useState, useEffect } from 'react'
import ItemIcon from './ItemIcon'
import { getForgeRecipes, craftPremadeRecipe } from '../api/client'

// The Forge's Recipe Book — blueprint recipes discovered while climbing
// (the "📜 Found a new Blueprint!" drops, ~15% per cleared floor) plus the
// seeded basics. This UI didn't exist before: blueprints dropped but could
// never be crafted. Crafts use a specific assigned smith as the crafter
// (their level/aptitude sets the power pool, scaled by the recipe's
// base_stat_mult), materials are tier-agnostic (any tier of Iron Ore
// satisfies "Iron Ore", lowest tiers spent first).
export default function RecipeBookPanel({ assignedHeroes, gold, materials, onCrafted }) {
  const [recipes, setRecipes] = useState([])
  const [crafterId, setCrafterId] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)

  useEffect(() => {
    getForgeRecipes().then(r => setRecipes(Array.isArray(r) ? r : [])).catch(() => {})
  }, [])

  useEffect(() => {
    // default the crafter to the first assigned smith
    if (!crafterId && assignedHeroes?.length) setCrafterId(String(assignedHeroes[0].id))
  }, [assignedHeroes])

  function haveMaterial(baseName, need) {
    // tier-agnostic tally, mirrors materials_service.get_material_total
    let total = 0
    for (const [name, qty] of Object.entries(materials || {})) {
      const stripped = name.replace(/\s*\([A-Z][+-]?\)\s*$/, '')
      if (stripped === baseName) total += qty
    }
    return total >= need
  }

  async function handleCraft(recipe) {
    if (!crafterId) { setMsg({ text: 'Assign a hero to the Forge to craft.', err: true }); return }
    setBusy(true)
    setMsg(null)
    try {
      const res = await craftPremadeRecipe(parseInt(crafterId), recipe.id)
      setMsg({ text: `${res.equipment.name} forged! (${res.equipment.rarity}-rank base — the crafter's skill shaped its stats)` })
      if (onCrafted) onCrafted()
    } catch (e) {
      setMsg({ text: e.message, err: true })
    } finally {
      setBusy(false)
    }
  }

  if (!recipes.length) {
    return (
      <div style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: 6 }}>
        <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif', marginBottom: '0.3rem' }}>📜 Recipe Book</div>
        <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>
          No blueprints discovered yet — they drop while clearing Tower floors.
        </div>
      </div>
    )
  }

  return (
    <div style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif' }}>📜 Recipe Book ({recipes.length})</div>
        <select className="input" value={crafterId} onChange={e => setCrafterId(e.target.value)} style={{ fontSize: '0.8rem', padding: '0.25rem' }}>
          <option value="">Crafter…</option>
          {(assignedHeroes || []).map(h => (
            <option key={h.id} value={h.id}>{h.name} (Lv.{h.level})</option>
          ))}
        </select>
      </div>
      <div className="text-dim text-sm" style={{ marginBottom: '0.5rem' }}>
        Blueprints found in the Tower. Any material tier satisfies a recipe (lowest spent first); the crafter's level and aptitude decide how strong the result rolls.
      </div>
      {msg && <div style={{ color: msg.err ? '#f87' : '#8e8', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{msg.text}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))', gap: '0.5rem' }}>
        {recipes.map(r => {
          let mats = {}
          try { mats = JSON.parse(r.materials_json || '{}') } catch {}
          const missing = Object.entries(mats).filter(([m, q]) => !haveMaterial(m, q))
          const poor = gold != null && gold < r.gold_cost
          return (
            <div key={r.id} className="card" style={{ padding: '0.6rem' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--text-hi)' }}>
                {r.name} <span className="text-dim" style={{ fontSize: '0.7rem', textTransform: 'capitalize' }}>· {r.type}</span>
              </div>
              {r.description && <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: '0.2rem 0' }}>{r.description}</div>}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', margin: '0.4rem 0' }}>
                {Object.entries(mats).map(([m, q]) => (
                  <span key={m} title={m} style={{
                    display: 'inline-flex', alignItems: 'center', gap: '0.2rem',
                    fontSize: '0.72rem', padding: '0.1rem 0.35rem', borderRadius: 4,
                    background: 'rgba(255,255,255,0.05)',
                    color: haveMaterial(m, q) ? 'var(--text-hi)' : '#f87',
                    border: `1px solid ${haveMaterial(m, q) ? 'var(--border)' : 'rgba(255,120,120,0.4)'}`,
                  }}>
                    <ItemIcon name={m} kind="material" size={16} /> {q}
                  </span>
                ))}
              </div>
              <button
                className="btn btn-gold"
                disabled={busy || !crafterId || missing.length > 0 || poor}
                onClick={() => handleCraft(r)}
                style={{ width: '100%', fontSize: '0.75rem', padding: '0.25rem' }}
                title={missing.length ? `Missing: ${missing.map(([m]) => m).join(', ')}` : ''}
              >
                {missing.length ? 'Missing materials' : poor ? `Need ${r.gold_cost}g` : `Craft (${r.gold_cost}g)`}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
