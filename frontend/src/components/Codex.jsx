/*
 * THE CODEX — the game's in-world encyclopedia, DISCOVERY-BASED:
 * an entry stays a "???" silhouette until the player first encounters the
 * thing it describes (see codexBus.unlockCodex / scanCombatForDiscoveries).
 * Basics every recruit would know start unlocked; systems earned by playing
 * unlock as they're met. Click an entry to read its full page.
 */
import React, { useState } from 'react'
import { getUnlocked } from '../codexBus'

const CATS = ['THE TOWER', 'HEROES & CLASSES', 'COMBAT', 'MIND & MORALE', 'DEATH & LEGACY', 'THE BASE']

// id: null = common knowledge (available from the start).
// id-keyed entries unlock via codexBus when first encountered in play.
const ENTRIES = {
  'THE TOWER': [
    { id: null, t: 'THE CLIMB', d: 'One floor at a time, and no way back', body: 'The Tower reveals a floor only to those who walk it. Every floor is what it is — its type, its dangers, its inhabitants are fixed truths you LEARN, not rolls you reroll. What you discover on a floor is remembered between attempts. Deaths beyond the threshold are permanent. Records say no company has ever passed the hundredth floor.' },
    { id: 'floor_conditions', t: 'FLOOR CONDITIONS', d: 'Some floors fight differently', body: 'Certain floors carry a lingering state — blessed ground that mends the party, bloodhaze that sharpens every blade, null fields that drink mana, dark that ruins precision. A floor\'s condition never changes: learn it, and bring the team that answers it. Past the sixtieth floor, conditions turn SEVERE.' },
    { id: 'elites', t: 'ELITE AFFIXES', d: 'Some monsters are more', body: 'A floor may harbor an Elite — Armored, Frenzied, Colossal, Deadly, Regenerating, or Warded. An elite is the same beast grown wrong: harder, faster, hungrier. Which floor hides which elite is a fixed truth. Deep past the eightieth floor, elites have been seen carrying TWO afflictions at once.' },
    { id: 'walls', t: 'THE WALLS', d: 'Floors 50, 70, 90', body: 'Three floors have broken more companies than all the rest together. Their wardens are padded beyond reason, and when wounded near death they rise a THIRD time. The community of climbers names them simply: the Walls. Plan for a siege, not a fight.' },
    { id: 'survival', t: 'THE SURVIVAL SWARM', d: 'Outlast the clock', body: 'Some miniboss floors do not send a champion — they send everything. The swarm cannot realistically be slain; the objective is to STAND when the horn finally sounds. Barriers, healing, and nerve win these floors. Damage merely entertains the Tower.' },
  ],
  'HEROES & CLASSES': [
    { id: null, t: 'STARS', d: 'Innate grade, 1-7★', body: 'A hero\'s star is their innate grade: it sets their level cap, their skill slots, and how brightly their support talents burn. Stars can be raised by Promotion — and each ascension returns a sealed passage of their Chronicle.' },
    { id: 'crossroads', t: 'THE CROSSROADS', d: 'Levels 30 and 60 demand a choice', body: 'At level 30, and again at 60, a hero stands at a crossroads: their class offers paths, and they will NOT grow further until one is chosen. Experience banks in the meantime — the moment the choice is made, the dam breaks and every held level floods in at once. Choose for the company, not just the hero: a support\'s branch decides what their facility does.' },
    { id: 'boons', t: 'COMPANY BOONS', d: 'Supports fight from home', body: 'A support hero assigned to their own facility projects power onto every climb: feasts, field surgery, opening gambits, war chests. The boon is decided by their evolution BRANCH; its strength by their MASTERY — star plus evolution. A grinded, fully-evolved 3★ can out-serve a raw 7★. They cannot climb and keep the home fires at once.' },
    { id: null, t: 'APTITUDES & TALENT', d: 'The hidden numbers', body: 'Five hidden aptitudes shape a hero beneath their stats. Levels reveal them slowly; the Mirror of Fate sells the truth faster. Their average is TALENT — it gates skill slots, steadies panic, and quickens learning. True prodigies exceed every reference.' },
  ],
  'COMBAT': [
    { id: null, t: 'TURN ORDER', d: 'Agility decides who moves', body: 'Each round, every combatant acts in agility order (with a little chaos). Ambushes steal the first round entirely — unless a Strategist\'s plan steals it back.' },
    { id: null, t: 'STATUS EFFECTS', d: 'Bleed, burn, poison, and worse', body: 'Bleed and burn tick a fraction of max health; poison stacks, each dose on its own clock. Stun and freeze steal turns. Burn halves all healing received. Damage-over-time ignores armor — the old convention holds. Shields blunt incoming blows for a few rounds; regen mends between them.' },
    { id: 'boss_phases', t: 'BOSS PHASES', d: 'Wounded bosses change', body: 'Every true boss fights in acts. Push one to two-thirds, then one-third of its health, and it CHANGES — calling reinforcements, calcifying armor, completing rituals, shedding its own plate for speed, or unleashing a cataclysm on the whole party. Each boss\'s phases are fixed: dying to one teaches you exactly what it will do next time.' },
    { id: 'death_saves', t: 'CHEATING DEATH', d: 'Undying Will and foresight', body: 'A blessed few refuse the killing blow — dropping to a single point of health instead, once per charge. Shrine Oracles grant this to the whole climb at the heights of mastery; a Prophet may even foresee the blow entirely, and the hero simply is not there when it lands.' },
    { id: null, t: 'PANIC & FEAR', d: 'Minds break before bodies', body: 'Outmatched fights, dying friends, and horrors press on a hero\'s willpower. The shaken freeze, flee the line, or swing wild. High morale, veteran nerve, and a steady Leader hold the line together.' },
  ],
  'MIND & MORALE': [
    { id: null, t: 'MORALE', d: 'Fighting spirit', body: 'High morale steadies a hero in the worst moments. It rises with victories, feasts, and kept promises; it collapses when comrades die in front of them.' },
    { id: null, t: 'STRESS & TRAUMA', d: 'The Tower\'s real toll', body: 'Stress accrues from every fight and breeds panic; the Tavern takes the edge off. Trauma is deeper — psychic scarring from witnessed deaths — and only time and the Infirmary mend it.' },
    { id: null, t: 'LOYALTY', d: 'Whether they stay', body: 'Loyalty deepens with gifts, shrine devotions, and shared survival. It decides more than mood — a captured hero\'s loyalty decides whose banner they follow.' },
  ],
  'DEATH & LEGACY': [
    { id: 'death', t: 'DEATH IS PERMANENT', d: 'No resurrection. None.', body: 'A hero who dies in the Tower is gone. Their gear returns; their body does not. What remains is what they DID — and the Memorial keeps it. Weigh every floor against the roster you cannot replace.' },
    { id: 'deeds', t: 'DEEDS', d: 'What they did, remembered', body: 'The company records deeds at the moments that matter — bosses felled, cataclysms weathered, death refused, lines held. A hero\'s deeds outlive them: the Memorial reads them back for as long as your company stands.' },
    { id: null, t: 'THE MEMORIAL & SACRIFICE', d: 'Bonds upon the living', body: 'Every qualifying death is enshrined with a title and score. Only the SACRIFICED — heroes given willingly — lend bonds of strength to the living. The rest are simply remembered.' },
  ],
  'THE BASE': [
    { id: null, t: 'FACILITIES', d: 'The company between climbs', body: 'The base feeds, heals, trains, arms, and consoles the roster. Every facility is capped by the Wall\'s level — raise the bulwark first. Assign the right specialist and the facility becomes something more.' },
    { id: 'boons', t: 'MASTERY & BRANCHES', d: 'Star + evolution = power', body: 'A stationed support\'s output scales with MASTERY (star plus evolution stage, to a ceiling of nine) — and their evolution BRANCH picks the mechanic itself. A Butcher feeds war rations; a Sous Chef lays a feast. The facility\'s boon banner tells you what its specialist is providing.' },
    { id: 'bestiary', t: 'THE BESTIARY', d: 'The pen of taken things', body: 'Beasts subdued in the Tower can be dragged home. Kept beasts add their menace to the base\'s defenses; a Scout of the hunting path swells both the odds of a capture and the size of the catch — the greatest ever taken were Alphas.' },
  ],
}

