/*
 * DAILY GATES / Daily Dungeons — live (mockup "Death Ceremony -
 * Illuminated.dc.html", screen "Daily Dungeons"). Three keyed gates a day,
 * rewards scale with the highest tower floor; keys return at dawn (UTC
 * midnight — see /base/daily_dungeon/status). The mock's third gate is the
 * Sanctum of Seals; live content ships the Wellspring of Aether until the
 * seals system exists.
 */
import React, { useState, useEffect } from 'react'
import { getDailyDungeonStatus, runDailyDungeon } from '../api/client'
import { emitToast } from '../toastBus'

const GATES = [
  {
    kind: 'GOLD', type: 'gold', name: 'VAULT OF GREED',
    desc: 'A hoard that regrows overnight. Take what you can carry.',
    reward: 'GOLD · SCALES WITH YOUR CLIMB',
    accent: '#ffd88a', border: 'rgba(255,216,138,.55)', wash: 'rgba(122,74,22,.22)',
    arch: 'rgba(255,216,138,.6)', archInner: 'rgba(255,216,138,.3)', filled: true,
  },
  {
    kind: 'MATERIALS', type: 'materials', name: 'QUARRY OF EMBERS',
    desc: 'Ore, essence and emberleaf — feed the Forge and the Alchemist.',
    reward: 'IRON · CRYSTAL · LEATHER · BONE',
    accent: '#8fbf9f', border: 'rgba(143,191,159,.5)', wash: 'rgba(36,80,58,.2)',
    arch: 'rgba(143,191,159,.55)', archInner: 'rgba(143,191,159,.28)', filled: false,
  },
  {
    kind: 'AETHER', type: 'aether', name: 'WELLSPRING OF AETHER',
    desc: 'Raw mana pools where the Tower bleeds. Bottle what the Skydock takes weeks to condense.',
    reward: 'AETHER · RAID FUEL',
    accent: '#c8a9f5', border: 'rgba(150,110,230,.5)', wash: 'rgba(58,42,104,.24)',
    arch: 'rgba(200,169,245,.55)', archInner: 'rgba(200,169,245,.28)', filled: false, glyph: '✦',
  },
]

function fmtCountdown(sec) {
  if (sec == null) return '—'
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60)
  return `${h}H ${String(m).padStart(2, '0')}M`
}

// The mock's arched doorway with a glowing heart.
function GateArch({ g }) {
  return (
    <div style={{ height: 96, position: 'relative', flex: 'none', marginTop: 10 }}>
      <div style={{ position: 'absolute', left: '50%', top: 6, transform: 'translateX(-50%)', width: 72, height: 88, border: `1px solid ${g.arch}`, borderRadius: '40px 40px 0 0', background: `linear-gradient(${g.wash},rgba(8,6,14,.4))` }} />
      <div style={{ position: 'absolute', left: '50%', top: 14, transform: 'translateX(-50%)', width: 56, height: 80, border: `1px solid ${g.archInner}`, borderRadius: '32px 32px 0 0' }} />
      {g.glyph ? (
        <div style={{ position: 'absolute', left: '50%', top: 40, transform: 'translateX(-50%)', fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 26, color: g.accent, textShadow: `0 0 18px ${g.accent}`, animation: 'toe-glow 3.2s ease-in-out infinite' }}>{g.glyph}</div>
      ) : (
        <div style={{ position: 'absolute', left: '50%', top: 44, transform: 'translateX(-50%) rotate(45deg)', width: 16, height: 16, background: g.accent, boxShadow: `0 0 22px ${g.accent}`, animation: 'toe-glow 3s ease-in-out infinite' }} />
      )}
    </div>
  )
}

