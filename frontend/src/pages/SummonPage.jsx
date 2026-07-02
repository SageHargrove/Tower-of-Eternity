import React, { useState, useEffect } from 'react'
import { pullHeroes, getOdds, getEquipmentOdds, getBase, getPityInfo, redeemSpark, redeemEquipSpark, pullEquipment } from '../api/client'
import HeroCard from '../components/HeroCard'
import SummoningOverlay from '../components/SummoningOverlay'
import FairyTip from '../components/FairyTip'
import { confirmDialog } from '../components/DialogHost'
import { EquipmentTypeIcon } from '../components/EquipmentTypeIcon'
import GameIcon from '../components/GameIcon'

// Mirrors backend services/class_service.py's is_combat_class() exclusion
// list — these classes can't be deployed to fight, only assigned to base
// facilities, which isn't obvious the first time you pull one.
const NON_COMBAT_CLASSES = ["Chef", "Blacksmith", "Quartermaster", "Alchemist", "Priest"]

// One pull button with its cost and, when the player can't afford it, the
// exact shortfall — a dead disabled button with no explanation was the old
// behavior and it's the single most confusing state on this page.
function SummonButton({ title, cost, currency, balance, onClick, disabled, pulling, premium }) {
  const short = balance < cost
  return (
    <button
      className="btn btn-gold"
      onClick={onClick}
      disabled={disabled}
      style={{
        flex: 1,
        padding: premium ? '1.8rem 1rem' : '1.2rem 1rem',
        fontSize: premium ? '1.5rem' : '1.25rem',
        fontFamily: 'Cinzel, serif',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.45rem',
        border: premium ? '2px solid var(--gold)' : '1px solid var(--border-hi)',
        borderRadius: 8,
        background: premium
          ? 'linear-gradient(170deg, rgba(201,168,76,0.16), rgba(201,168,76,0.05))'
          : 'linear-gradient(170deg, rgba(150,150,150,0.12), rgba(150,150,150,0.04))',
        boxShadow: premium && !short ? '0 0 20px rgba(201,168,76,0.25)' : 'none',
      }}
    >
      <div>{pulling ? 'Summoning…' : title}</div>
      <div style={{ fontSize: premium ? '0.95rem' : '0.85rem', color: '#fff', opacity: 0.8, letterSpacing: '2px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
        {cost.toLocaleString()} {currency === 'gem' ? 'GEMS' : 'GOLD'} <GameIcon name={currency === 'gem' ? 'gem' : 'gold_coin'} size={14} />
      </div>
      {short && !pulling && (
        <div style={{ fontSize: '0.72rem', color: 'var(--red)', opacity: 0.9, letterSpacing: '0.05em' }}>
          Need {(cost - balance).toLocaleString()} more
        </div>
      )}
    </button>
  )
}

// Collapsible info card — pull-rate tables are reference material, not
// something the player needs staring at them on every visit.
function Collapsible({ title, children, defaultOpen = false, headerExtra }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card" style={{ marginTop: '1rem', padding: open ? '1.5rem' : '0.9rem 1.5rem' }}>
      <div
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', userSelect: 'none' }}
        onClick={() => setOpen(o => !o)}
      >
        <div className="section-header" style={{ margin: 0, border: 'none', paddingBottom: 0 }}>{title}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          {open && headerExtra && <div onClick={e => e.stopPropagation()}>{headerExtra}</div>}
          <span className="text-dim" style={{ fontSize: '0.8rem' }}>{open ? '▾ Hide' : '▸ Show'}</span>
        </div>
      </div>
      {open && <div style={{ marginTop: '1rem' }}>{children}</div>}
    </div>
  )
}

export default function SummonPage({ onGoldChange }) {
  const [activeTab, setActiveTab] = useState('heroes')
  const [gold, setGold] = useState(0)
  const [gems, setGems] = useState(0)
  const [odds, setOdds] = useState(null)
  const [goldOdds, setGoldOdds] = useState(null)
  const [equipGoldOdds, setEquipGoldOdds] = useState(null)
  const [equipGemOdds, setEquipGemOdds] = useState(null)
  const [pityInfo, setPityInfo] = useState(null)
  const [pulling, setPulling] = useState(false)
  const [redeeming, setRedeeming] = useState(false)
  const [redeemingEquip, setRedeemingEquip] = useState(false)
  // Hero and equipment results are tracked separately rather than one shared
  // array — pulling one no longer wipes the other's results off screen.
  const [heroResults, setHeroResults] = useState([])
  const [equipResults, setEquipResults] = useState([])
  const [heroOddsCurrency, setHeroOddsCurrency] = useState('gem')
  const [equipOddsCurrency, setEquipOddsCurrency] = useState('gem')
  const [error, setError] = useState(null)
  const [expandedId, setExpandedId] = useState(null)
  const [showAnimation, setShowAnimation] = useState(false)
  const [fairyGender, setFairyGender] = useState('female')
  const [fairyTip, setFairyTip] = useState({ show: false, message: '' })

  useEffect(() => {
    refreshData()
  }, [])

  async function refreshData() {
    getBase().then(b => { setGold(b.gold); setGems(b.gems || 0); setFairyGender(b.fairy_gender) })
    getOdds().then(setOdds)
    getOdds('gold').then(setGoldOdds)
    getEquipmentOdds('gold').then(setEquipGoldOdds)
    getEquipmentOdds('gem').then(setEquipGemOdds)
    getPityInfo().then(setPityInfo)
  }

  async function doPull(count, currency = 'gem') {
    setPulling(true)
    setError(null)
    setHeroResults([])
    try {
      // Portraits are always generated — this stopped being a player choice.
      const data = await pullHeroes(count, true, currency)
      setHeroResults(data.pulled)
      const cost = count * (currency === 'gold' ? 250 : 100)
      if (currency === 'gold') setGold(g => g - cost)
      else setGems(g => g - cost)
      setShowAnimation(true)

      if (!localStorage.getItem('seen_noncombat_tip')) {
        const noncombat = data.pulled.find(h => NON_COMBAT_CLASSES.includes(h.hero_class))
        if (noncombat) {
          localStorage.setItem('seen_noncombat_tip', 'true')
          setFairyTip({
            show: true,
            message: `${noncombat.name} is a ${noncombat.hero_class} — not a combat class! Assign them to a Facility back at your Base instead of deploying them to the Tower.`
          })
          setTimeout(() => setFairyTip(t => ({ ...t, show: false })), 12000)
        }
      }
      await refreshData()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setError(e.message)
    } finally {
      setPulling(false)
    }
  }

  async function doPullEquipment(count, currency = 'gold') {
    setPulling(true)
    setError(null)
    setEquipResults([])
    try {
      const data = await pullEquipment(count, currency)
      setEquipResults(data.results.map(e => ({...e, is_equipment: true})))
      const cost = count * (currency === 'gem' ? 150 : 500)
      if (currency === 'gem') setGems(g => g - cost)
      else setGold(g => g - cost)
      await refreshData()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setError(e.message)
    } finally {
      setPulling(false)
    }
  }

  async function doSpark() {
    if (!(await confirmDialog(`Redeem ${pityInfo.spark_threshold} sparks for a guaranteed 5★ hero?`))) return
    setRedeeming(true)
    setError(null)
    try {
      const data = await redeemSpark()
      setHeroResults([data.hero])
      await refreshData()
    } catch (e) {
      setError(e.message)
    } finally {
      setRedeeming(false)
    }
  }

  async function doEquipSpark() {
    if (!(await confirmDialog(`Redeem ${pityInfo.equip_spark_threshold} sparks for a guaranteed A-tier item?`))) return
    setRedeemingEquip(true)
    setError(null)
    try {
      const data = await redeemEquipSpark()
      setEquipResults([{ ...data.equipment, is_equipment: true }])
      await refreshData()
    } catch (e) {
      setError(e.message)
    } finally {
      setRedeemingEquip(false)
    }
  }

  const results = activeTab === 'equipment' ? equipResults : heroResults

  return (
    <div className="page">
      <FairyTip
        show={fairyTip.show}
        message={fairyTip.message}
        fairyGender={fairyGender}
        onDismiss={() => setFairyTip(t => ({ ...t, show: false }))}
      />

      {showAnimation && results.length > 0 && (
        <SummoningOverlay
          results={results}
          onComplete={() => setShowAnimation(false)}
        />
      )}

      {!showAnimation && (
        <>
          <div className="section-header">Summoning Gate</div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', margin: '1rem 0' }}>
            <button
              className="btn"
              onClick={() => setActiveTab('heroes')}
              style={{ padding: '0.6rem 1.5rem', fontSize: '1rem', fontFamily: 'Cinzel, serif', border: activeTab === 'heroes' ? '2px solid var(--gold)' : '1px solid var(--border)', opacity: activeTab === 'heroes' ? 1 : 0.6 }}
            >Heroes</button>
            <button
              className="btn"
              onClick={() => setActiveTab('equipment')}
              style={{ padding: '0.6rem 1.5rem', fontSize: '1rem', fontFamily: 'Cinzel, serif', border: activeTab === 'equipment' ? '2px solid var(--gold)' : '1px solid var(--border)', opacity: activeTab === 'equipment' ? 1 : 0.6 }}
            >Equipment</button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '800px', margin: '0 auto' }}>

        {activeTab === 'heroes' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
          <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '1rem' }}>
              <div className="section-header" style={{ margin: 0, border: 'none', paddingBottom: 0, color: 'var(--gold)' }}>Premium Summon</div>
              <div className="text-dim" style={{ fontSize: '0.85rem' }}>Better odds · builds Sparks · you have <span style={{ color: '#00ffff' }}>{gems.toLocaleString()} <GameIcon name="gem" size={14} /></span></div>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <SummonButton title="Summon 1x" cost={100} currency="gem" balance={gems} premium
                onClick={() => doPull(1, 'gem')} disabled={pulling || gems < 100} pulling={pulling} />
              <SummonButton title="Summon 10x" cost={1000} currency="gem" balance={gems} premium
                onClick={() => doPull(10, 'gem')} disabled={pulling || gems < 1000} pulling={pulling} />
            </div>
            {gems < 100 && (
              <div className="text-dim" style={{ marginTop: '0.8rem', fontSize: '0.85rem', fontStyle: 'italic', textAlign: 'center' }}>
                Out of gems — claim Achievement rewards and set new Tower floor records to earn more.
              </div>
            )}
          </div>

          <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '1rem' }}>
              <div className="section-header" style={{ margin: 0, border: 'none', paddingBottom: 0 }}>Standard Summon</div>
              <div className="text-dim" style={{ fontSize: '0.85rem' }}>you have <span className="text-gold">{gold.toLocaleString()} <GameIcon name="gold_coin" size={14} /></span></div>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <SummonButton title="Summon 1x" cost={250} currency="gold" balance={gold}
                onClick={() => doPull(1, 'gold')} disabled={pulling || gold < 250} pulling={pulling} />
              <SummonButton title="Summon 10x" cost={2500} currency="gold" balance={gold}
                onClick={() => doPull(10, 'gold')} disabled={pulling || gold < 2500} pulling={pulling} />
            </div>
          </div>

          {(odds || goldOdds) && (
            <Collapsible
              title="Pull Rates"
              headerExtra={
                <div style={{ display: 'flex', gap: '0.3rem' }}>
                  <button className="btn" onClick={() => setHeroOddsCurrency('gem')} style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem', opacity: heroOddsCurrency === 'gem' ? 1 : 0.5 }}>Gem</button>
                  <button className="btn" onClick={() => setHeroOddsCurrency('gold')} style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem', opacity: heroOddsCurrency === 'gold' ? 1 : 0.5 }}>Gold</button>
                </div>
              }
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {Object.entries((heroOddsCurrency === 'gold' ? goldOdds : odds) || {}).map(([star, data]) => {
                  const numStar = Number(star);
                  const isRainbow = numStar === 7;
                  return (
                    <div key={star} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem', padding: '0.4rem 1rem', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)', borderRadius: 4 }}>
                      <span className={isRainbow ? 'rainbow-text' : `birth-star-${star}`} style={{ color: isRainbow ? undefined : `var(--star${star})`, textShadow: numStar >= 5 ? '0 0 5px currentColor' : 'none' }}>
                        {'★'.repeat(numStar)}
                      </span>
                      <span className="text-dim" style={{ fontFamily: 'monospace', fontSize: '1.1rem' }}>
                        {Number(data.percent).toFixed(3)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </Collapsible>
          )}

          {/* Pity counter is intentionally hidden from the player — showing
              an exact "guaranteed in N pulls" countdown makes the gacha
              feel mechanical/goofy rather than exciting. It still runs
              server-side (routers/gacha.py), just not surfaced here.
              Sparks stay visible below since that's a player-facing
              strategic currency, not a hidden-RNG safety net. */}

          {pityInfo && (
            <div className="card" style={{ marginTop: '1rem' }}>
              <div className="section-header" style={{ marginBottom: '1rem', textAlign: 'center' }}>Sparks (Gem Summons Only)</div>
              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '0.8rem' }}>
                  <div className="text-dim" style={{ fontSize: '1.1rem' }}>Sparks</div>
                  <div style={{ fontSize: '1.5rem', color: 'var(--star5)', fontFamily: 'Cinzel, serif' }}>
                    {pityInfo.spark_points} <span className="text-dim" style={{ fontSize: '1rem' }}>/ {pityInfo.spark_threshold}</span>
                  </div>
                </div>
                <div style={{ width: '100%', height: '8px', background: 'var(--bg)', borderRadius: '4px', overflow: 'hidden', marginBottom: '1.5rem', border: '1px solid var(--border)' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(100, (pityInfo.spark_points / pityInfo.spark_threshold) * 100)}%`,
                    background: 'var(--star5)',
                    boxShadow: '0 0 10px var(--star5)',
                    transition: 'width 0.5s ease-out'
                  }} />
                </div>

                <button
                  className="btn"
                  style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', background: pityInfo.spark_points >= pityInfo.spark_threshold ? 'rgba(201, 168, 76, 0.2)' : 'rgba(255,255,255,0.05)', color: pityInfo.spark_points >= pityInfo.spark_threshold ? 'var(--star5)' : 'var(--text-dim)', border: `2px solid ${pityInfo.spark_points >= pityInfo.spark_threshold ? 'var(--star5)' : 'var(--border)'}`, boxShadow: pityInfo.spark_points >= pityInfo.spark_threshold ? '0 0 15px rgba(201,168,76,0.3)' : 'none' }}
                  onClick={doSpark}
                  disabled={redeeming || pulling || pityInfo.spark_points < pityInfo.spark_threshold}
                >
                  {redeeming ? 'Redeeming...' : `Redeem 5★ (${pityInfo.spark_threshold} Sparks)`}
                </button>
              </div>
            </div>
          )}
        </div>
        )}

        {activeTab === 'equipment' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
          <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '1rem' }}>
              <div className="section-header" style={{ margin: 0, border: 'none', paddingBottom: 0, color: 'var(--gold)' }}>Premium Forge</div>
              <div className="text-dim" style={{ fontSize: '0.85rem' }}>Better odds · builds Sparks · you have <span style={{ color: '#00ffff' }}>{gems.toLocaleString()} <GameIcon name="gem" size={14} /></span></div>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <SummonButton title="Summon 1x" cost={150} currency="gem" balance={gems} premium
                onClick={() => doPullEquipment(1, 'gem')} disabled={pulling || gems < 150} pulling={pulling} />
              <SummonButton title="Summon 10x" cost={1500} currency="gem" balance={gems} premium
                onClick={() => doPullEquipment(10, 'gem')} disabled={pulling || gems < 1500} pulling={pulling} />
            </div>
            {gems < 150 && (
              <div className="text-dim" style={{ marginTop: '0.8rem', fontSize: '0.85rem', fontStyle: 'italic', textAlign: 'center' }}>
                Out of gems — claim Achievement rewards and set new Tower floor records to earn more.
              </div>
            )}
          </div>

          <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '1rem' }}>
              <div className="section-header" style={{ margin: 0, border: 'none', paddingBottom: 0 }}>Standard Forge</div>
              <div className="text-dim" style={{ fontSize: '0.85rem' }}>you have <span className="text-gold">{gold.toLocaleString()} <GameIcon name="gold_coin" size={14} /></span></div>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <SummonButton title="Summon 1x" cost={500} currency="gold" balance={gold}
                onClick={() => doPullEquipment(1, 'gold')} disabled={pulling || gold < 500} pulling={pulling} />
              <SummonButton title="Summon 10x" cost={5000} currency="gold" balance={gold}
                onClick={() => doPullEquipment(10, 'gold')} disabled={pulling || gold < 5000} pulling={pulling} />
            </div>
          </div>

          {(equipGoldOdds || equipGemOdds) && (
            <Collapsible
              title="Equipment Rates"
              headerExtra={
                <div style={{ display: 'flex', gap: '0.3rem' }}>
                  <button className="btn" onClick={() => setEquipOddsCurrency('gem')} style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem', opacity: equipOddsCurrency === 'gem' ? 1 : 0.5 }}>Gem</button>
                  <button className="btn" onClick={() => setEquipOddsCurrency('gold')} style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem', opacity: equipOddsCurrency === 'gold' ? 1 : 0.5 }}>Gold</button>
                </div>
              }
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {(equipOddsCurrency === 'gold' ? equipGoldOdds : equipGemOdds)?.map((tier, idx) => {
                  const midGrade = tier.grades[Math.floor(tier.grades.length / 2)]
                  const tooltip = (tier.breakdown || []).map(b => `${b.grade}: ${b.percent}%`).join('\n')
                  return (
                    <div
                      key={idx}
                      title={tooltip}
                      style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1rem', padding: '0.4rem 1rem', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)', borderRadius: 4, cursor: 'help' }}
                    >
                      <span className="text-hi">{midGrade}-Tier <span className="text-dim" style={{ fontSize: '0.75rem' }}>[?]</span></span>
                      <span className="text-dim" style={{ fontFamily: 'monospace' }}>{tier.percent.toFixed(2)}%</span>
                    </div>
                  )
                })}
              </div>
            </Collapsible>
          )}

          {pityInfo && (
            <div className="card" style={{ marginTop: '1rem' }}>
              <div className="section-header" style={{ marginBottom: '1rem', textAlign: 'center' }}>Sparks (Gem Summons Only)</div>
              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '0.8rem' }}>
                  <div className="text-dim" style={{ fontSize: '1.1rem' }}>Sparks</div>
                  <div style={{ fontSize: '1.5rem', color: 'var(--star5)', fontFamily: 'Cinzel, serif' }}>
                    {pityInfo.equip_spark_points} <span className="text-dim" style={{ fontSize: '1rem' }}>/ {pityInfo.equip_spark_threshold}</span>
                  </div>
                </div>
                <div style={{ width: '100%', height: '8px', background: 'var(--bg)', borderRadius: '4px', overflow: 'hidden', marginBottom: '1.5rem', border: '1px solid var(--border)' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(100, (pityInfo.equip_spark_points / pityInfo.equip_spark_threshold) * 100)}%`,
                    background: 'var(--star5)',
                    boxShadow: '0 0 10px var(--star5)',
                    transition: 'width 0.5s ease-out'
                  }} />
                </div>

                <button
                  className="btn"
                  style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', background: pityInfo.equip_spark_points >= pityInfo.equip_spark_threshold ? 'rgba(201, 168, 76, 0.2)' : 'rgba(255,255,255,0.05)', color: pityInfo.equip_spark_points >= pityInfo.equip_spark_threshold ? 'var(--star5)' : 'var(--text-dim)', border: `2px solid ${pityInfo.equip_spark_points >= pityInfo.equip_spark_threshold ? 'var(--star5)' : 'var(--border)'}`, boxShadow: pityInfo.equip_spark_points >= pityInfo.equip_spark_threshold ? '0 0 15px rgba(201,168,76,0.3)' : 'none' }}
                  onClick={doEquipSpark}
                  disabled={redeemingEquip || pulling || pityInfo.equip_spark_points < pityInfo.equip_spark_threshold}
                >
                  {redeemingEquip ? 'Redeeming...' : `Redeem A-Tier Item (${pityInfo.equip_spark_threshold} Sparks)`}
                </button>
              </div>
            </div>
          )}
        </div>
        )}

          {error && (
            <div className="text-red text-center" style={{ marginTop: '0.5rem', fontSize: '1.1rem' }}>{error}</div>
          )}
      </div>

      {/* Results — hero and equipment pulls keep separate history, shown
          according to whichever tab is active. */}
      {results.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <div className="section-header" style={{ marginBottom: '1rem' }}>Summoned</div>
          <div className="hero-grid">
            {results.map((item, idx) => {
              if (item.is_equipment) {
                return (
                  <div key={idx} className="card" style={{ border: '1px solid var(--border)', textAlign: 'center', padding: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <EquipmentTypeIcon item={item} fontSize="3rem" />
                    </div>
                    <div style={{ fontSize: '1.2rem', fontFamily: 'Cinzel, serif', fontWeight: 'bold' }}>{item.name}</div>
                    <div style={{ fontSize: '1rem', marginTop: '0.5rem', color: 'var(--star5)' }}>{item.rarity} Rank</div>
                  </div>
                )
              }
              return (
                <div key={item.id}>
                  <HeroCard hero={item} onClick={() => setExpandedId(item.id)} />
                  {item.chatter_line && (
                    <div style={{ marginTop: '0.4rem', textAlign: 'center', fontStyle: 'italic', fontSize: '0.85rem', color: 'var(--gold)' }}>
                      "{item.chatter_line}"
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {expandedId && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.85)', zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(5px)'
        }} onClick={() => setExpandedId(null)}>
          <div style={{ width: '1000px', maxWidth: '95vw', maxHeight: '90vh', overflowY: 'auto', borderRadius: '8px' }} onClick={e => e.stopPropagation()}>
            <HeroCard
              hero={heroResults.find(h => h.id === expandedId)}
              showFull={true}
            />
          </div>
        </div>
      )}
        </>
      )}
    </div>
  )
}
