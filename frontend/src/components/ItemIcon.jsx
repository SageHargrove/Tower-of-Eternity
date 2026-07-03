import React, { useState, useEffect } from 'react'

// Icon for a named item (material / consumable / currency). Resolves the
// generated 1:1 art in /icons by slugifying the name — "Iron Ore (C)" ->
// iron_ore.png — with per-name overrides for items whose art file isn't a
// straight slug, then a per-kind generic, then nothing.
// Naming convention for new art: lowercase_with_underscores.png in
// frontend/public/icons/ and it just shows up.

const NAME_OVERRIDES = {
  // potions (alchemist_service POTION_CATALOG)
  'Minor Healing Draught': 'low_health_potion',
  'Greater Healing Draught': 'high_health_potion',
  'Vitality Elixir': 'high_health_potion',
  'Calming Tonic': 'potion',
  'Panacea': 'alchemy_flask',
  'Mana Draught': 'low_mana_potion',
  'Greater Mana Draught': 'high_mana_potion',
  // food (cooking_service FOOD_CATALOG)
  "Traveler's Rations": 'travelers_rations',
  "Hero's Feast": 'hero_feast',
  // market shop bundles
  'Ingredient Basket': 'mystic_wheat',
  'Ingredient Cart': 'mystic_wheat',
  'Bandage Bundle': 'bandage',
  'Raw Material Crate': 'monster_bone',
  // materials whose art has a different name
  'Tattered Cloth': 'worn_leather',
  'Refined Iron': 'iron_ore',
  'Steel': 'iron_ore',
  'Copper': 'iron_ore',
  'Leather': 'worn_leather',
  'Spirit Dust': 'mystic_dust',
  'Imp Horn': 'buff_horn',
}

const KIND_FALLBACK = {
  material: 'monster_bone',
  potion: 'potion',
  food: 'rations',
  scroll: 'scroll',
}

function slugify(name) {
  // strip material tier suffix "(C)" then snake_case
  return name
    .replace(/\s*\([A-Z][+-]?\)\s*$/, '')
    .trim()
    .toLowerCase()
    .replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

export default function ItemIcon({ name, kind = 'material', size = 40, style }) {
  const base = name.replace(/\s*\([A-Z][+-]?\)\s*$/, '').trim()
  const candidates = []
  if (NAME_OVERRIDES[base]) candidates.push(NAME_OVERRIDES[base])
  candidates.push(slugify(name))
  if (KIND_FALLBACK[kind]) candidates.push(KIND_FALLBACK[kind])

  const [idx, setIdx] = useState(0)
  useEffect(() => { setIdx(0) }, [name])
  if (idx >= candidates.length) return null
  return (
    <img
      src={`/icons/${candidates[idx]}.png`}
      alt={name}
      width={size}
      height={size}
      style={{ objectFit: 'contain', imageRendering: 'auto', ...style }}
      onError={() => setIdx(i => i + 1)}
      draggable={false}
    />
  )
}
