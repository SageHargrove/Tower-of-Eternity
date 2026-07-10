/*
 * FOUR TIERS — the banner-tier showcase (mockup "Base - Illuminated").
 * Four hanging standards (Iron / Silver / Gold / Mythic) using the painted
 * showcase art; tiers beyond the Wall's level hang veiled. The frame is
 * drawn by the game, the art is yours.
 */
import React, { useState, useEffect } from 'react'
import { getBanner } from '../api/client'

const CUT = 'polygon(0 0,100% 0,100% 82%,50% 100%,0 82%)'
const CUT_INNER = 'polygon(0 0,100% 0,100% 81%,50% 99%,0 81%)'

const TIERS = [
  { n: 1, name: 'IRON', color: '#a8a8b4', dim: '#6f6f7e', border: 'rgba(120,120,132,.5)', top: '2px solid #55555f' },
  { n: 2, name: 'SILVER', color: '#c3cddf', dim: '#8b95ab', border: 'rgba(176,188,210,.65)', top: '2px solid #8b95ab', req: 'WALL LV 5' },
  { n: 3, name: 'GOLD', color: '#d8bb84', dim: '#b89762', border: 'rgba(216,187,132,.8)', top: '3px solid #b89762', req: 'WALL LV 15' },
  { n: 4, name: 'MYTHIC', color: '#c8a9f5', dim: '#c8a9f5', border: 'rgba(216,187,132,.85)', top: 'none', req: 'WALL LV 30' },
]

const EMBERS = [
  [26, 300, 4, '#e8a34c', 4, 0], [120, 330, 3, '#c8a9f5', 5, 1], [200, 310, 4, '#e8a34c', 4.5, 2],
  [66, 320, 3, '#ffd88a', 5.5, 2.6], [170, 340, 3, '#c8a9f5', 4.2, 0.5], [44, 334, 5, '#e8a34c', 3.6, 1.6],
  [146, 318, 4, '#ffd88a', 4.8, 3.2], [96, 342, 5, '#e8a34c', 4, 0.9],
]

