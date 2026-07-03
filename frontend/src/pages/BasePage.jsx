import React, { useState, useEffect } from 'react'
import { getBase, getFacilities, buildFacility, upgradeFacility, assignFacility, removeFacility, restHeroes, listHeroes, configTraining, getMageTowerUpgrades, buyResearchUpgrade, craftMaterialEquipment, craftBandages, getBaseFloors, assignBaseFloor, getLegacies, getChatLogs, renameBase, upgradeBase, getMarketCatalog, purchaseMarketItem, getBaseUpgrades, buyBaseUpgrade, getMailList, claimMail, getShip, buildShip, renameShip } from '../api/client'
import MirrorOfFate from '../components/MirrorOfFate'
import ItemIcon from '../components/ItemIcon'
import TeamBanner from '../components/TeamBanner'
import UpgradeTreePanel from '../components/UpgradeTreePanel'
import RecipeBookPanel from '../components/RecipeBookPanel'
import BannerStudio from '../components/BannerStudio'
import { getBanner } from '../api/client'
import { CookingPanel, RefineAetherPanel, BestiaryPanel, ReliquaryPanel, ChronospherePanel, TranscendencePanel } from '../components/EndgamePanels'
import LoreJournal from '../components/LoreJournal'
import GameIcon from '../components/GameIcon'
import { alertDialog } from '../components/DialogHost'

// Facility banner art comes in visual tiers that track the facility's
// LEVEL (art parity is anchored to the Wall, since nothing can out-level
// it). Naming convention: {slug}_tier{n}.png in static/facilities/, slug =
// lowercase with underscores (wall_tier1.png, training_grounds_tier2.png…
// a plural variant like walls_tier1.png is also accepted). Fallback chain:
// exact tier → each lower tier → the flat {Type}.png → hidden.
// Visual progression caps at Tier 4 (the white-marble-and-gold celestial
// look) — levels 45+ keep using the Tier 4 assets.
function facilityArtTier(level) {
  if (level >= 30) return 4
  if (level >= 15) return 3
  if (level >= 5) return 2
  return 1
}

// Late-game facilities never look "tier 1" — by the floor you can build
// them, the base around them is already grand, so their art STARTS at a
// higher tier (no tattered-shack Transcendence Core). Art below these
// minimums intentionally doesn't exist.
const MIN_ART_TIER = { 'Bestiary': 2, 'Reliquary': 2, 'Chronosphere': 3, 'Transcendence Core': 4 }

function FacilityBanner({ type, level, style }) {
  const slug = type.toLowerCase().replace(/ /g, '_')
  const minTier = MIN_ART_TIER[type] || 1
  const tier = Math.max(minTier, facilityArtTier(level || 1))
  const candidates = []
  for (let t = tier; t >= minTier; t--) {
    candidates.push(`/static/facilities/${slug}_tier${t}.png`)
    candidates.push(`/static/facilities/${slug}s_tier${t}.png`)
  }
  candidates.push(`/static/facilities/${type}.png`)
  const [idx, setIdx] = useState(0)
  useEffect(() => { setIdx(0) }, [type, tier])
  if (idx >= candidates.length) return null
  return (
    <img
      src={candidates[idx]}
      alt=""
      onError={() => setIdx(i => i + 1)}
      style={style}
    />
  )
}

// SQLite's CURRENT_TIMESTAMP stores UTC with no timezone marker — passing
// the raw "YYYY-MM-DD HH:MM:SS" string to new Date() makes JS read it as
// LOCAL time, so every chat/mail timestamp displayed hours off (confirmed:
// chatter showing "11:59 PM" at 6:59 PM local). Append the Z so it parses
// as the UTC instant it actually is; toLocaleTimeString then converts.
function parseUtcTimestamp(ts) {
  if (!ts) return new Date()
  return new Date(ts.includes('T') || ts.endsWith('Z') ? ts : ts.replace(' ', 'T') + 'Z')
}

// Hand-painted banner art for the base-wide upgrade tree — keyed by the
// upgrade's id (see DEFAULT_UPGRADES in routers/base.py) so a rename there
// doesn't silently lose its art.
const UPGRADE_BANNERS = {
  infirmary: '/static/facilities/Infirmary.png',
  forge: '/static/facilities/Forge.png',
}

// We now dynamically load banners for facilities based on their type name.
// E.g. /static/facilities/Market.png

// Kept accurate to the actual backend effects (time_service, restaurant/
// infirmary/alchemist/research/sanctum services, get_workshop_discount) —
// each names the real mechanic and the classes the code actually favors.
const FACILITY_TOOLTIPS = {
  "Market": "Generates passive gold (scales with level) and stocks a small shop for ingredients, materials, and bandages. Merchants and Quartermasters give the biggest generation bonus; anyone assigned helps a little and earns passive XP.",
  "Farm": "Grows alchemy INGREDIENTS passively (scales with level) — cook them into consumables at the Dining Hall, or brew them into potions at the Alchemist Lab. Farmers and Druids give the biggest generation bonus.",
  "Training Grounds": "Assigned heroes passively earn XP over time (scales with level) — level up the bench without risking them in the Tower.",
  "Dining Hall": "Assigned cooks passively restore MORALE for the entire living roster, and the kitchen COOKS Farm ingredients into early consumables (rations, stews) heroes can carry into the Tower. Chefs are worth triple anyone else in the kitchen.",
  "Forge": "Crafts weapons, armor, and accessories. Craft quality is capped by your single best Blacksmith — extra smiths of the same tier add a smaller bonus on top.",
  "Infirmary": "Passively heals TRAUMA over time and crafts Bandages (auto-used on your most injured heroes before the next floor). Medics and Priests heal fastest.",
  "Vault": "Each upgrade expands equipment storage capacity. Assigned caretakers don't affect capacity — they just earn passive XP while minding the shelves.",
  "Alchemist Lab": "Brews potions passively over time. Alchemists and Mages brew dramatically faster; high Mental aptitude helps too.",
  "Tavern": "Assigned hosts take the edge off — passively reduces STRESS for the entire living roster. Bards and Chefs make the best hosts.",
  "Skydock": "Discounts the gold cost of upgrading every OTHER facility (up to 50% off), scaling with Skydock level — Magic Engineers triple their contribution. This is where magic battleships will be built: Magic Engineers craft the greatest hulls, but any high-Mental hero can apprentice here for a basic vessel.",
  "Wall": "The base's FOUNDATION — no other facility can be upgraded above the Wall's level, so raise it first. Every level also adds flat defense rating for the coming Raid system (opt-in): raiders must breach the Wall before the Bastion's garrison ever engages.",
  "Bastion": "Your garrison for the coming Raid system (raiding is opt-in). Stationed heroes contribute their strength behind the Wall's cover — and a Magic Engineer's arcane cannons DOUBLE the whole garrison, letting even 1★ heroes hold the line.",
  "Shrine": "Assigned clergy slowly deepen the whole roster's LOYALTY (affinity) — the same track gifts raise, and the one that decides whether a captured hero stays yours. Priests and Acolytes are twice as effective.",
  "Mage Tower": "Conducts magical research for permanent upgrades. Magic Engineers are the most effective researchers, then Mages, then Spellswords.",
  "Mirror of Fate": "Pay gold to instantly reveal a hero's hidden Talent. The Mirror's level sets the detail: a vague tier at first, a numeric range at Lv.5, the exact number at Lv.10.",
  "Bestiary": "Houses beasts captured in the Tower. Kept beasts add their menace to your base's defense rating; higher levels hold more (and bigger) monsters.",
  "Reliquary": "A museum of your conquests — mount the Trophies major Bosses drop (every 10th floor) to grant permanent, roster-wide passive buffs.",
  "Chronosphere": "Bend time once per day: instantly simulate hours of passive base generation (gold, ingredients, XP, fatigue recovery). Upgrades increase the hours skipped.",
  "Transcendence Core": "The endgame furnace — feed it staggering amounts of gold to permanently empower your entire roster, one infusion at a time. Each infusion costs more than the last.",
}

