import React from 'react'

// Inline panel for a facility's BASE-UPGRADE track (the base_upgrades
// table — a separate, gold-bought progression from the facility's own
// level). Rendered inside the matching facility card: Infirmary and Forge
// each have one. Effects live server-side: Infirmary levels boost
// rest_at_base_recovery; Forge levels add +10 craft quality each
// (see forge_craft in routers/base.py).
const EFFECT_COPY = {
  infirmary: (lvl) => lvl > 0
    ? `Rest & Recovery currently enhanced (Tier ${lvl}) — better morale/stress/trauma recovery every time the roster rests.`
    : 'Enhances Rest & Recovery — each tier improves how much morale/stress/trauma every rest restores.',
  forge: (lvl) => lvl > 0
    ? `Crafting quality +${lvl * 10} (Tier ${lvl}) — applied on top of your best Blacksmith's skill for every craft.`
    : 'Each tier adds +10 flat crafting quality to everything forged here, on top of your smiths.',
}

export default function UpgradeTreePanel({ upgrade, gold, onBuy, busy }) {
  if (!upgrade) return null
  const level = upgrade.level || 0
  const maxLevel = upgrade.max_level || 5
  const maxed = level >= maxLevel
  const copy = EFFECT_COPY[upgrade.id]

  return (
    <div style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <div style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif' }}>
            ✦ {upgrade.name} Enhancement
            <span style={{ marginLeft: '0.6rem', letterSpacing: '2px', fontSize: '0.95rem' }}>
              {Array.from({ length: maxLevel }).map((_, i) => (
                <span key={i} style={{ color: i < level ? 'var(--gold)' : 'rgba(255,255,255,0.15)' }}>◆</span>
              ))}
            </span>
          </div>
          <div className="text-dim text-sm" style={{ marginTop: '0.25rem', maxWidth: 520 }}>
            {copy ? copy(level) : upgrade.description}
          </div>
        </div>
        {maxed ? (
          <span style={{ color: 'var(--gold)', fontFamily: 'Cinzel, serif', fontSize: '0.9rem' }}>MAX</span>
        ) : (
          <button
            className="btn btn-gold"
            disabled={busy || (gold != null && gold < upgrade.next_cost)}
            onClick={() => onBuy(upgrade.id)}
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
          >
            Enhance to Tier {level + 1} ({upgrade.next_cost?.toLocaleString()}g)
          </button>
        )}
      </div>
    </div>
  )
}