export default function BannerTiers({ onClose, onOpenStudio }) {
  const [unlocked, setUnlocked] = useState(1)

  useEffect(() => {
    getBanner().then(b => setUnlocked(b.unlocked_tier || 1)).catch(() => {})
  }, [])

  return (
    <div className="ilm-btiers">
      <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
            <span style={{ width: 9, height: 9, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
            <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 600, letterSpacing: '.5em', fontSize: '0.7rem', color: 'var(--gold)' }}>BANNER STUDIO</span>
          </div>
          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.4rem', color: 'var(--text-hi)', textShadow: '0 6px 40px rgba(124,58,214,.35)' }}>FOUR TIERS</div>
          <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 2 }}>The frame is drawn by the game — the art is yours.</div>
        </div>
        {onOpenStudio && (
          <button className="ilm-btn ilm-btn-gold" style={{ marginTop: 8, marginRight: 48 }} onClick={onOpenStudio}>OPEN THE STUDIO ›</button>
        )}
      </div>

      {/* shared hanging rod */}
      <div style={{ height: 3, margin: '22px 8px 0', background: 'linear-gradient(90deg,rgba(184,151,98,0),var(--gold) 8%,var(--gold) 92%,rgba(184,151,98,0))' }} />

      <div className="ilm-btiers-row">
        {TIERS.map((t, i) => {
          const locked = t.n > unlocked
          const mythic = t.n === 4
          return (
            <div key={t.n} className="ilm-btier" style={{ animationDelay: `${i * 0.7}s` }}>
              {mythic && <div style={{ position: 'absolute', inset: '-14px -6px auto', height: 380, pointerEvents: 'none', background: 'radial-gradient(60% 55% at 50% 40%, rgba(150,110,230,.4), rgba(0,0,0,0) 72%)' }} />}
              {mythic && !locked && EMBERS.map(([l, tp, s, c, d, dl], j) => (
                <span key={j} style={{ position: 'absolute', left: `${(l / 250) * 100}%`, top: tp * 0.85, width: s, height: s, borderRadius: '50%', background: c, boxShadow: `0 0 ${s * 2}px ${c}`, animation: `ember-rise ${d}s linear ${dl}s infinite` }} />
              ))}

              {/* cloth: painted showcase art */}
              <div className="ilm-btier-cloth" style={{ clipPath: CUT }}>
                <img src={`/icons/banners/showcase_tier${t.n}.png`} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
                <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(170deg,rgba(16,10,26,.32),rgba(10,7,16,.4) 70%)' }} />
              </div>
              {/* frame */}
              <div className="ilm-btier-frame" style={{ clipPath: CUT, borderTop: t.top === 'none' ? undefined : t.top, boxShadow: `inset 0 0 0 1px ${t.border}${t.n >= 3 ? ', inset 0 0 30px rgba(184,151,98,.22)' : ''}${mythic ? ', inset 0 -48px 52px -14px rgba(232,163,76,.55), inset 0 0 36px rgba(150,110,230,.3)' : ''}` }} />
              {t.n >= 2 && <div className="ilm-btier-frame" style={{ inset: '8px 8px 16px', clipPath: CUT_INNER, boxShadow: `inset 0 0 0 1px ${t.border.replace(/\.\d+\)/, '.35)')}` }} />}
              {/* mythic rainbow trim */}
              {mythic && <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 6, pointerEvents: 'none', backgroundImage: 'linear-gradient(90deg,#ff2020,#ff8c00,#ffe600,#30e030,#00e5ff,#4060ff,#b040ff,#ff30c0,#ff2020)', backgroundSize: '200% 100%', animation: 'star-rainbow-slide 4s linear infinite' }} />}
              {/* rod finials */}
              <div className="ilm-btier-finial" style={{ left: -6, borderColor: t.dim }} />
              <div className="ilm-btier-finial" style={{ right: -6, borderColor: t.dim }} />
              {t.n >= 3 && (
                <div className="ilm-btier-crest" style={{ borderColor: t.color, boxShadow: mythic ? '0 0 12px rgba(150,110,230,.7)' : undefined }}>
                  <span style={{ transform: 'rotate(-45deg)', color: t.color, fontSize: 11 }}>✦</span>
                </div>
              )}

              {/* locked veil */}
              {locked && (
                <>
                  <div style={{ position: 'absolute', inset: 0, zIndex: 5, background: 'rgba(5,4,10,.78)', clipPath: CUT }} />
                  <div style={{ position: 'absolute', left: '50%', top: '32%', transform: 'translateX(-50%)', zIndex: 6, textAlign: 'center' }}>
                    <div style={{ width: 26, height: 18, border: `3px solid ${t.color}`, borderBottom: 'none', borderRadius: '13px 13px 0 0', margin: '0 auto' }} />
                    <div style={{ width: 44, height: 32, background: '#140b22', border: `1px solid ${t.color}`, margin: '-2px auto 0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ width: 8, height: 8, transform: 'rotate(45deg)', background: t.color, display: 'inline-block' }} />
                    </div>
                    <div style={{ fontFamily: "'Cinzel',serif", fontSize: '0.56rem', letterSpacing: '.22em', color: 'var(--text-dim)', marginTop: 10, whiteSpace: 'nowrap' }}>UNLOCKS AT {t.req}</div>
                  </div>
                </>
              )}

              {/* label */}
              <div className="ilm-btier-label">
                {mythic
                  ? <div className="rainbow-text" style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.3em', fontSize: '0.85rem' }}>TIER IV</div>
                  : <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.3em', fontSize: '0.85rem', color: t.color }}>TIER {'I'.repeat(t.n)}</div>}
                <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: '0.6rem', color: t.dim, marginTop: 4 }}>{t.name}</div>
                {t.n === unlocked && (
                  <div style={{ marginTop: 7 }}><span style={{ fontFamily: "'Cinzel',serif", fontSize: '0.55rem', letterSpacing: '.22em', color: '#0a0710', background: 'var(--gold-hi)', padding: '2px 9px' }}>CURRENT</span></div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div style={{ textAlign: 'center', fontFamily: "'Cinzel',serif", letterSpacing: '.26em', fontSize: '0.66rem', color: 'var(--muted)', marginTop: 20 }}>
        HIGHER TIERS EARNED BY THE WALL'S RISE · FRAME IS DRAWN BY THE GAME, ART IS YOURS
      </div>
    </div>
  )
}