// Tiny inline sparkline showing the real diminishing-returns curve a
// stationed floor follows: stat_bonus_pct = (total_lp / sqrt(headcount)) / 10
// (see get_floor_lp in base_service.py — the backend value this curve is
// built from, not a separate frontend-side recalculation). Steep drop from
// 1→2 heroes, flattening out by 4-5 — exactly the "diminishing returns"
// shape, just keyed on crowding a floor rather than a level number.
function DiminishingReturnsCurve({ curve, current }) {
  if (!curve || curve.length < 2) return null
  const w = 80, h = 28, pad = 3
  const maxVal = curve[0].stat_bonus_pct || 1
  const points = curve.map((pt, i) => {
    const x = pad + (i / (curve.length - 1)) * (w - pad * 2)
    const y = h - pad - (pt.stat_bonus_pct / maxVal) * (h - pad * 2)
    return { x, y, ...pt }
  })
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  const currentPt = points[Math.min(current, points.length) - 1]
  return (
    <svg width={w} height={h} style={{ marginTop: '0.25rem', overflow: 'visible' }}>
      <path d={pathD} fill="none" stroke="rgba(74,222,128,0.5)" strokeWidth="1.5" />
      {currentPt && (
        <circle cx={currentPt.x} cy={currentPt.y} r="3" fill="var(--gold)">
          <title>{`${current} stationed → +${currentPt.stat_bonus_pct}% stats`}</title>
        </circle>
      )}
    </svg>
  )
}

