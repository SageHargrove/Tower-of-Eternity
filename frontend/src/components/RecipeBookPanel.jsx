import React, { useState, useEffect } from 'react'
import ItemIcon from './ItemIcon'
import { getForgeRecipes, craftPremadeRecipe } from '../api/client'
import MinigameShell, { AUTO_RESOLVE_MULT } from './minigames/MinigameShell'
import ForgeTiming from './minigames/ForgeTiming'

/*
 * THE FORGE — recipes + the anvil (spec "Forge - Illuminated.dc.html").
 * Left: RECIPES BY FORGE LEVEL, grouped by type, SELECT per row. Right:
 * ON THE ANVIL — the chosen recipe, its materials, the crafter, and
 * STRIKE THE STEEL. Blueprints drop while climbing (~15%/floor); crafts
 * use a specific assigned smith (level/aptitude set the power pool),
 * materials are tier-agnostic (lowest tiers spent first).
 */
export default function RecipeBookPanel({ assignedHeroes, gold, materials, onCrafted }) {
  const [recipes, setRecipes] = useState([])
  const [selectedId, setSelectedId] = useState(null)
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

  // The craft button opens STRIKE THE STEEL (the Forge timing minigame) —
  // skipping auto-resolves at the ADEPT baseline (never a punishment).
  const [minigameRecipe, setMinigameRecipe] = useState(null)

  function handleCraft(recipe) {
    if (!crafterId) { setMsg({ text: 'Assign a hero to the Forge to craft.', err: true }); return }
    setMinigameRecipe(recipe)
  }

  async function doCraft(recipe, qualityMult) {
    setMinigameRecipe(null)
    setBusy(true)
    setMsg(null)
    try {
      const res = await craftPremadeRecipe(parseInt(crafterId), recipe.id, qualityMult)
      if (res.ruined) {
        setMsg({ text: res.message || 'The work is ruined — the materials are gone.', err: true })
        if (onCrafted) onCrafted()
        return
      }
      const q = res.quality && res.quality !== 1 ? ` The strikes ${res.quality > 1 ? 'sang' : 'faltered'} — quality ×${res.quality.toFixed(2)}.` : ''
      setMsg({ text: `${res.equipment.name} forged — ${res.equipment.rarity}-rank base, shaped by the crafter's hand.${q}` })
      if (onCrafted) onCrafted()
    } catch (e) {
      setMsg({ text: e.message, err: true })
    } finally {
      setBusy(false)
    }
  }

  const micro = { fontFamily: "'Cinzel',serif", letterSpacing: '.16em', fontSize: 9 }

  if (!recipes.length) {
    return (
      <div style={{ marginTop: '1rem', border: '1px solid rgba(184,151,98,.3)', background: 'rgba(12,7,24,.45)', padding: '14px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
          <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: 10, color: 'var(--gold)' }}>RECIPES BY FORGE LEVEL</span>
        </div>
        <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 14, marginTop: 8 }}>
          No blueprints discovered yet — they drop while clearing Tower floors.
        </div>
      </div>
    )
  }

  const groups = [['weapon', 'WEAPONS'], ['armor', 'ARMOR'], ['accessory', 'ACCESSORIES']]
  const grouped = groups
    .map(([type, label]) => [label, recipes.filter(r => String(r.type || '').toLowerCase().startsWith(type))])
    .filter(([, list]) => list.length > 0)
  const ungrouped = recipes.filter(r => !groups.some(([t]) => String(r.type || '').toLowerCase().startsWith(t)))
  if (ungrouped.length) grouped.push(['OTHER WORKS', ungrouped])

  const selected = recipes.find(r => r.id === selectedId) || null
  const crafter = (assignedHeroes || []).find(h => String(h.id) === String(crafterId)) || null
  const selMats = (() => { try { return JSON.parse(selected?.materials_json || '{}') } catch { return {} } })()
  const selMissing = Object.entries(selMats).filter(([m, q]) => !haveMaterial(m, q))
  const selPoor = selected && gold != null && gold < selected.gold_cost

  return (
    <div style={{ marginTop: '1rem', display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'stretch' }}>
      {/* ── recipes by forge level ── */}
      <div style={{ flex: '1.3 1 320px', minWidth: 300 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
          <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: 10, color: 'var(--gold)' }}>RECIPES BY FORGE LEVEL</span>
          <span style={{ height: 1, flex: 1, background: 'rgba(184,151,98,.2)' }} />
          <span style={{ ...micro, color: 'var(--muted)' }}>{recipes.length} KNOWN</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 420, overflowY: 'auto', paddingRight: 4 }}>
          {grouped.map(([label, list]) => (
            <div key={label}>
              <div style={{ ...micro, letterSpacing: '.22em', color: 'var(--lavender)', marginBottom: 6 }}>{label}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {list.map(r => {
                  const sel = r.id === selectedId
                  return (
                    <div key={r.id} onClick={() => setSelectedId(sel ? null : r.id)} style={{
                      display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px', cursor: 'pointer',
                      border: sel ? '1px solid rgba(255,216,138,.6)' : '1px solid rgba(184,151,98,.25)',
                      background: sel ? 'linear-gradient(90deg,rgba(184,151,98,.12),rgba(12,7,24,.5))' : 'rgba(12,7,24,.4)',
                    }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 12, letterSpacing: '.06em', color: sel ? 'var(--gold-hi)' : 'var(--text-hi)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {r.name.toUpperCase()}
                        </div>
                        <div style={{ display: 'flex', gap: 8, marginTop: 3, alignItems: 'center', flexWrap: 'wrap' }}>
                          {Object.entries((() => { try { return JSON.parse(r.materials_json || '{}') } catch { return {} } })()).map(([m, q]) => (
                            <span key={m} title={m} style={{ display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 11, color: haveMaterial(m, q) ? 'var(--muted)' : '#d98a8a' }}>
                              <ItemIcon name={m} kind="material" size={13} /> {q}
                            </span>
                          ))}
                          <span style={{ ...micro, fontSize: 8, color: 'var(--gold-hi)' }}>{r.gold_cost}G</span>
                        </div>
                      </div>
                      <span style={{ ...micro, flex: 'none', padding: '4px 12px', color: sel ? '#0a0710' : 'var(--muted)', fontWeight: sel ? 700 : 500, background: sel ? 'linear-gradient(120deg,#ffd88a,#b89762)' : 'none', border: sel ? 'none' : '1px solid rgba(184,151,98,.35)', clipPath: 'polygon(5px 0,100% 0,calc(100% - 5px) 100%,0 100%)' }}>
                        {sel ? 'SELECTED' : 'SELECT'}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── on the anvil ── */}
      <div style={{ position: 'relative', flex: '1 1 280px', minWidth: 270, border: '1px solid rgba(232,163,76,.45)', background: 'linear-gradient(160deg,rgba(60,36,16,.25),rgba(12,7,24,.65))', padding: '16px 18px 70px', clipPath: 'polygon(0 0,100% 0,100% 100%,14px 100%)' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: 12, height: 12, borderLeft: '2px solid #e8a34c', borderTop: '2px solid #e8a34c' }} />
        <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: 10, color: '#e8a34c' }}>ON THE ANVIL</div>
        {selected ? (
          <>
            <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 19, color: 'var(--text-hi)', marginTop: 5 }}>{selected.name.toUpperCase()}</div>
            {selected.description && <div style={{ fontSize: 13.5, fontStyle: 'italic', color: '#c9b8a8', marginTop: 3, lineHeight: 1.4 }}>{selected.description}</div>}
            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                <span style={{ color: '#c9bfa8' }}>Gold cost</span>
                <span style={{ fontFamily: "'Cinzel',serif", fontSize: 12, color: selPoor ? '#d98a8a' : 'var(--gold-hi)' }}>{selected.gold_cost} GOLD</span>
              </div>
              {Object.entries(selMats).map(([m, q]) => (
                <div key={m} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                  <span style={{ color: '#c9bfa8', display: 'inline-flex', alignItems: 'center', gap: 6 }}><ItemIcon name={m} kind="material" size={15} /> {m}</span>
                  <span style={{ fontFamily: "'Cinzel',serif", fontSize: 12, color: haveMaterial(m, q) ? '#a8dfb8' : '#d98a8a' }}>×{q}{haveMaterial(m, q) ? '' : ' · SHORT'}</span>
                </div>
              ))}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 14, marginTop: 4 }}>
                <span style={{ color: '#c9bfa8' }}>Smith</span>
                <select value={crafterId} onChange={e => setCrafterId(e.target.value)}
                  style={{ background: 'rgba(8,6,14,.6)', border: '1px solid rgba(232,163,76,.4)', color: 'var(--text-hi)', padding: '4px 8px', fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.06em' }}>
                  <option value="">CHOOSE…</option>
                  {(assignedHeroes || []).map(h => (
                    <option key={h.id} value={h.id}>{h.name.toUpperCase()} · LV {h.level}</option>
                  ))}
                </select>
              </div>
            </div>
            <div style={{ fontSize: 12.5, fontStyle: 'italic', color: 'var(--muted)', marginTop: 12 }}>
              {crafter
                ? `${crafter.name}'s level and aptitude decide how strong the steel rolls. Any material tier feeds the recipe — lowest spent first.`
                : 'Assign a smith to the Forge — the crafter\'s hand shapes the result.'}
            </div>
            {msg && <div style={{ fontSize: 13, fontStyle: 'italic', color: msg.err ? '#d98a8a' : '#a8dfb8', marginTop: 8 }}>{msg.text}</div>}
            <button disabled={busy || !crafterId || selMissing.length > 0 || selPoor}
              onClick={() => handleCraft(selected)}
              title={selMissing.length ? `Missing: ${selMissing.map(([m]) => m).join(', ')}` : ''}
              style={{ position: 'absolute', left: 18, right: 18, bottom: 16, textAlign: 'center', cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 12, color: '#0a0710', background: 'linear-gradient(120deg,#ffd88a,#e8a34c)', border: 'none', padding: '10px 0', clipPath: 'polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)', boxShadow: '0 8px 24px rgba(232,163,76,.35)', opacity: busy || !crafterId || selMissing.length > 0 || selPoor ? 0.5 : 1 }}>
              {busy ? 'THE HAMMER FALLS…' : selMissing.length ? 'MISSING MATERIALS' : selPoor ? `NEED ${selected.gold_cost} GOLD` : 'STRIKE THE STEEL'}
            </button>
          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, padding: '40px 10px', textAlign: 'center' }}>
            <span style={{ width: 26, height: 26, transform: 'rotate(45deg)', border: '1px dashed rgba(232,163,76,.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ transform: 'rotate(-45deg)', color: '#e8a34c', fontFamily: "'Cinzel',serif", fontSize: 11 }}>⚒</span>
            </span>
            <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 14, lineHeight: 1.5 }}>
              The anvil stands cold.<br />Select a recipe to lay steel upon it.
            </div>
            {msg && <div style={{ fontSize: 13, fontStyle: 'italic', color: msg.err ? '#d98a8a' : '#a8dfb8' }}>{msg.text}</div>}
          </div>
        )}
      </div>

      {/* STRIKE THE STEEL — forge timing minigame (skip = ADEPT baseline) */}
      {minigameRecipe && (
        <MinigameShell
          title="STRIKE THE STEEL"
          flavor={`${minigameRecipe.name} waits on the anvil. Take the hammer yourself, or trust the smith's steady hands.`}
          onSkip={() => doCraft(minigameRecipe, AUTO_RESOLVE_MULT)}
          onResolve={(mult) => doCraft(minigameRecipe, mult)}
          game={(difficulty, onDone) => <ForgeTiming difficulty={difficulty} onDone={onDone} />}
        />
      )}
    </div>
  )
}
