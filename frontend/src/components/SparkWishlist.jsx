/*
 * SPARK WISHLIST — name up to three classes; the guaranteed 5★ from a
 * spark redeem will be one of them (mockup "Squad Overview - Illuminated").
 * Freely changeable until the spark is spent.
 */
import React, { useState, useEffect } from 'react'
import { getSparkWishlist, setSparkWishlist } from '../api/client'
import { emitToast } from '../toastBus'

const COMBAT = ['Warrior', 'Spearman', 'Thief', 'Archer', 'Mage', 'Acolyte', 'Magic Engineer', 'Spellsword']

const initials = name => name === 'Magic Engineer' ? 'EN' : name.slice(0, 2).toUpperCase()
const displayName = name => name === 'Magic Engineer' ? 'M. ENGINEER' : name.toUpperCase()

// Pool chips are gold-toned for combat classes, green for support/profession
// (spec: "Spark Wishlist" mockup); the chosen three glow gold regardless.
function ClassChip({ name, on, onClick, support }) {
  const idle = support
    ? { color: '#a8bfae', border: '1px solid rgba(74,154,106,.3)', diamond: 'rgba(143,191,159,.5)', mono: '#8fbf9f', bg: '#122016' }
    : { color: '#c9bfa8', border: '1px solid rgba(184,151,98,.3)', diamond: 'rgba(216,187,132,.6)', mono: '#d8bb84', bg: '#1c1030' }
  return (
    <button onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', whiteSpace: 'nowrap',
      fontFamily: "'Cinzel',serif", fontSize: '0.62rem', letterSpacing: '.08em',
      color: on ? '#f3ecdd' : idle.color,
      background: on ? 'linear-gradient(120deg,rgba(184,151,98,.14),rgba(12,7,24,.6))' : 'rgba(12,7,24,.5)',
      border: on ? '1px solid #d8bb84' : idle.border, padding: '6px 9px',
      boxShadow: on ? '0 0 14px rgba(184,151,98,.25)' : 'none',
    }}>
      <span style={{ width: 20, height: 20, transform: 'rotate(45deg)', border: `1px solid ${on ? '#d8bb84' : idle.diamond}`, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flex: 'none', background: idle.bg }}>
        <span style={{ transform: 'rotate(-45deg)', fontSize: '0.48rem', color: on ? '#d8bb84' : idle.mono }}>{initials(name)}</span>
      </span>
      {displayName(name)}
    </button>
  )
}

export default function SparkWishlist({ onClose }) {
  const [data, setData] = useState(null)
  const [picked, setPicked] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getSparkWishlist().then(d => { setData(d); setPicked(d.classes || []) }).catch(() => {})
  }, [])

  const pool = data?.pool || []
  const combat = pool.filter(c => COMBAT.includes(c))
  const support = pool.filter(c => !COMBAT.includes(c))

  function toggle(name) {
    setPicked(p => p.includes(name) ? p.filter(x => x !== name) : (p.length < 3 ? [...p, name] : p))
  }

  async function seal() {
    setSaving(true)
    try {
      await setSparkWishlist(picked)
      emitToast(picked.length ? `Wishlist sealed — ${picked.join(', ')}.` : 'Wishlist cleared — the spark rolls free.', 'success')
      onClose()
    } catch (e) { emitToast(e.message, 'error') } finally { setSaving(false) }
  }

  return (
    <div className="ilm-modal-scrim" style={{ zIndex: 330 }} onClick={onClose}>
      <div className="ilm-featmodal" style={{ width: 620, maxWidth: '94vw', maxHeight: '88vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
        <span className="ilm-corner" /><span className="ilm-corner ilm-corner-r" />
        <button className="ilm-close" style={{ position: 'absolute', top: 14, right: 14 }} onClick={onClose}>✕</button>
        <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>GEM SUMMON · SPARK</div>
        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.7rem', color: 'var(--text-hi)', marginTop: 2 }}>SPARK WISHLIST</div>
        <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', margin: '8px 0 14px', lineHeight: 1.5 }}>
          Name up to three classes. When your Sparks reach {data?.threshold ?? 50}, the guaranteed 5★ will be one of them.
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
          <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
          <span className="ilm-micro" style={{ color: 'var(--gold)' }}>YOUR THREE</span>
          <span style={{ flex: 1, height: 1, background: 'rgba(184,151,98,.25)' }} />
          <span className="ilm-micro" style={{ color: 'var(--lavender)' }}>SPARKS {data?.spark_points ?? 0}/{data?.threshold ?? 50}</span>
        </div>
        <div style={{ display: 'flex', gap: 10, marginBottom: 18, flexWrap: 'wrap' }}>
          {[0, 1, 2].map(i => picked[i]
            ? <ClassChip key={picked[i]} name={picked[i]} on onClick={() => toggle(picked[i])} />
            : <span key={`empty-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: "'Cinzel',serif", fontSize: '0.62rem', letterSpacing: '.1em', color: 'var(--muted)', border: '1px dashed rgba(154,134,184,.35)', padding: '7px 12px 7px 8px' }}>
                <span style={{ width: 22, height: 22, transform: 'rotate(45deg)', border: '1px dashed rgba(154,134,184,.4)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flex: 'none' }}><span style={{ transform: 'rotate(-45deg)' }}>+</span></span>
                {['FIRST', 'SECOND', 'THIRD'][i]} CLASS
              </span>)}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '4px 0 10px' }}>
          <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--violet)', display: 'inline-block' }} />
          <span className="ilm-micro" style={{ color: 'var(--lavender)' }}>COMBAT CLASSES</span>
          <span style={{ flex: 1, height: 1, background: 'rgba(150,110,230,.25)' }} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 7 }}>
          {combat.map(c => <ClassChip key={c} name={c} on={picked.includes(c)} onClick={() => toggle(c)} />)}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '14px 0 10px' }}>
          <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: '#8fbf9f', display: 'inline-block' }} />
          <span className="ilm-micro" style={{ color: '#8fbf9f' }}>SUPPORT & PROFESSION</span>
          <span style={{ flex: 1, height: 1, background: 'rgba(74,154,106,.25)' }} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 7 }}>
          {support.map(c => <ClassChip key={c} name={c} on={picked.includes(c)} support onClick={() => toggle(c)} />)}
        </div>

        <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: '0.8rem', margin: '16px 0' }}>You may change your wishlist freely until the Spark is spent.</div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="ilm-btn ilm-btn-violet" style={{ flex: 1.4 }} disabled={saving} onClick={seal}>{saving ? 'SEALING…' : 'SEAL THE WISHLIST'}</button>
          <button style={{ flex: 0.7, background: 'none', border: 'none', cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: 500, letterSpacing: '.2em', fontSize: '0.68rem', color: 'var(--text-dim)' }} onClick={onClose}>CANCEL</button>
        </div>
      </div>
    </div>
  )
}
