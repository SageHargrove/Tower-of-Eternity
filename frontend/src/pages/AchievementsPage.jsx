import React, { useState, useEffect } from 'react'
import PageTitle from '../components/PageTitle'
import { getAchievements, claimAchievement, getRites, claimRite } from '../api/client'

const CATEGORY_ORDER = ['Tower', 'Summoning', 'Roster', 'Combat', 'Economy', 'Equipment', 'Arena']

// Ticket rewards render as bordered chips — 7★ slides the rainbow (spec),
// lower stars borrow their rarity color.
const TICKET_COLORS = { 3: '#1e90ff', 4: '#b84dff', 5: '#ffb300', 6: '#ff3333' }
function TicketChip({ label }) {
  const star = Number(String(label).match(/^(\d)/)?.[1]) || 0
  if (star === 7) {
    return (
      <span className="rainbow-text" style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 11, letterSpacing: '.14em', padding: '3px 9px', border: '1px solid rgba(255,255,255,.4)' }}>
        7★ TICKET
      </span>
    )
  }
  const c = TICKET_COLORS[star] || 'var(--gold-hi)'
  return (
    <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, letterSpacing: '.14em', color: c, border: `1px solid ${c}80`, padding: '3px 9px' }}>
      {star ? `${star}★ TICKET` : String(label).toUpperCase()}
    </span>
  )
}

// Reward cluster per spec: violet diamond + gem count in lavender, gold
// diamond + gold count, ticket chips. No PNG art.
function rewardText(reward) {
  const parts = []
  if (reward.gems) parts.push(
    <span key="gems" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
      <span style={{ width: 8, height: 8, transform: 'rotate(45deg)', display: 'inline-block', flex: 'none', background: 'var(--violet)', boxShadow: '0 0 8px var(--violet)' }} />
      <span style={{ fontFamily: "'Cinzel',serif", fontSize: 13, color: '#c8a9f5' }}>{reward.gems}</span>
    </span>
  )
  if (reward.gold) parts.push(
    <span key="gold" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
      <span style={{ width: 8, height: 8, transform: 'rotate(45deg)', display: 'inline-block', flex: 'none', background: 'var(--gold)' }} />
      <span style={{ fontFamily: "'Cinzel',serif", fontSize: 13, color: 'var(--gold-hi)' }}>{reward.gold}</span>
    </span>
  )
  if (reward.summon_ticket) parts.push(<TicketChip key="ticket" label={reward.summon_ticket} />)
  return <span style={{ display: 'inline-flex', gap: 12, alignItems: 'center' }}>{parts}</span>
}