export default function BasePage({ onGoldChange, onSubTabChange, tourTargetSubTab }) {
  const [activeTab, setActiveTab] = useState('lobby')
  const [base, setBase] = useState(null)
  const [facilitiesData, setFacilitiesData] = useState(null)
  const [baseHeroes, setBaseHeroes] = useState([])
  const [resting, setResting] = useState(false)
  const [msg, setMsg] = useState(null)
  const [facilityLoading, setFacilityLoading] = useState(false)
  const [mageUpgrades, setMageUpgrades] = useState(null)
  const [crafting, setCrafting] = useState(false)
  const [marketCatalog, setMarketCatalog] = useState({})
  const [purchasing, setPurchasing] = useState(false)
  const [baseUpgrades, setBaseUpgrades] = useState([])
  const [upgradingId, setUpgradingId] = useState(null)
  
  // Mail
  const [banner, setBanner] = useState(null)
  const [showBannerStudio, setShowBannerStudio] = useState(false)
  const [mailList, setMailList] = useState([])
  const [claiming, setClaiming] = useState(false)
  
  // Legacy & Floors
  const [legacies, setLegacies] = useState([])
  const [expandedLegacyId, setExpandedLegacyId] = useState(null)
  const [legacyPage, setLegacyPage] = useState(0)
  const LEGACIES_PER_PAGE = 10
  const [floorsData, setFloorsData] = useState(null)
  const [assigning, setAssigning] = useState(false)
  const [chats, setChats] = useState([])
  const [newChatIds, setNewChatIds] = useState(new Set())
  const seenChatIds = React.useRef(new Set())
  const hasLoadedChatsOnce = React.useRef(false)

  function applyChats(ch) {
    const list = ch || []
    const fresh = hasLoadedChatsOnce.current ? list.filter(c => !seenChatIds.current.has(c.id)).map(c => c.id) : []
    list.forEach(c => seenChatIds.current.add(c.id))
    hasLoadedChatsOnce.current = true
    setChats(list)
    if (fresh.length) {
      setNewChatIds(new Set(fresh))
      setTimeout(() => setNewChatIds(new Set()), 3000)
    }
  }
  
  const [sortMode, setSortMode] = useState('level-desc')
  const [filterClass, setFilterClass] = useState('All')
  const [ship, setShip] = useState(null)
  const [shipBusy, setShipBusy] = useState(false)
  const [shipNameDraft, setShipNameDraft] = useState('')
  
  useEffect(() => { loadAll() }, [])

  useEffect(() => { onSubTabChange?.(activeTab) }, [activeTab])

  // Hero Chatter feed polls on its own, faster cadence than the rest of the
  // page — it should feel like an ongoing conversation, not a static log
  // that only updates on a full page reload.
  useEffect(() => {
    const interval = setInterval(() => {
      getChatLogs(5).then(applyChats).catch(() => {})
    }, 20000)
    return () => clearInterval(interval)
  }, [])

  async function loadAll() {
    getBanner().then(setBanner).catch(() => {})
    try {
      const [b, fac, heroes, leg, flrs, ch, catalog, upgrades, mail] = await Promise.all([
        getBase(),
        getFacilities(),
        listHeroes(true),
        getLegacies().catch(() => ({ legacies: [] })),
        getBaseFloors().catch(() => ({ floors: [], base_heroes: [] })),
        getChatLogs(5).catch(() => []),
        getMarketCatalog().catch(() => ({})),
        getBaseUpgrades().catch(() => []),
        getMailList().catch(() => [])
      ])
      setBase(b)
      setFacilitiesData(fac)
      setBaseHeroes(heroes.filter(h => h.is_alive === 1 && h.is_on_team === 0))
      setLegacies(leg.legacies || [])
      setFloorsData(flrs)
      applyChats(ch)
      setMarketCatalog(catalog)
      setBaseUpgrades(upgrades)
      setMailList(mail)
      getShip().then(setShip).catch(() => {})
      
      const hasMage = fac.built?.some(f => f.type === 'Mage Tower')
      if (hasMage) {
        const mage = await getMageTowerUpgrades().catch(() => null)
        setMageUpgrades(mage)
      }
    } catch (e) {
      console.error(e)
    }
  }

const handleRenameBase = async () => {
    const newName = prompt("Enter a new name for your base:", base.name);
    if (!newName) return;
    try {
      await renameBase(newName);
      loadAll();
    } catch(e) {
      alertDialog(e.message || "Failed to rename base.");
    }
  };

  const handleRest = async () => {
    setResting(true)
    try {
      const data = await restHeroes()
      alertDialog(`Rested ${data.rested} heroes — Health fully restored, morale/stress/trauma recovered. Cost: ${data.cost} ingredients.`)
      loadAll()
    } catch (e) {
      alertDialog(e.message || "Cannot rest.")
    } finally {
      setResting(false)
    }
  }

  const handleUpgradeBase = async () => {
    try {
      await upgradeBase()
      alertDialog("Base Upgraded! Max Roster Size increased.")
      loadAll()
      if (onGoldChange) onGoldChange()
    } catch(e) { alertDialog(e.message || "Failed to upgrade") }
  }



  async function handleBuyBaseUpgrade(upgradeId) {
    setUpgradingId(upgradeId)
    try {
      await buyBaseUpgrade(upgradeId)
      loadAll()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setUpgradingId(null)
    }
  }

  async function handleBuildFacility(type) {
    setFacilityLoading(true)
    try {
      await buildFacility(type)
      loadAll()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setFacilityLoading(false)
    }
  }

  async function handleUpgradeFacility(facId) {
    setFacilityLoading(true)
    try {
      await upgradeFacility(facId)
      loadAll()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setFacilityLoading(false)
    }
  }

  async function handleAssignFacility(facId, heroId) {
    setFacilityLoading(true)
    try {
      const res = await assignFacility(facId, heroId)
      if (res?.chatter_line) setMsg(res.chatter_line)
      loadAll()
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setFacilityLoading(false)
    }
  }

  async function handleRemoveFacility(heroId) {
    setFacilityLoading(true)
    try {
      await removeFacility(heroId)
      loadAll()
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setFacilityLoading(false)
    }
  }

  async function handleBuyResearch(upgradeId) {
    setFacilityLoading(true)
    try {
      await buyResearchUpgrade(upgradeId)
      loadAll()
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setFacilityLoading(false)
    }
  }

  async function handleCraft(heroId, slot) {
    setCrafting(true)
    try {
      await craftMaterialEquipment(heroId, slot)
      loadAll()
      if (onGoldChange) onGoldChange()
      alertDialog("Crafted successfully!")
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setCrafting(false)
    }
  }

  async function handleCraftBandages(heroId) {
    setCrafting(true)
    try {
      const res = await craftBandages(heroId, 1)
      loadAll()
      if (onGoldChange) onGoldChange()
      alertDialog(`Crafted a Bandage (${res.total} in stock). Auto-used on your most injured heroes before your next floor.`)
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setCrafting(false)
    }
  }

  async function handlePurchase(itemId) {
    setPurchasing(true)
    try {
      const res = await purchaseMarketItem(itemId)
      loadAll()
      if (onGoldChange) onGoldChange()
      const detail = res.material ? `${res.amount}x ${res.material}` : res.ingredients ? `${res.ingredients} ingredients` : ''
      alertDialog(`Purchased ${res.item}! +${detail}`)
    } catch (e) {
      alertDialog(e.message)
    } finally {
      setPurchasing(false)
    }
  }

  async function handleAssignFloor(heroId, floorNum) {
    setAssigning(true)
    try {
      await assignBaseFloor(heroId, floorNum === null ? 0 : floorNum)
      loadAll()
    } catch(e) {
      alertDialog(e.message || e)
    } finally {
      setAssigning(false)
    }
  }

  async function handleClaimMail(mailId) {
    setClaiming(true)
    try {
      await claimMail(mailId)
      loadAll()
      if (onGoldChange) onGoldChange()
    } catch(e) {
      alertDialog(e.message || e)
    } finally {
      setClaiming(false)
    }
  }

  if (!base) return <div className="page text-dim">Loading...</div>
  if (!facilitiesData) return <div className="page text-dim">Loading facilities...</div>

  let materials = {}
  try { materials = JSON.parse(base.materials || '{}') } catch {}

  
  let goldGen = 0;
  let ingredientsGen = 0;
  let aetherGen = 0;
  if (facilitiesData && facilitiesData.built) {
    facilitiesData.built.forEach(f => {
      let multiplier = 1.0 + ((f.heroes?.length || 0) * 0.10);
      if (f.type === 'Market') goldGen += Math.floor(100 * f.level * multiplier);
      if (f.type === 'Farm') ingredientsGen += Math.floor(5 * f.level * multiplier);
      if (f.type === 'Skydock') aetherGen += Math.floor(2 * f.level * multiplier);
    });
  }

  const renderTabs = () => (
    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', overflowX: 'auto' }}>
      {/* Mailbox last — least-visited tab */}
      {['lobby', 'facilities', 'legacy', 'floors', 'lore', 'mail'].map(tab => {
        const locked = !!tourTargetSubTab && tab !== tourTargetSubTab

        let label = tab
        if (tab === 'floors') label = 'Base Hierarchy'
        else if (tab === 'legacy') label = 'Legacies'
        else if (tab === 'lobby') label = 'The Lobby'
        else if (tab === 'mail') label = 'Mailbox'
        else if (tab === 'lore') label = 'Lore Journal'
        
        // Unclaimed mail indicator
        let badge = null;
        if (tab === 'mail') {
          const unclaimed = mailList.filter(m => !m.is_claimed).length
          if (unclaimed > 0) {
            badge = <span style={{ marginLeft: '0.4rem', background: 'var(--gold)', color: '#000', borderRadius: '50%', padding: '0.1rem 0.4rem', fontSize: '0.8rem', fontWeight: 'bold' }}>{unclaimed}</span>
          }
        }

        return (
          <button key={tab} className={`tab-btn ${activeTab === tab ? 'active' : ''}`} disabled={locked} onClick={() => { if (!locked) setActiveTab(tab) }}
          style={{
            background: 'none', border: 'none', padding: '0.5rem 1rem', cursor: locked ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center',
            color: activeTab === tab ? 'var(--gold)' : 'var(--text-dim)',
            borderBottom: activeTab === tab ? '2px solid var(--gold)' : '2px solid transparent',
            fontFamily: 'Cinzel, serif', fontSize: '1.1rem', textTransform: 'uppercase',
            opacity: locked ? 0.35 : 1,
            boxShadow: tab === tourTargetSubTab ? '0 0 8px var(--gold)' : 'none',
          }}>
            {label} {badge}
          </button>
        )
      })}
    </div>
  )


const getGenRate = (fac) => {
    const rates = { Market: [100, 'Gold'], Farm: [5, 'Ingredients'], Skydock: [2, 'Aether'] };
    if (!rates[fac.type]) return null;
    const [per, resName] = rates[fac.type];
    let multiplier = 1.0 + ((fac.heroes || []).length * 0.10);
    let amt = Math.floor(per * fac.level * multiplier);
    return `Generating: +${amt} ${resName} / 5 mins`;
  };

  return (
    <div className="page">
      <div className="section-header">Home Base</div>

      {renderTabs()}

      {activeTab === 'lobby' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Top Row: Base Stats & Recovery */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
            
            {/* Base Expansion */}
            <div className="card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', color: 'var(--text-hi)', marginBottom: '1rem' }}>Base Expansion</div>
              <div className="text-dim" style={{ fontSize: '1.1rem', lineHeight: 1.6, marginBottom: 'auto' }}>
                Upgrading the base expands your facilities and allows you to recruit more heroes to your cause.<br/><br/>
                Current Max Roster: <span className="text-hi" style={{ fontSize: '1.3rem' }}>{base.max_roster_size || 10}</span><br/>
                Next Upgrade: <span className="text-green">+10 Roster Slots</span>
              </div>
              <button className="btn btn-gold" onClick={handleUpgradeBase} style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', marginTop: '2rem' }}>
                Upgrade Base ({5000 * base.level}G)
              </button>
            </div>

            {/* The Lobby Profile */}
            <div className="card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
              <div 
                className="hover-brighten"
                style={{ cursor: 'pointer', transition: 'transform 0.2s', marginBottom: '1rem' }} 
                onClick={() => setShowBannerStudio(true)} 
                title="Click to customize your Team Banner"
              >
                <TeamBanner banner={banner} size={300} />
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.8rem', marginBottom: '0.4rem' }}>
                <div style={{ fontFamily: 'Cinzel, serif', fontSize: '2.4rem', color: 'var(--gold)', lineHeight: 1.1 }}>
                  {base.name}
                </div>
                <button className="hover-brighten" style={{ background: 'transparent', border: 'none', padding: '0.2rem', fontSize: '1.4rem', color: 'var(--text-dim)', cursor: 'pointer', display: 'flex' }} onClick={handleRenameBase} title="Rename Base">✎</button>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                <span style={{ fontSize: '1.3rem', color: 'var(--text-dim)' }}>Lv.{base.level}</span>
                {base.difficulty && base.difficulty !== 'normal' && (
                  <span style={{
                    fontSize: '0.8rem', padding: '0.15rem 0.6rem', borderRadius: 5,
                    fontFamily: 'Cinzel, serif', letterSpacing: '1px',
                    color: base.difficulty === 'hard' ? '#e66' : '#6e6',
                    border: `1px solid ${base.difficulty === 'hard' ? 'rgba(230,100,100,0.4)' : 'rgba(100,230,100,0.4)'}`,
                  }}>
                    {base.difficulty.toUpperCase()} MODE
                  </span>
                )}
              </div>
              
              <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center', width: '100%', padding: '1.5rem 0', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)', marginBottom: '1.5rem' }}>
                <div style={{ textAlign: 'center' }}>
                  <div className="text-dim" style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.3rem' }}>Treasury</div>
                  <div className="text-gold" style={{ fontFamily: 'Cinzel, serif', fontSize: '1.4rem' }}>{base.gold.toLocaleString()} G</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div className="text-dim" style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.3rem' }}>Ingredients</div>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.4rem', color: '#9fd68a' }}>{base.ingredients?.toLocaleString()}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div className="text-dim" style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.3rem' }}>Aether</div>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.4rem', color: '#8fb8ff' }}>{(base.aether || 0).toLocaleString()}</div>
                </div>
              </div>
              
              <div style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '1.0rem' }}>
                  <span className="text-dim">Market:</span>
                  <span className="text-gold">+{goldGen} G / 5m</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '1.0rem' }}>
                  <span className="text-dim">Farm:</span>
                  <span style={{ color: '#9fd68a' }}>+{ingredientsGen} Ing / 5m</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.0rem' }}>
                  <span className="text-dim">Skydock:</span>
                  <span style={{ color: '#8fb8ff' }}>+{aetherGen} Aeth / 5m</span>
                </div>
              </div>
            </div>

            {/* Rest & Recovery */}
            <div className="card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', color: 'var(--text-hi)', marginBottom: '1rem' }}>Rest & Recovery</div>
              <div className="text-dim" style={{ fontSize: '1.1rem', lineHeight: 1.6, marginBottom: 'auto' }}>
                Resting at base recovers morale (+25), reduces stress (-20), and slowly heals trauma (-5) for all living heroes.<br/><br/>
                Resting costs 50 ingredients (a hot meal for the roster) and has a 5-minute cooldown.
              </div>
              {(() => {
                const now = Date.now() / 1000;
                const lastRest = base.last_rest_time || 0;
                const cd = 300;
                const rem = Math.max(0, cd - (now - lastRest));
                const isCooldown = rem > 0;
                return (
                  <button className="btn btn-gold" onClick={handleRest} disabled={resting || isCooldown} style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', marginTop: '2rem' }}>
                    {resting ? 'Resting...' : isCooldown ? `Cooldown (${Math.ceil(rem)}s)` : 'Rest All Heroes (50 Ingredients)'}
                  </button>
                )
              })()}
              {msg && <div className="text-green" style={{ marginTop: '1rem', fontSize: '1.1rem', textAlign: 'center' }}>{msg}</div>}
            </div>

            </div>
            
            {/* Bottom Row: Hero Chatter Box */}
          <div className="card" style={{ padding: '1.5rem', minHeight: '250px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.4rem', color: 'var(--gold)', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              Hero Chatter
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.7rem', color: 'var(--green)', fontFamily: 'monospace', letterSpacing: '1px' }}>
                <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'var(--green)', animation: 'pulse-live 1.5s ease-in-out infinite' }} />
                LIVE
              </span>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              {chats && chats.length > 0 ? chats.map(chat => (
                <div key={chat.id} style={{ marginBottom: '0.6rem', transition: 'background 1s ease', background: newChatIds.has(chat.id) ? 'rgba(201,168,76,0.12)' : 'transparent', borderRadius: 4, padding: newChatIds.has(chat.id) ? '0.4rem' : '0' }}>
                  <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.2rem' }}>
                    <span className="text-dim" style={{ fontSize: '0.8rem', whiteSpace: 'nowrap' }}>[{parseUtcTimestamp(chat.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}]</span>
                    <span style={{ color: 'var(--gold)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>[{chat.location}]</span>
                  </div>
                  {(chat.messages || []).map((m, i) => (
                    <div key={i} style={{ fontSize: '1.05rem', marginLeft: '0.5rem' }}>
                      <span className="text-hi" style={{ fontFamily: 'Cinzel, serif' }}>{m.speaker}:</span> {m.message}
                    </div>
                  ))}
                </div>
              )) : (
                <div className="text-dim" style={{ fontStyle: 'italic', textAlign: 'center', marginTop: '2rem' }}>The lobby is quiet...</div>
              )}
            </div>
          </div>

        </div>
      )}

      {activeTab === 'facilities' && (
        <>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Left Column: Built Facilities */}
          <div style={{ flex: '2 1 500px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* ── Shipyard — magic battleship, docked at the Skydock ── */}
            {facilitiesData.built?.some(f => f.type === 'Skydock') && ship && (
              <div className="card" style={{ overflow: 'hidden', padding: 0, border: '1px solid rgba(160,80,255,0.4)' }}>
                <div style={{ width: '100%', aspectRatio: '21/9', overflow: 'hidden', position: 'relative', background: 'radial-gradient(ellipse at 50% 80%, rgba(60,30,100,0.4), #08060e)' }}>
                  {ship.tier > 0 ? (
                    <img src={`/images/battleships/ship_${ship.tier}.png`} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center' }} />
                  ) : (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '0.4rem' }}>
                      <div style={{ fontFamily: 'Cinzel, serif', letterSpacing: '0.2em', color: 'var(--text-dim)' }}>THE DRYDOCK IS EMPTY</div>
                      <div className="text-dim" style={{ fontSize: '0.8rem', fontStyle: 'italic' }}>Lay a keel below.</div>
                    </div>
                  )}
                  <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(0,0,0,0) 55%, rgba(10,10,14,0.95) 100%)' }} />
                  {ship.tier > 0 && banner && (
                    <div style={{ position: 'absolute', top: 8, right: 12 }} title="Your banner flies from the mast">
                      <TeamBanner banner={banner} size={56} />
                    </div>
                  )}
                </div>
                <div style={{ padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div>
                      <h3 style={{ fontFamily: 'Cinzel, serif', color: '#b06aff', margin: 0 }}>
                        ⚓ {ship.tier > 0 ? (ship.ship_name || ship.ship.name) : 'Shipyard'}
                        {ship.tier > 0 && <span className="text-dim" style={{ fontSize: '0.8rem', marginLeft: '0.6rem' }}>{ship.ship.name} · Tier {ship.tier}/5</span>}
                      </h3>
                      {ship.tier > 0 && (
                        <div className="text-dim" style={{ fontSize: '0.82rem', fontStyle: 'italic', marginTop: '0.3rem', maxWidth: 560 }}>{ship.ship.desc}</div>
                      )}
                    </div>
                    {ship.defense && (
                      <div title="Base defense rating for the coming Raid system: Wall + Bastion garrison + docked ship."
                        style={{ fontFamily: 'Cinzel, serif', fontSize: '0.8rem', color: 'var(--text-dim)', textAlign: 'right', cursor: 'help' }}>
                        Defense <span style={{ color: 'var(--gold)', fontSize: '1.1rem' }}>{ship.defense.total}</span>
                        <div style={{ fontSize: '0.65rem' }}>Wall {ship.defense.wall} · Garrison {ship.defense.garrison} · Ship {ship.defense.ship}{ship.defense.beasts > 0 && <> · Beasts {ship.defense.beasts}</>}</div>
                      </div>
                    )}
                  </div>

                  {ship.tier > 0 && (
                    <div style={{ display: 'flex', gap: '1.2rem', marginTop: '0.6rem', fontSize: '0.8rem' }}>
                      <span className="text-dim">Crew capacity <span style={{ color: 'var(--text-hi)' }}>{ship.ship.crew}</span></span>
                      <span className="text-dim">Firepower <span style={{ color: 'var(--text-hi)' }}>{ship.ship.defense}</span></span>
                      <form style={{ marginLeft: 'auto', display: 'flex', gap: '0.4rem' }} onSubmit={async (e) => {
                        e.preventDefault()
                        if (!shipNameDraft.trim()) return
                        try { await renameShip(shipNameDraft); setShipNameDraft(''); getShip().then(setShip) } catch (err) { alertDialog(err.message) }
                      }}>
                        <input className="input" placeholder="Name your ship…" value={shipNameDraft} onChange={e => setShipNameDraft(e.target.value)}
                          style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', padding: '0.25rem 0.5rem', color: '#fff', borderRadius: 4, fontSize: '0.78rem', width: 160 }} />
                        <button className="btn" type="submit" style={{ fontSize: '0.7rem', padding: '0.25rem 0.6rem' }} disabled={!shipNameDraft.trim()}>Christen</button>
                      </form>
                    </div>
                  )}

                  {ship.next ? (
                    <div style={{ marginTop: '0.9rem', borderTop: '1px solid var(--border)', paddingTop: '0.8rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.6rem' }}>
                      <div>
                        <div style={{ fontFamily: 'Cinzel, serif', fontSize: '0.85rem', color: 'var(--text-hi)' }}>
                          {ship.tier > 0 ? 'Next hull' : 'Lay a keel'}: {ship.next.name} <span className="text-gold">({ship.next.cost.toLocaleString()}g)</span>
                        </div>
                        <div className="text-dim" style={{ fontSize: '0.72rem', marginTop: '0.2rem' }}>
                          {ship.next.requires === 'engineer'
                            ? 'Requires a Magic Engineer assigned to the Skydock.'
                            : 'Requires a Magic Engineer — or any hero with 70+ Mental aptitude — assigned to the Skydock.'}
                        </div>
                        {ship.blocker && <div style={{ fontSize: '0.72rem', color: 'var(--red)', marginTop: '0.2rem' }}>{ship.blocker}</div>}
                      </div>
                      <button
                        className="btn"
                        disabled={!ship.can_build || shipBusy}
                        onClick={async () => {
                          setShipBusy(true)
                          try {
                            const res = await buildShip()
                            alertDialog(`The ${res.name} takes to the sky! (Tier ${res.tier})`)
                            getShip().then(setShip)
                            getBase().then(setBase)
                          } catch (err) { alertDialog(err.message) } finally { setShipBusy(false) }
                        }}
                        style={{ border: '1px solid #b06aff', color: '#d0a0ff', background: 'rgba(80,30,130,0.2)', padding: '0.5rem 1.2rem' }}
                      >
                        {shipBusy ? 'Building…' : ship.tier > 0 ? 'Refit Hull' : 'Build Ship'}
                      </button>
                    </div>
                  ) : (
                    <div style={{ marginTop: '0.9rem', fontFamily: 'Cinzel, serif', fontSize: '0.8rem', color: '#b06aff', textAlign: 'center' }}>
                      ✦ The greatest hull the Skydock can produce. The sky is yours. ✦
                    </div>
                  )}
                </div>
              </div>
            )}
            {facilitiesData.built.sort((a,b) => a.cost - b.cost).map(fac => (
              <div key={fac.id} className="card" style={{ overflow: 'hidden', padding: 0 }}>
                <div style={{ width: '100%', aspectRatio: '3/1', overflow: 'hidden', position: 'relative' }}>
                  <FacilityBanner type={fac.type} level={fac.level} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center', display: 'block' }} />
                  <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(0,0,0,0) 50%, rgba(10,10,14,0.95) 100%)' }} />
                </div>
                <div style={{ padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <h3 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', margin: 0 }}>{fac.type} (Lv.{fac.level})</h3>
                        <span title={FACILITY_TOOLTIPS[fac.type] || "Base facility."} style={{ fontSize: '0.8rem', color: 'var(--gold)', cursor: 'help' }}>[?]</span>
                      </div>
                      {getGenRate(fac) && (
                        <div style={{ fontSize: '0.9rem', color: 'var(--star2)', marginTop: '0.2rem', fontFamily: 'Cinzel, serif' }}>
                          {getGenRate(fac)}
                        </div>
                      )}
                    </div>
                  {fac.level < fac.max_level && (
                    <div style={{ textAlign: 'right' }}>
                      <button
                        className="btn"
                        onClick={() => handleUpgradeFacility(fac.id)}
                        disabled={facilityLoading || base.gold < fac.upgrade_cost || fac.wall_capped}
                        title={fac.wall_capped ? `The Wall must reach Level ${fac.level + 1} first — nothing outgrows its foundation.` : undefined}
                        style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}
                      >
                        Upgrade ({fac.upgrade_cost}g)
                      </button>
                      {fac.wall_capped && (
                        <div style={{ fontSize: '0.65rem', color: 'var(--red)', marginTop: '0.2rem' }}>
                          🧱 Wall Lv.{fac.level + 1} required
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                  {fac.heroes.map(h => (
                    <div key={h.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(0,0,0,0.3)', padding: '0.5rem 0.75rem', borderRadius: 6 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <img src={`/${h.portrait_path}`} alt={h.name} style={{ width: 100, height: 100, borderRadius: '50%', objectFit: 'cover', objectPosition: 'center 15%', border: '1px solid var(--border)' }} />
                            <div className="text-hi" style={{ fontSize: '0.8rem', marginTop: '0.3rem', textAlign: 'center' }}>{h.name}</div>
                          </div>
                      <span style={{ fontSize: '0.95rem' }}>{h.name}</span>
                      <button onClick={() => handleRemoveFacility(h.id)} style={{ background: 'none', border: 'none', color: 'var(--red)', cursor: 'pointer', marginLeft: '0.5rem' }}>&times;</button>
                      {fac.type === 'Forge' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginLeft: '0.5rem' }}>
                          <button onClick={() => handleCraft(h.id, 'weapon')} disabled={crafting} className="btn btn-gold" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>Weapon (100g, 3 Iron, 1 Bone)</button>
                          <button onClick={() => handleCraft(h.id, 'armor')} disabled={crafting} className="btn btn-gold" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>Armor (100g, 2 Dark Crystal, 2 Iron)</button>
                          <button onClick={() => handleCraft(h.id, 'accessory')} disabled={crafting} className="btn btn-gold" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>Accessory (100g, 3 Dust, 1 Ear)</button>
                        </div>
                      )}
                      {fac.type === 'Infirmary' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginLeft: '0.5rem' }}>
                          <button onClick={() => handleCraftBandages(h.id)} disabled={crafting} className="btn btn-gold" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>Bandage (15 ingredients)</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {fac.heroes.length < fac.slots_unlocked && (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <select id={`assign-${fac.id}`} className="input" style={{ flex: 1 }}>
                      <option value="">Assign hero...</option>
                      {baseHeroes.filter(h => !fac.heroes.find(fh => fh.id === h.id)).map(h => (
                        <option key={h.id} value={h.id}>{h.name} ({h.class_name})</option>
                      ))}
                    </select>
                    <button className="btn btn-primary" onClick={() => {
                      const sel = document.getElementById(`assign-${fac.id}`)
                      if (sel && sel.value) handleAssignFacility(fac.id, parseInt(sel.value))
                    }} disabled={facilityLoading}>Assign</button>
                  </div>
                )}

                {/* Market Shop */}
                {fac.type === 'Market' && Object.keys(marketCatalog).length > 0 && (
                  <div style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: 6 }}>
                    <div className="text-dim" style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>Shop</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.5rem' }}>
                      {Object.entries(marketCatalog).map(([itemId, item]) => (
                        <div key={itemId} className="card" style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <ItemIcon name={item.name} kind="material" size={26} />
                            <div style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>{item.name}</div>
                          </div>
                          <button 
                            className="btn btn-gold" 
                            onClick={() => handleBuyMarketItem(itemId)} 
                            disabled={purchasing || (item.currency === 'gold' ? base.gold : base.gems) < item.cost}
                            style={{ fontSize: '0.75rem', padding: '0.3rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem' }}
                          >
                            {item.cost} {item.currency === 'gold' ? <span>Gold <GameIcon name="gold_coin" size={14} /></span> : <span>Gems <GameIcon name="gem" size={14} /></span>}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Mage Tower Research */}
                {fac.type === 'Mage Tower' && mageUpgrades && (
                  <div style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: 6 }}>
                    <div style={{ color: 'var(--purple)', marginBottom: '0.5rem' }}>Research Points: {mageUpgrades.points}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.5rem' }}>
                      {mageUpgrades.upgrades.map(u => (
                        <div key={u.id} className="card" style={{ padding: '0.5rem' }}>
                          <div style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>{u.name} (Lv.{u.level}/{u.max_level})</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', margin: '0.2rem 0 0.5rem' }}>{u.desc}</div>
                          <button className="btn" onClick={() => handleBuyResearch(u.id)} disabled={facilityLoading || u.level >= u.max_level || mageUpgrades.points < u.cost} style={{ width: '100%', fontSize: '0.75rem', padding: '0.2rem' }}>
                            {u.level >= u.max_level ? 'MAX' : `Research (${u.cost} RP)`}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Mirror of Fate — talent reveals */}
                {fac.type === 'Mirror of Fate' && (
                  <MirrorOfFate
                    level={fac.level}
                    gold={base.gold}
                    onGoldChange={() => { loadAll(); if (onGoldChange) onGoldChange() }}
                  />
                )}

                {/* Base-upgrade enhancement tracks (gold-bought, separate from facility level) */}
                {fac.type === 'Infirmary' && (
                  <UpgradeTreePanel upgrade={baseUpgrades.find(u => u.id === 'infirmary')} gold={base.gold} busy={upgradingId === 'infirmary'} onBuy={handleBuyBaseUpgrade} />
                )}
                {fac.type === 'Forge' && (
                  <>
                    <UpgradeTreePanel upgrade={baseUpgrades.find(u => u.id === 'forge')} gold={base.gold} busy={upgradingId === 'forge'} onBuy={handleBuyBaseUpgrade} />
                    <RecipeBookPanel assignedHeroes={fac.heroes} gold={base.gold} materials={materials} onCrafted={() => { loadAll(); if (onGoldChange) onGoldChange() }} />
                  </>
                )}

                {/* Economy + endgame facility panels */}
                {fac.type === 'Dining Hall' && <CookingPanel onResourceChange={() => { loadAll(); if (onGoldChange) onGoldChange() }} />}
                {fac.type === 'Alchemist Lab' && <RefineAetherPanel onResourceChange={() => { loadAll(); if (onGoldChange) onGoldChange() }} />}
                {fac.type === 'Bestiary' && <BestiaryPanel />}
                {fac.type === 'Reliquary' && <ReliquaryPanel />}
                {fac.type === 'Chronosphere' && <ChronospherePanel onResourceChange={() => { loadAll(); if (onGoldChange) onGoldChange() }} />}
                {fac.type === 'Transcendence Core' && <TranscendencePanel gold={base.gold} onResourceChange={() => { loadAll(); if (onGoldChange) onGoldChange() }} />}
                </div>
              </div>
            ))}
          </div>

          {/* Right Column: Available Facilities */}
          <div style={{ flex: '1 1 300px' }}>
            <h3 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', marginBottom: '1rem' }}>Available Facilities</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {facilitiesData.available.sort((a,b) => a.cost - b.cost).map(fac => (
                <div key={fac.type} className="card" style={{ display: 'flex', flexDirection: 'column', padding: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontFamily: 'Cinzel, serif', fontSize: '1.1rem', color: 'var(--gold)' }}>{fac.type}</span>
                        <span title={FACILITY_TOOLTIPS[fac.type] || "Base facility."} style={{ fontSize: '0.8rem', color: 'var(--gold)', cursor: 'help' }}>[?]</span>
                      </div>
                      <button className="btn btn-gold" onClick={() => handleBuildFacility(fac.type)} disabled={facilityLoading || base.gold < fac.cost} style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}>
                        Build ({fac.cost}g)
                      </button>
                    </div>
                  {fac.floor_restricted && (
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', fontStyle: 'italic' }}>Unlocked at Floor {fac.unlock_floor}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        </>
      )}

      {showBannerStudio && (
        <BannerStudio
          onClose={() => setShowBannerStudio(false)}
          onSaved={() => getBanner().then(setBanner).catch(() => {})}
        />
      )}

      {activeTab === 'mail' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '800px', margin: '0 auto' }}>
          <h3 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', marginBottom: '0.5rem' }}>Mailbox</h3>
          {mailList.length === 0 && <div className="text-dim text-sm text-center" style={{ marginTop: '2rem' }}>Your inbox is empty.</div>}
          
          {mailList.map(mail => (
            <div key={mail.id} className="card" style={{ padding: '1rem', border: mail.is_claimed ? '1px solid var(--border)' : '1px solid var(--gold)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: mail.is_claimed ? 'var(--text-hi)' : 'var(--gold)' }}>{mail.subject}</div>
                  <div className="text-dim text-sm" style={{ marginTop: '0.2rem' }}>From: {mail.sender} &nbsp;·&nbsp; {parseUtcTimestamp(mail.created_at).toLocaleDateString()}</div>
                </div>
                {!mail.is_claimed ? (
                  <button className="btn btn-gold" onClick={() => handleClaimMail(mail.id)} disabled={claiming} style={{ padding: '0.5rem 1rem' }}>
                    Claim Rewards
                  </button>
                ) : (
                  <span className="text-dim text-sm">Claimed</span>
                )}
              </div>
              
              <div style={{ lineHeight: 1.6, color: 'var(--text-hi)', whiteSpace: 'pre-wrap', marginBottom: '1.5rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
                {mail.body}
              </div>
              
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <span className="text-dim text-sm" style={{ alignSelf: 'center' }}>Rewards:</span>
                {(() => {
                  try {
                    const rw = JSON.parse(mail.rewards_json || '{}')
                    const badges = []
                    if (rw.gems) badges.push(<div key="gems" style={{ padding: '0.3rem 0.6rem', background: 'rgba(0,255,255,0.1)', border: '1px solid rgba(0,255,255,0.3)', borderRadius: 4, color: '#00ffff' }}>{rw.gems} <GameIcon name="gem" size={14} /></div>)
                    if (rw.gold) badges.push(<div key="gold" style={{ padding: '0.3rem 0.6rem', background: 'rgba(201,168,76,0.1)', border: '1px solid var(--gold)', borderRadius: 4, color: 'var(--gold)' }}>{rw.gold} Gold</div>)
                    if (rw.ingredients || rw.supplies) badges.push(<div key="ingredients" style={{ padding: '0.3rem 0.6rem', background: 'rgba(159,214,138,0.1)', border: '1px solid #9fd68a', borderRadius: 4, color: 'var(--text-hi)' }}>{(rw.ingredients || 0) + (rw.supplies || 0)} Ingredients</div>)
                    return badges
                  } catch (e) {
                    return null
                  }
                })()}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'legacy' && (
        <div>
          <h3 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', marginBottom: '1rem' }}>
            Fallen Heroes {legacies.length > 0 && <span className="text-dim text-sm">({legacies.length})</span>}
          </h3>
          {legacies.length === 0 && <div className="text-dim text-sm">No legacies found.</div>}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {legacies.slice(legacyPage * LEGACIES_PER_PAGE, (legacyPage + 1) * LEGACIES_PER_PAGE).map(leg => {
              const bonus = (() => { try { return JSON.parse(leg.bonus_json || '{}') } catch { return {} } })()
              const expanded = expandedLegacyId === leg.id
              return (
                <div key={leg.id} className="card" style={{ padding: '0.6rem 0.9rem', cursor: 'pointer' }}
                     onClick={() => setExpandedLegacyId(expanded ? null : leg.id)}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {leg.is_sacrifice && leg.portrait_path ? (
                      <img src={`/${leg.portrait_path}`} alt={leg.hero_name} style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover', objectPosition: 'center 15%', border: '1px solid var(--gold)', flexShrink: 0 }} />
                    ) : (
                      <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#222', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem', color: '#555', flexShrink: 0 }}>
                        ✦
                      </div>
                    )}
                    <div style={{ minWidth: 110, fontFamily: 'Cinzel, serif', color: 'var(--text-hi)', fontSize: '0.9rem' }}>{leg.hero_name}</div>
                    <div className="text-dim text-xs" style={{ minWidth: 90 }}>{leg.is_sacrifice ? 'Sacrificed' : 'Fallen'} · {leg.hero_star}★</div>
                    <div className="text-xs" style={{ color: 'var(--gold)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{leg.title}</div>
                    <div className="text-dim text-xs" style={{ flexShrink: 0 }}>{expanded ? '▲' : '▼'}</div>
                  </div>
                  {expanded && (
                    <div style={{ marginTop: '0.6rem', paddingTop: '0.6rem', borderTop: '1px solid var(--border)' }}>
                      <div className="text-xs text-dim" style={{ lineHeight: 1.4, marginBottom: '0.4rem' }}>{leg.flavor_text}</div>
                      <div className="text-xs text-dim">
                        Floors survived: {bonus.floors_survived ?? 0} · Kills: {bonus.kills ?? 0} · Legacy: {bonus.primary_bonus?.desc || 'None'}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
          {legacies.length > LEGACIES_PER_PAGE && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
              <button className="btn" disabled={legacyPage === 0} onClick={() => setLegacyPage(p => Math.max(0, p - 1))}>← Prev</button>
              <div className="text-dim text-sm" style={{ alignSelf: 'center' }}>
                Page {legacyPage + 1} of {Math.ceil(legacies.length / LEGACIES_PER_PAGE)}
              </div>
              <button className="btn" disabled={(legacyPage + 1) * LEGACIES_PER_PAGE >= legacies.length} onClick={() => setLegacyPage(p => p + 1)}>Next →</button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'floors' && floorsData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card" style={{ marginBottom: '1rem', padding: '1rem 1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.1rem', color: 'var(--text-hi)' }}>Base Hierarchy</div>
              <div className="text-dim text-sm">
                Drag heroes onto a floor to station them — stationed heroes get an all-stats bonus in the Tower and recover fatigue faster.
              </div>
            </div>
            {/* Full mechanics behind a disclosure — the three-paragraph wall
                of text was the first thing the tab showed. */}
            <details style={{ marginTop: '0.5rem' }}>
              <summary className="text-sm" style={{ cursor: 'pointer', userSelect: 'none', color: 'rgba(201,168,76,0.8)' }}>
                How the bonus math works
              </summary>
              <div className="text-dim text-sm" style={{ lineHeight: 1.6, marginTop: '0.5rem' }}>
                Each floor has a fixed bonus pool that's split evenly among whoever's stationed there — higher floors have
                a bigger pool, but spreading more heroes across one floor shrinks everyone's individual share.
                Diminishing returns kick in fast: going from 1 to 2 heroes on a floor costs each of them far more than
                2 to 3 does. The little curve under each floor's bonus % shows exactly where it sits on that drop-off.
                Every hero always lives on some floor — drag them between floors to redistribute.
              </div>
            </details>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {/* Everyone lives on a floor (backend defaults everyone to Floor 1),
                so there's no "unassigned" pool anymore — the floors ARE the
                roster view; drag heroes between floors to redistribute. */}
            <div style={{ flex: '1 1 100%', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <h3 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', marginBottom: '0.5rem' }}>Floors</h3>
              {floorsData.floors.map(f => (
                <div key={f.floor_number} className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.2rem', padding: '0.85rem 1rem', borderLeft: '2px solid var(--gold-dim)' }}>
                  <div style={{ width: '100px', flexShrink: 0 }}>
                    <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', fontSize: '1.05rem' }}>Floor {f.floor_number}</div>
                    <div className="text-green" style={{ fontSize: '0.75rem', fontWeight: 'bold' }} title="Stat bonus per stationed hero, and bonus fatigue recovery rate">
                      +{f.stat_bonus_pct}% stats
                    </div>
                    {f.bonus_curve && <DiminishingReturnsCurve curve={f.bonus_curve} current={Math.max(1, f.heroes.length)} />}
                  </div>
                  <div style={{ flex: 1, display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    {/* Render assigned heroes */}
                    {f.heroes.map(h => (
                      <div key={h.id}
                           draggable
                           onDragStart={(e) => e.dataTransfer.setData('heroId', h.id)}
                           onClick={() => { if (f.floor_number !== 1) handleAssignFloor(h.id, 1) }}
                           style={{ cursor: 'grab', position: 'relative' }}
                           title={f.floor_number !== 1 ? `${h.name} (Lv ${h.level} ${h.hero_class}) — drag to another floor, or click to send back to Floor 1` : `${h.name} (Lv ${h.level} ${h.hero_class}) — drag to another floor`}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <img src={`/${h.portrait_path}`} alt={h.name} draggable={false} style={{ width: 100, height: 100, borderRadius: '50%', objectFit: 'cover', objectPosition: 'center 15%', border: '1px solid var(--border)' }} />
                            <div className="text-hi" style={{ fontSize: '0.8rem', marginTop: '0.3rem', textAlign: 'center' }}>{h.name}</div>
                          </div>
                      </div>
                    ))}
                    {/* Render single empty drop slot */}
                    <div onDragOver={(e) => e.preventDefault()}
                         onDrop={(e) => {
                           e.preventDefault();
                           const heroId = e.dataTransfer.getData('heroId');
                           if (heroId) {
                             handleAssignFloor(heroId, f.floor_number);
                           }
                         }}
                         style={{ 
                           width: 100, height: 100, borderRadius: '50%', 
                           border: '1px dashed var(--text-dim)', 
                           display: 'flex', alignItems: 'center', justifyContent: 'center',
                           transition: 'all 0.2s'
                         }}>
                      <span className="text-dim" style={{ fontSize: '1.5rem' }}>+</span>
                    </div>
                  </div>
                </div>
              ))}
              <div className="text-dim text-sm" style={{ fontStyle: 'italic', marginTop: '0.3rem' }}>
                ⛰ A new base floor unlocks every 10 Tower floors cleared. Every hero lives on a floor —
                new arrivals settle on Floor 1; spread them out as more floors open up.
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'lore' && (
        <div className="card" style={{ maxWidth: 780, margin: '0 auto', width: '100%' }}>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--gold)', marginBottom: '1.2rem' }}>
            <GameIcon name="journal" size={20} /> Lore Journal
          </div>
          <div className="text-dim" style={{ fontSize: '0.8rem', marginBottom: '1.2rem' }}>
            A new page unlocks every 10 floors cleared — written from what your team actually fought and chose along the way.
          </div>
          <LoreJournal inline />
        </div>
      )}
    </div>
  )
}