export default function Codex({ onClose }) {
  const [cat, setCat] = useState('THE TOWER')
  const [openEntry, setOpenEntry] = useState(null)
  const unlocked = getUnlocked()
  const entries = ENTRIES[cat] || []
  const known = e => e.id === null || unlocked.has(e.id)
  const knownCount = Object.values(ENTRIES).flat().filter(known).length
  const totalCount = Object.values(ENTRIES).flat().length

  return (
    <div className="ilm-codex">
      <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>
      <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>KNOWLEDGE · {knownCount} OF {totalCount} PAGES RECOVERED</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.4rem', color: 'var(--text-hi)', letterSpacing: '.04em', textShadow: '0 6px 40px rgba(124,58,214,.4)' }}>THE CODEX</div>
      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 2 }}>Everything the Tower will not tell you — written down by those who lived to tell it.</div>

      <div className="ilm-codex-grid">
        <div className="ilm-codex-rail">
          {CATS.map(c => (
            <button key={c} className={`ilm-codex-cat ${cat === c ? 'active' : ''}`} onClick={() => { setCat(c); setOpenEntry(null) }}>{c}</button>
          ))}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: '0.62rem', color: 'var(--gold)' }}>{cat} · {entries.filter(known).length}/{entries.length} KNOWN</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {entries.map(e => {
              const k = known(e)
              const isOpen = openEntry === e.t
              return (
                <div key={e.t}>
                  <div className="ilm-codex-entry" onClick={() => k && setOpenEntry(isOpen ? null : e.t)}
                    style={{ cursor: k ? 'pointer' : 'default', opacity: k ? 1 : 0.5 }}>
                    <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: k ? 'var(--gold-dim)' : 'transparent', border: k ? 'none' : '1px solid rgba(150,110,230,.4)', display: 'inline-block', flex: 'none' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.82rem', letterSpacing: '.06em', color: k ? 'var(--text-hi)' : 'var(--muted)' }}>
                        {k ? e.t : '? ? ?'}
                      </div>
                      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.84rem' }}>
                        {k ? e.d : 'This page has not been lived yet.'}
                      </div>
                    </div>
                    <span style={{ color: 'var(--gold-dim)' }}>{k ? (isOpen ? '›' : '+') : '?'}</span>
                  </div>
                  {isOpen && k && (
                    <div style={{ margin: '2px 0 8px 28px', padding: '12px 16px', borderLeft: '2px solid rgba(184,151,98,.35)', background: 'rgba(12,7,24,.4)', fontFamily: "'Cormorant Garamond',serif", fontStyle: 'italic', fontSize: '0.98rem', lineHeight: 1.6, color: '#d8cbb0' }}>
                      {e.body}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