export default function AchievementsPage({ onGoldChange }) {
  const [achievements, setAchievements] = useState(null)
  const [loading, setLoading] = useState(true)
  const [claiming, setClaiming] = useState(null)
  const [toast, setToast] = useState(null)
  const [activeCategory, setActiveCategory] = useState(null)
  const [mode, setMode] = useState('dailies') // 'dailies' | 'weeklies' | 'achievements'
  const [rites, setRites] = useState(null)
  const [claimingRite, setClaimingRite] = useState(null)

  function loadRites() {
    getRites().then(setRites).catch(() => setRites(null))
  }
  useEffect(() => { loadRites() }, [])

  async function handleClaimRite(q) {
    setClaimingRite(q.id)
    try {
      const res = await claimRite(q.id)
      setToast(<span>Claimed! {rewardText(res.reward)}</span>)
      loadRites()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setToast(e.message)
    } finally {
      setClaimingRite(null)
      setTimeout(() => setToast(null), 3000)
    }
  }

  useEffect(() => { refresh() }, [])

  async function refresh() {
    setLoading(true)
    try {
      const res = await getAchievements()
      setAchievements(res.achievements || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function handleClaim(id) {
    setClaiming(id)
    try {
      const res = await claimAchievement(id)
      setToast(<span>Claimed! {rewardText(res.reward)}</span>)
      await refresh()
      if (onGoldChange) onGoldChange()
    } catch (e) {
      setToast(e.message)
    } finally {
      setClaiming(null)
      setTimeout(() => setToast(null), 3000)
    }
  }

  async function handleClaimAllRites(list) {
    const claimable = (list || []).filter(q => q.complete && !q.claimed)
    if (claimable.length === 0) return
    setClaimingRite('all')
    const total = { gems: 0, gold: 0, summon_ticket: 0 }
    let claimed = 0
    try {
      for (const q of claimable) {
        const res = await claimRite(q.id)
        claimed++
        for (const k of Object.keys(total)) total[k] += res.reward?.[k] || 0
      }
      setToast(<span>Claimed {claimed} rite{claimed === 1 ? '' : 's'}! {rewardText(total)}</span>)
    } catch (e) {
      setToast(claimed > 0 ? `Claimed ${claimed} before an error: ${e.message}` : e.message)
    } finally {
      setClaimingRite(null)
      loadRites()
      if (onGoldChange) onGoldChange()
      setTimeout(() => setToast(null), 4000)
    }
  }

  async function handleClaimAll() {
    const claimable = (achievements || []).filter(a => a.complete && !a.claimed)
    if (claimable.length === 0) return
    setClaiming('all')
    // Tally the combined haul so the toast reports one total instead of
    // flashing per-achievement.
    const total = { gems: 0, gold: 0, summon_ticket: 0 }
    let claimed = 0
    try {
      for (const a of claimable) {
        const res = await claimAchievement(a.id)
        claimed++
        for (const k of Object.keys(total)) total[k] += res.reward?.[k] || 0
      }
      setToast(<span>Claimed {claimed} achievement{claimed === 1 ? '' : 's'}! {rewardText(total)}</span>)
    } catch (e) {
      setToast(claimed > 0 ? `Claimed ${claimed} before an error: ${e.message}` : e.message)
    } finally {
      setClaiming(null)
      await refresh()
      if (onGoldChange) onGoldChange()
      setTimeout(() => setToast(null), 4000)
    }
  }

  if (loading || !achievements) return <div className="page text-dim">Loading Achievements...</div>

  const claimedCount = achievements.filter(a => a.claimed).length
  const claimableCount = achievements.filter(a => a.complete && !a.claimed).length
  const byCategory = {}
  for (const a of achievements) {
    if (!byCategory[a.category]) byCategory[a.category] = []
    byCategory[a.category].push(a)
  }
  const categories = CATEGORY_ORDER.filter(c => byCategory[c])
  const cat = activeCategory && byCategory[activeCategory] ? activeCategory : categories[0]
  const rows = byCategory[cat] || []

  return (
    <div className="page">
      {toast && (
        <div style={{ position: 'fixed', top: '6rem', right: '2rem', background: 'rgba(8,6,14,0.95)', border: '1px solid var(--gold)', color: 'var(--gold-hi)', padding: '0.8rem 1.2rem', clipPath: 'polygon(0 0,100% 0,100% 100%,10px 100%)', zIndex: 1000 }}>
          {toast}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '2.5rem', alignItems: 'start' }}>

        {/* ============ LEFT CONSOLE ============ */}
        {/* Context-aware: the category ledger + achievement CLAIM ALL only make
            sense on the ACHIEVEMENTS tab. Dailies/Weeklies get their own rite
            summary instead of the (wrong) achievement category filters. */}
        <div className="ent-1" style={{ display: 'flex', flexDirection: 'column' }}>
          <PageTitle eyebrow="Renown" title="DEEDS" ghost="GLORY" compact />

          {mode === 'achievements' ? (
            <>
              <button className="btn btn-gold" onClick={handleClaimAll}
                disabled={claimableCount === 0 || claiming === 'all'}
                style={{ padding: '13px 0', letterSpacing: '.22em', textAlign: 'center',
                  animation: claimableCount > 0 ? 'claim-glow 3s ease-in-out infinite' : undefined }}>
                {claiming === 'all' ? 'CLAIMING…' : `CLAIM ALL · ${claimableCount} READY`}
              </button>
              <div className="text-dim" style={{ fontSize: '0.8rem', margin: '0.6rem 0 1.2rem', letterSpacing: '.02em' }}>
                {claimedCount} / {achievements.length} claimed
              </div>

              {/* category ledger */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {categories.map(c => {
                  const list = byCategory[c]
                  const done = list.filter(a => a.claimed).length
                  const ready = list.filter(a => a.complete && !a.claimed).length
                  const active = c === cat
                  return (
                    <div key={c} onClick={() => setActiveCategory(c)}
                      style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '9px 14px', fontFamily: 'Cinzel, serif', letterSpacing: '.2em', fontSize: 12, textTransform: 'uppercase',
                        color: active ? '#0a0710' : 'var(--text-dim)', fontWeight: active ? 700 : 400,
                        background: active ? 'linear-gradient(120deg,var(--lavender),var(--violet-deep))' : 'transparent',
                        clipPath: active ? 'polygon(8px 0,100% 0,calc(100% - 8px) 100%,0 100%)' : undefined }}>
                      <span>{c}</span>
                      <span style={{ color: active ? '#0a0710' : ready > 0 ? 'var(--gold-hi)' : 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 6 }}>
                        {ready > 0 && !active && <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--gold-hi)', boxShadow: '0 0 6px var(--gold-hi)', animation: 'pulse-live 2s ease-in-out infinite' }} />}
                        {done}/{list.length}
                      </span>
                    </div>
                  )
                })}
              </div>
            </>
          ) : (() => {
            const list = mode === 'dailies' ? (rites?.dailies || []) : (rites?.weeklies || [])
            const riteReady = list.filter(q => q.complete && !q.claimed).length
            const riteClaimed = list.filter(q => q.claimed).length
            const resetSec = mode === 'dailies' ? rites?.daily_resets_in_seconds : rites?.weekly_resets_in_seconds
            const resetLabel = resetSec != null ? `${Math.floor(resetSec / 3600)}h ${String(Math.floor((resetSec % 3600) / 60)).padStart(2, '0')}m` : '—'
            return (
              <>
                <button className="btn btn-gold" onClick={() => handleClaimAllRites(list)}
                  disabled={riteReady === 0 || claimingRite === 'all'}
                  style={{ padding: '13px 0', letterSpacing: '.22em', textAlign: 'center',
                    animation: riteReady > 0 ? 'claim-glow 3s ease-in-out infinite' : undefined }}>
                  {claimingRite === 'all' ? 'CLAIMING…' : `CLAIM ALL · ${riteReady} READY`}
                </button>
                <div className="text-dim" style={{ fontSize: '0.8rem', margin: '0.6rem 0 1.2rem', letterSpacing: '.02em' }}>
                  {riteClaimed} / {list.length} claimed today
                </div>
                <div style={{ border: '1px solid rgba(184,151,98,.25)', background: 'rgba(12,7,24,.4)', padding: '14px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                    <span style={{ width: 8, height: 8, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
                    <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: 11, color: 'var(--gold)' }}>
                      {mode === 'dailies' ? 'DAILY RITES' : 'WEEKLY RITES'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
                    <span className="ilm-micro" style={{ color: 'var(--muted)' }}>RENEWS IN</span>
                    <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 17, color: 'var(--text-hi)' }}>{resetLabel}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span className="ilm-micro" style={{ color: 'var(--muted)' }}>READY TO CLAIM</span>
                    <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 17, color: riteReady > 0 ? 'var(--gold-hi)' : 'var(--muted)' }}>{riteReady}</span>
                  </div>
                  <div style={{ fontStyle: 'italic', fontSize: 12.5, color: 'var(--muted)', marginTop: 12, lineHeight: 1.5 }}>
                    {mode === 'dailies' ? 'Rites renew at dawn — claim them before they reset.' : 'Weekly rites reset with the new week.'}
                  </div>
                </div>
              </>
            )
          })()}
        </div>

        {/* ============ RIGHT: DEEDS LIST ============ */}
        <div className="ent-2">
          {/* DAILIES / WEEKLIES / ACHIEVEMENTS separation (spec). The keepers
              haven't shipped daily/weekly rites server-side yet — those tabs
              show an honest quiet state until they do. */}
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 26, borderBottom: '1px solid rgba(184,151,98,.2)', marginBottom: 16 }}>
            {[['dailies', 'DAILIES'], ['weeklies', 'WEEKLIES'], ['achievements', 'ACHIEVEMENTS']].map(([id, label]) => {
              const ready = id === 'dailies' ? (rites?.dailies || []).filter(q => q.complete && !q.claimed).length
                : id === 'weeklies' ? (rites?.weeklies || []).filter(q => q.complete && !q.claimed).length : 0
              return (
                <button key={id} onClick={() => setMode(id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'Cinzel, serif', letterSpacing: '.22em', fontSize: 12,
                    fontWeight: mode === id ? 700 : 500, color: mode === id ? 'var(--text-hi)' : 'var(--muted)',
                    borderBottom: mode === id ? '2px solid var(--gold)' : '2px solid transparent', padding: '0 0 8px',
                    display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  {label}
                  {ready > 0 && <span style={{ fontFamily: "'Cormorant Garamond',serif", fontStyle: 'italic', letterSpacing: 0, fontSize: 12, color: '#8fbf9f', textTransform: 'none' }}>{ready} ready</span>}
                </button>
              )
            })}
            <span style={{ flex: 1 }} />
            <span style={{ fontStyle: 'italic', fontSize: 13, color: 'var(--muted)', paddingBottom: 8 }}>
              {mode === 'achievements' ? 'Deeds are forever' : 'Rites renew at dawn'}
            </span>
          </div>

          {mode !== 'achievements' && (() => {
            const list = mode === 'dailies' ? (rites?.dailies || []) : (rites?.weeklies || [])
            const resetSec = mode === 'dailies' ? rites?.daily_resets_in_seconds : rites?.weekly_resets_in_seconds
            const resetLabel = resetSec != null ? `resets in ${Math.floor(resetSec / 3600)}h ${String(Math.floor((resetSec % 3600) / 60)).padStart(2, '0')}m` : ''
            if (!rites) {
              return (
                <div style={{ fontStyle: 'italic', color: 'var(--muted)', padding: '2rem 0', textAlign: 'center' }}>
                  The keepers are still posting the rites…
                </div>
              )
            }
            return (
              <>
                {/* ◆ DAILY RITES ——— resets in Xh Ym */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
                  <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.3em', fontSize: 11, color: 'var(--gold)' }}>
                    {mode === 'dailies' ? 'DAILY RITES' : 'WEEKLY RITES'}
                  </span>
                  <span style={{ height: 1, flex: 1, background: 'rgba(184,151,98,.2)' }} />
                  <span style={{ fontStyle: 'italic', fontSize: 13, color: 'var(--muted)' }}>{resetLabel}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {list.map((q, ri) => {
                    const claimable = q.complete && !q.claimed
                    return (
                      <div key={q.id} style={{
                        display: 'flex', alignItems: 'center', gap: 16, padding: '13px 18px',
                        clipPath: 'polygon(0 0,100% 0,calc(100% - 12px) 100%,0 100%)',
                        background: claimable ? 'linear-gradient(120deg,rgba(184,151,98,.1),rgba(12,7,24,.55))' : q.claimed ? 'rgba(12,7,24,.3)' : 'rgba(12,7,24,.45)',
                        border: `1px solid ${claimable ? 'rgba(184,151,98,.55)' : q.claimed ? 'rgba(184,151,98,.18)' : 'rgba(150,110,230,.3)'}`,
                        opacity: q.claimed ? 0.55 : 1,
                        animation: claimable ? `claim-glow 3s ease-in-out ${(ri % 3) * 0.8}s infinite` : undefined,
                      }}>
                        <span style={{ width: 34, height: 34, transform: 'rotate(45deg)', flex: 'none',
                          border: `1px solid ${claimable ? '#d8bb84' : q.claimed ? 'rgba(184,151,98,.4)' : 'rgba(150,110,230,.5)'}`,
                          background: claimable ? '#1c1030' : '#140b22',
                          display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <span style={{ transform: 'rotate(-45deg)', fontSize: q.claimed ? 13 : 14, color: q.claimed ? '#8fbf9f' : claimable ? '#d8bb84' : '#c8a9f5' }}>
                            {q.claimed ? '✓' : claimable ? '✦' : '⟡'}
                          </span>
                        </span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.12em', fontSize: 15, color: q.claimed ? '#c9bfa8' : claimable ? 'var(--text-hi)' : '#e7ddc9' }}>
                            {q.name}
                          </div>
                          {q.complete || q.target <= 1 ? (
                            <div style={{ fontSize: 15, fontStyle: 'italic', color: 'var(--muted)' }}>{q.desc}</div>
                          ) : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 6 }}>
                              <div style={{ flex: 1, height: 5, background: 'rgba(124,58,214,.15)', border: '1px solid rgba(150,110,230,.3)' }}>
                                <div style={{ width: `${Math.min(100, (q.progress / q.target) * 100)}%`, height: '100%', background: 'linear-gradient(90deg,#8b46d6,#c8a9f5)' }} />
                              </div>
                              <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, color: 'var(--muted)' }}>
                                {q.progress}<span style={{ color: '#6f628c' }}>/{q.target}</span>
                              </span>
                            </div>
                          )}
                        </div>
                        {rewardText(q.reward)}
                        {q.claimed ? (
                          <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: 11, color: '#8fbf9f' }}>CLAIMED</span>
                        ) : q.complete ? (
                          <button disabled={claimingRite === q.id} onClick={() => handleClaimRite(q)}
                            style={{ cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 12, color: '#0a0710', background: 'linear-gradient(120deg,#ffd88a,#b89762)', border: 'none', padding: '8px 18px', clipPath: 'polygon(8px 0,100% 0,calc(100% - 8px) 100%,0 100%)' }}>
                            {claimingRite === q.id ? '…' : 'CLAIM'}
                          </button>
                        ) : null}
                      </div>
                    )
                  })}
                </div>
              </>
            )
          })()}

          {mode === 'achievements' && (<>
          {/* section header — ◆ {CAT} DEEDS ——— */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
            <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.3em', fontSize: 11, color: 'var(--gold)' }}>{cat.toUpperCase()} DEEDS</span>
            <span style={{ height: 1, flex: 1, background: 'rgba(184,151,98,.2)' }} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {rows.map((a, ri) => {
              const pct = Math.min(100, (a.progress / a.target) * 100)
              const claimable = a.complete && !a.claimed
              return (
                <div key={a.id} style={{
                  display: 'flex', alignItems: 'center', gap: 16, padding: '13px 18px',
                  clipPath: 'polygon(0 0,100% 0,calc(100% - 12px) 100%,0 100%)',
                  background: claimable ? 'linear-gradient(120deg,rgba(184,151,98,.1),rgba(12,7,24,.55))' : a.claimed ? 'rgba(12,7,24,.3)' : 'rgba(12,7,24,.45)',
                  border: `1px solid ${claimable ? 'rgba(184,151,98,.55)' : a.claimed ? 'rgba(184,151,98,.18)' : 'rgba(150,110,230,.3)'}`,
                  opacity: a.claimed ? 0.55 : 1,
                  animation: claimable ? `claim-glow 3s ease-in-out ${(ri % 3) * 0.8}s infinite` : undefined,
                }}>
                  <span style={{ width: 34, height: 34, transform: 'rotate(45deg)', flex: 'none',
                    border: `1px solid ${claimable ? '#d8bb84' : a.claimed ? 'rgba(184,151,98,.4)' : 'rgba(150,110,230,.5)'}`,
                    background: a.claimed || !claimable ? '#140b22' : '#1c1030',
                    display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ transform: 'rotate(-45deg)', fontSize: a.claimed ? 13 : 14, color: a.claimed ? '#8fbf9f' : claimable ? '#d8bb84' : '#c8a9f5' }}>
                      {a.claimed ? '✓' : claimable ? '✦' : '⟡'}
                    </span>
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.12em', fontSize: 15, color: a.claimed ? '#c9bfa8' : claimable ? 'var(--text-hi)' : '#e7ddc9', textTransform: 'uppercase' }}>
                      {a.name}
                    </div>
                    {a.complete ? (
                      <div style={{ fontSize: 15, fontStyle: 'italic', color: 'var(--muted)' }}>{a.desc}</div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 6 }}>
                        <div style={{ flex: 1, height: 5, background: 'rgba(124,58,214,.15)', border: '1px solid rgba(150,110,230,.3)' }}>
                          <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg,#8b46d6,#c8a9f5)' }} />
                        </div>
                        <span style={{ fontFamily: "'Cinzel',serif", fontSize: 11, color: 'var(--muted)' }}>
                          {a.progress.toLocaleString()}<span style={{ color: '#6f628c' }}>/{a.target.toLocaleString()}</span>
                        </span>
                      </div>
                    )}
                  </div>
                  {rewardText(a.reward)}
                  {a.claimed ? (
                    <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: 11, color: '#8fbf9f' }}>CLAIMED</span>
                  ) : a.complete ? (
                    <button disabled={claiming === a.id} onClick={() => handleClaim(a.id)}
                      style={{ cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 12, color: '#0a0710', background: 'linear-gradient(120deg,#ffd88a,#b89762)', border: 'none', padding: '8px 18px', clipPath: 'polygon(8px 0,100% 0,calc(100% - 8px) 100%,0 100%)' }}>
                      {claiming === a.id ? '…' : 'CLAIM'}
                    </button>
                  ) : null}
                </div>
              )
            })}
          </div>
          </>)}
        </div>
      </div>
    </div>
  )
}
