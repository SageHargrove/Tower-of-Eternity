/*
 * Tip — the app-wide Illuminated tooltip.
 *
 * Usage: <Tip text="What this thing does."><span>STR</span></Tip>
 * Wraps any child; on hover/focus shows a styled tooltip. Uses fixed
 * positioning measured from the trigger so it never clips inside
 * overflow-hidden panels (the app hides scrollbars everywhere, so clipped
 * tooltips would simply vanish). Pure CSS-in-JS, no portal dependency.
 */
import React, { useState, useRef } from 'react'

export default function Tip({ text, children, width = 260, style }) {
  const [pos, setPos] = useState(null)
  const ref = useRef(null)

  function show() {
    const r = ref.current?.getBoundingClientRect()
    if (!r) return
    // Above the trigger, clamped to the viewport horizontally.
    const x = Math.max(10, Math.min(window.innerWidth - width - 10, r.left + r.width / 2 - width / 2))
    setPos({ x, y: r.top - 8 })
  }

  if (!text) return children
  return (
    <span ref={ref} onMouseEnter={show} onMouseLeave={() => setPos(null)}
      onFocus={show} onBlur={() => setPos(null)} tabIndex={-1}
      style={{ cursor: 'help', ...style }}>
      {children}
      {pos && (
        <span style={{
          position: 'fixed', left: pos.x, top: pos.y, transform: 'translateY(-100%)',
          width, zIndex: 4000, pointerEvents: 'none',
          background: 'linear-gradient(160deg, #1a1029, #0c0716)',
          border: '1px solid rgba(184,151,98,.5)',
          clipPath: 'polygon(0 0, 100% 0, 100% 100%, 8px 100%)',
          boxShadow: '0 12px 40px rgba(0,0,0,.7)',
          padding: '9px 12px', display: 'block',
          fontFamily: "'Cormorant Garamond', serif", fontStyle: 'italic',
          fontSize: 13.5, lineHeight: 1.45, color: '#d8cbb0',
          letterSpacing: 0, whiteSpace: 'normal', textTransform: 'none',
        }}>
          {text}
        </span>
      )}
    </span>
  )
}

// Shared copy for concepts that appear on multiple screens — ONE source of
// truth so the same stat never gets two different explanations.
export const TIPS = {
  // six core stats
  strength: 'STRENGTH — physical damage. The power stat for melee classes; drives basic attacks and most weapon skills.',
  intelligence: 'INTELLIGENCE — magical damage and max mana. The power stat for casters.',
  agility: 'AGILITY — turn order (who strikes first each round) and a source of dodge.',
  endurance: 'ENDURANCE — the real mitigation stat: reduces damage taken and feeds max health.',
  willpower: 'WILLPOWER — mental fortitude: resists fear and panic, feeds mana and magic resistance.',
  luck: 'LUCK — crit chance, loot quality, and a hundred small mercies. Team-averaged for drops.',
  // vitals
  health: 'HEALTH — reaches zero and the hero DIES. Death is permanent. Heals between floors from rest, regen, and the Infirmary.',
  mana: 'MANA — fuels active skills in combat. Starts fights at half; regenerates each round.',
  morale: 'MORALE — fighting spirit. High morale steadies heroes; low morale invites panic, poor performance, and worse.',
  stress: 'STRESS — accumulates from fights, fear, and overwork. High stress breeds panic and breakdowns. The Tavern takes the edge off.',
  trauma: 'TRAUMA — lasting psychic wounds from deaths witnessed and horrors endured. Heals slowly; the Infirmary hastens it.',
  fatigue: 'FATIGUE — physical exhaustion from climbing and training. Rest clears it.',
  loyalty: 'LOYALTY (affinity) — how devoted this hero is to your company. Raised by gifts, the Shrine, and shared victories.',
  // currencies
  gold: 'GOLD — the company\'s coin: upgrades, crafting, rest, rituals. Earned from every floor, the Market, and stationed specialists.',
  gems: 'GEMS — the rare currency. Spent on summons.',
  aether: 'AETHER — refined mana, fuel for battleship expeditions and raids. Condensed slowly at the Skydock or refined at the Lab.',
  ingredients: 'INGREDIENTS — grown at the Farm; cooked into consumables at the Dining Hall or brewed into potions at the Lab.',
  // systems
  star: 'STAR — a hero\'s innate grade (1-7★). Sets level cap, skill slots, and how strongly their support boons scale. Promote to raise it.',
  mastery: 'MASTERY — a support\'s facility power: star + evolution stage. A grinded, fully-evolved 3★ can out-serve a raw 7★.',
  deeds: 'DEEDS — permanent records of what a hero has actually done. They survive death; the Memorial keeps them.',
  evolution_gate: 'At levels 30 and 60 a hero must CHOOSE an evolution path before they can grow further — XP banks until the choice is made.',
  // aptitudes (hidden until revealed by levels or the Mirror of Fate)
  apt_combat: 'COMBAT aptitude — instinct for the kill. Feeds crit and weapon skill growth.',
  apt_tactical: 'TACTICAL aptitude — reading the field. Feeds crafting quality and battle decision-making.',
  apt_survival: 'SURVIVAL aptitude — refusing to die. Feeds dodge, endurance growth, and expedition safety.',
  apt_mental: 'MENTAL aptitude — force of mind. Feeds mana, research speed, and resisting the Tower\'s horrors.',
  apt_leadership: 'LEADERSHIP aptitude — others follow. Feeds Leader steadying, mentorship, and how sharply they play at the Commander\'s Table.',
  apt_magic: 'MAGIC aptitude — the arcane current. Feeds spell power and enchanted-gear affinity.',
  // summoning
  pity: 'PITY — every summon without a high-star hero builds hidden momentum; a guaranteed high pull lands before the counter maxes.',
  spark: 'SPARKS — every summon earns one. Bank enough and EXCHANGE them for a guaranteed 5★ (heroes) or A-tier (equipment) of your choosing.',
}