export default function DailyDungeons({ onClose }) {
  const [status, setStatus] = useState(null)
  const [running, setRunning] = useState(null)
  const [tiers, setTiers] = useState({ gold: 1, materials: 1, aether: 1 })

  async function load() {
    try { setStatus(await getDailyDungeonStatus()) } catch { /* backend older than status endpoint */ }
  }
  useEffect(() => { load() }, [])

  async function enter(gate) {
    setRunning(gate.type)
    try {
      const res = await runDailyDungeon(gate.type, tiers[gate.type] || 1)
      if (res.type === 'materials') {
        const drops = Object.entries(res.reward).map(([k, v]) => `${k.replace(/_/g, ' ')} ×${v}`).join(', ')
        emitToast(`${gate.name} cleared — ${drops}`, 'success')
      } else {
        emitToast(res.message || `${gate.name} cleared!`, 'success')
      }
      await load()
    } catch (e) {
      emitToast(e.message, 'error')
    } finally {
      setRunning(null)
    }
  }

  const maxKeys = status?.max_keys ?? 3

  return (
    <div className="ilm-dungeons">
      <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>

      {/* header — ghost DAILY behind GATES */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 2 }}>
            <span style={{ width: 9, height: 9, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
            <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 600, letterSpacing: '.5em', fontSize: 13, color: 'var(--gold)' }}>AT THE TOWER'S FOOT</span>
          </div>
          <div className="ilm-title-stack">
            <div className="ghost">DAILY</div>
            <div className="solid">GATES</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10, marginRight: 40 }}>
          <span className="ilm-livedot" />
          <span style={{ fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: '.2em', color: '#e08585' }}>GATES CLOSE IN {fmtCountdown(status?.resets_in_seconds)}</span>
          {status?.scale_floor > 0 && (
            <span style={{ fontFamily: "'Cinzel',serif", fontSize: 9, letterSpacing: '.14em', color: 'var(--gold-hi)', border: '1px solid rgba(184,151,98,.4)', padding: '2px 8px', marginLeft: 8 }}>SCALED TO FLOOR {status.scale_floor}</span>
          )}
        </div>
      </div>

      {/* gates */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginTop: 18 }}>
        {GATES.map(g => {
          const keys = status?.keys?.[g.type] ?? maxKeys
          const noKeys = keys <= 0
          return (
            <div key={g.name} style={{
              position: 'relative', border: `1px solid ${g.border}`,
              background: `linear-gradient(160deg,${g.wash},rgba(12,7,24,.6))`,
              padding: '18px 20px', clipPath: 'polygon(0 0,100% 0,100% 100%,14px 100%)',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 340,
            }}>
              <GateArch g={g} />
              <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: 9, color: g.accent, textAlign: 'center', marginTop: 8 }}>{g.kind}</div>
              <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 20, color: 'var(--text-hi)', textAlign: 'center', marginTop: 4 }}>{g.name}</div>
              <div style={{ fontSize: 13, fontStyle: 'italic', color: 'var(--muted)', textAlign: 'center', marginTop: 5, lineHeight: 1.35 }}>{g.desc}</div>
              {/* tier chips — deeper tiers open as the runner climbs (30 / 60) */}
              <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 12 }}>
                {[1, 2, 3].map(t => {
                  const unlocked = (status?.tiers_unlocked || [1]).includes(t)
                  const active = (tiers[g.type] || 1) === t
                  return (
                    <button key={t} disabled={!unlocked} onClick={() => setTiers(prev => ({ ...prev, [g.type]: t }))}
                      title={unlocked ? `Tier ${t}` : `Opens past floor ${status?.tier_floors?.[t] ?? (t === 2 ? 30 : 60)}`}
                      style={{ width: 30, height: 26, flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 11, cursor: unlocked ? 'pointer' : 'default',
                        border: active && unlocked ? `1px solid ${g.accent}` : '1px solid rgba(184,151,98,.28)',
                        background: active && unlocked ? 'rgba(184,151,98,.14)' : 'rgba(12,7,24,.45)',
                        color: !unlocked ? '#4a4458' : active ? g.accent : 'var(--muted)',
                        clipPath: 'polygon(5px 0,100% 0,calc(100% - 5px) 100%,0 100%)' }}>
                      {['I', 'II', 'III'][t - 1]}
                    </button>
                  )
                })}
              </div>
              <div style={{ textAlign: 'center', fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.14em', color: 'var(--muted)', marginTop: 8 }}>
                {g.reward}{(tiers[g.type] || 1) > 1 ? ` · TIER ${['I', 'II', 'III'][(tiers[g.type] || 1) - 1]} PAYS ×${(tiers[g.type] === 2 ? '2.2' : '4')}` : ''}
              </div>
              <span style={{ flex: 1 }} />
              {/* keys */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 10 }}>
                <span style={{ fontFamily: "'Cinzel',serif", fontSize: 8, letterSpacing: '.18em', color: 'var(--muted)' }}>KEYS</span>
                {Array.from({ length: maxKeys }).map((_, i) => (
                  <span key={i} style={{
                    width: 9, height: 9, transform: 'rotate(45deg)', display: 'inline-block',
                    background: i < keys ? g.accent : 'transparent',
                    border: i < keys ? 'none' : `1px solid ${g.archInner}`,
                  }} />
                ))}
              </div>
              {noKeys ? (
                <div style={{ marginTop: 10, textAlign: 'center', fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 11, color: '#6f628c', border: '1px solid rgba(138,123,176,.35)', padding: '10px 0', clipPath: 'polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)' }}>
                  NO KEYS · DAWN
                </div>
              ) : (
                <button onClick={() => enter(g)} disabled={running === g.type}
                  style={g.filled ? {
                    cursor: 'pointer', marginTop: 10, textAlign: 'center', fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 11,
                    color: '#0a0710', background: 'linear-gradient(120deg,#ffd88a,#b89762)', border: 'none',
                    padding: '11px 0', clipPath: 'polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)', boxShadow: '0 6px 20px rgba(184,151,98,.35)',
                  } : {
                    cursor: 'pointer', marginTop: 10, textAlign: 'center', fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.2em', fontSize: 11,
                    color: g.accent, border: `1px solid ${g.border}`, background: `${g.wash}`,
                    padding: '10px 0', clipPath: 'polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)',
                  }}>
                  {running === g.type ? 'BREACHING…' : 'ENTER THE GATE'}
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* footer */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 20 }}>
        <span style={{ height: 1, flex: 1, background: 'linear-gradient(90deg,transparent,rgba(184,151,98,.3))' }} />
        <span style={{ fontSize: 12.5, fontStyle: 'italic', color: 'var(--muted)' }}>Three keys per gate each day — rewards scale with your deepest climb, and the gates reseal at dawn.</span>
        <span style={{ height: 1, flex: 1, background: 'linear-gradient(90deg,rgba(184,151,98,.3),transparent)' }} />
      </div>
    </div>
  )
}
