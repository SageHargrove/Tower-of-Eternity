import React, { useState, useEffect, useRef } from 'react'
import { getBanner, saveBanner } from '../api/client'
import Pennant, { CLOTH_SWATCHES, CUTS, FRAME_TIERS, SIGILS } from './Pennant'
import BannerTiers from './BannerTiers'

// Banner Studio — faithful to the Illuminated mockup: pick a CLOTH color (or
// paint your own layer), a SIGIL glyph / emblem PNG, the TAIL CUT (free), and
// the TIER FRAME (earned by renown — Wall progression — never bought). Saved
// banners live in localStorage; SHARE CODE serializes the design to a compact
// string any player can paste back in.

const CANVAS_SIZE = 512
const PALETTE = ['#e8e0d0', '#c9a84c', '#d4364e', '#3f7fd0', '#3fae5a', '#a83dff', '#f0f0f0', '#1a1a1a', '#e07830', '#00b8b8']
const PRESETS_KEY = 'bannerPresets'

const CUT_LABEL = { swallow: 'SWALLOW', point: 'POINT', square: 'SQUARE' }
const ROMAN = ['I', 'II', 'III', 'IV']

function loadPresets() {
  try { return JSON.parse(localStorage.getItem(PRESETS_KEY)) || [] } catch { return [] }
}

function Field({ label, children, hint }) {
  return (
    <div style={{ marginBottom: '0.9rem' }}>
      <div className="ilm-micro" style={{ color: 'var(--gold)', letterSpacing: '.3em', marginBottom: 6 }}>{label}</div>
      {children}
      {hint && <div className="text-dim" style={{ fontStyle: 'italic', fontSize: '0.72rem', marginTop: 4 }}>{hint}</div>}
    </div>
  )
}

export default function BannerStudio({ onClose, onSaved }) {
  const [data, setData] = useState(null)
  const [cloth, setCloth] = useState(CLOTH_SWATCHES[1])
  const [cut, setCut] = useState('swallow')
  const [frame, setFrame] = useState(1)
  const [sigil, setSigil] = useState(null)
  const [emblem, setEmblem] = useState(null)
  const [painting, setPainting] = useState(false)
  const [paintData, setPaintData] = useState(null)
  const [color, setColor] = useState(PALETTE[1])
  const [brush, setBrush] = useState(14)
  const [erasing, setErasing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showTiers, setShowTiers] = useState(false)
  const [msg, setMsg] = useState(null)
  const [presets, setPresets] = useState(loadPresets)
  const canvasRef = useRef(null)
  const drawing = useRef(false)
  const last = useRef(null)

  useEffect(() => {
    getBanner().then(b => {
      setData(b)
      if (b.cloth) setCloth(b.cloth)
      if (b.cut) setCut(b.cut)
      setFrame(b.frame_tier || Math.min(b.unlocked_tier || 1, b.template_tier || 1))
      setSigil(b.sigil || null)
      setEmblem(b.emblem || null)
      if (b.paint) setPaintData(b.paint)
    }).catch(e => setMsg(e.message))
  }, [])

  /* ---- paint layer (kept from the old studio, now optional) -------------- */
  function canvasPos(e) {
    const cv = canvasRef.current
    const rect = cv.getBoundingClientRect()
    const pt = e.touches ? e.touches[0] : e
    return {
      x: (pt.clientX - rect.left) * (CANVAS_SIZE / rect.width),
      y: (pt.clientY - rect.top) * (CANVAS_SIZE / rect.height),
    }
  }
  function strokeTo(pos) {
    const ctx = canvasRef.current.getContext('2d')
    ctx.globalCompositeOperation = erasing ? 'destination-out' : 'source-over'
    ctx.strokeStyle = color
    ctx.lineWidth = brush
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.beginPath()
    ctx.moveTo(last.current.x, last.current.y)
    ctx.lineTo(pos.x, pos.y)
    ctx.stroke()
    last.current = pos
  }
  function handleDown(e) { e.preventDefault(); drawing.current = true; last.current = canvasPos(e); strokeTo({ x: last.current.x + 0.01, y: last.current.y }) }
  function handleMove(e) { if (drawing.current) { e.preventDefault(); strokeTo(canvasPos(e)) } }
  function handleUp() {
    if (!drawing.current) return
    drawing.current = false
    setPaintData(canvasRef.current.toDataURL('image/png'))
  }
  function clearCanvas() {
    canvasRef.current?.getContext('2d').clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
    setPaintData(null)
  }
  function handleImport(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const img = new Image()
    img.onload = () => {
      const cv = canvasRef.current
      const ctx = cv.getContext('2d')
      ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
      const scale = Math.min((CANVAS_SIZE * 0.6) / img.width, (CANVAS_SIZE * 0.6) / img.height)
      const w = img.width * scale, h = img.height * scale
      ctx.drawImage(img, (CANVAS_SIZE - w) / 2, CANVAS_SIZE * 0.18, w, h)
      setPaintData(cv.toDataURL('image/png'))
    }
    img.src = URL.createObjectURL(file)
    e.target.value = ''
  }
  // hydrate canvas when opening the paint drawer with an existing layer
  useEffect(() => {
    if (!painting || !paintData) return
    const cv = canvasRef.current
    if (!cv) return
    const img = new Image()
    img.onload = () => { cv.getContext('2d').drawImage(img, 0, 0, CANVAS_SIZE, CANVAS_SIZE) }
    img.src = paintData
  }, [painting]) // eslint-disable-line react-hooks/exhaustive-deps

  /* ---- presets + share code ---------------------------------------------- */
  const design = { cloth, cut, frame_tier: frame, sigil, emblem }

  function savePreset() {
    const next = [design, ...presets.filter(p => JSON.stringify(p) !== JSON.stringify(design))].slice(0, 6)
    setPresets(next)
    localStorage.setItem(PRESETS_KEY, JSON.stringify(next))
  }
  function applyPreset(p) {
    setCloth(p.cloth || CLOTH_SWATCHES[1]); setCut(p.cut || 'swallow')
    setFrame(Math.min(p.frame_tier || 1, data?.unlocked_tier || 1))
    setSigil(p.sigil || null); setEmblem(p.emblem || null)
  }
  async function shareCode() {
    try {
      await navigator.clipboard.writeText(`TOE1:${btoa(JSON.stringify(design))}`)
      setMsg('Share code copied — hand it to your lodge.')
    } catch { setMsg('Could not reach the clipboard.') }
  }
  function importCode() {
    const code = window.prompt('Paste a banner share code:')
    if (!code) return
    try {
      const p = JSON.parse(atob(code.replace(/^TOE1:/, '')))
      applyPreset(p)
      setMsg('Design loaded.')
    } catch { setMsg('That code did not read as a banner.') }
  }

  async function handleSave() {
    setSaving(true)
    setMsg(null)
    try {
      await saveBanner(frame, emblem, paintData, { cloth, cut, frame_tier: frame, sigil })
      if (onSaved) onSaved()
      onClose()
    } catch (e) {
      setMsg(e.message)
    } finally {
      setSaving(false)
    }
  }

  if (!data) return null
  const unlocked = data.unlocked_tier || 1

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 300, background: 'rgba(5,5,10,0.92)', display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={onClose}>
      <div className="card" style={{ position: 'relative', width: 'min(980px, 96vw)', maxHeight: '92vh', overflowY: 'auto', padding: '1.5rem' }} onClick={e => e.stopPropagation()}>
        <span className="ilm-corner" /><span className="ilm-corner ilm-corner-r" />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
              <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.5em', fontSize: '0.6rem', color: 'var(--gold)' }}>YOUR STANDARD</span>
            </div>
            <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.5rem', letterSpacing: '.04em', color: 'var(--text-hi)', marginTop: 4 }}>BANNER STUDIO</div>
            <div className="text-dim" style={{ fontStyle: 'italic', fontSize: '0.82rem' }}>Cut your own standard — it flies on your flagship, your profile, and the boards.</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button className="ilm-btn ilm-btn-ghost" style={{ padding: '4px 12px', fontSize: '0.62rem' }} onClick={() => setShowTiers(true)}>FOUR TIERS ›</button>
            <button className="ilm-close" onClick={onClose}>✕</button>
          </div>
        </div>
        {showTiers && <BannerTiers onClose={() => setShowTiers(false)} />}

        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
          {/* ═══ controls (left card of the mockup) ═══ */}
          <div style={{ flex: 1, minWidth: 300 }}>
            <Field label="CLOTH">
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                {CLOTH_SWATCHES.map(c => (
                  <button key={c} onClick={() => setCloth(c)}
                    style={{ width: 44, height: 26, background: c, cursor: 'pointer', border: cloth === c ? '2px solid var(--gold)' : '2px solid rgba(255,255,255,.18)' }} />
                ))}
                <input type="color" value={cloth} onChange={e => setCloth(e.target.value)} title="Custom cloth"
                  style={{ width: 30, height: 26, padding: 0, border: 'none', background: 'none', cursor: 'pointer' }} />
                <button className={`ilm-btn ${painting ? 'ilm-btn-gold' : 'ilm-btn-ghost'}`} onClick={() => setPainting(p => !p)} style={{ fontSize: '0.62rem', padding: '0.35rem 0.7rem' }}>
                  ✎ PAINT YOUR OWN
                </button>
              </div>
            </Field>

            {painting && (
              <div style={{ marginBottom: '0.9rem', border: '1px solid var(--border)', padding: '0.7rem' }}>
                <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                  {PALETTE.map(c => (
                    <button key={c} onClick={() => { setColor(c); setErasing(false) }}
                      style={{ width: 22, height: 22, borderRadius: '50%', background: c, cursor: 'pointer', border: color === c && !erasing ? '2px solid var(--gold)' : '2px solid rgba(255,255,255,0.2)' }} />
                  ))}
                  <input type="color" value={color} onChange={e => { setColor(e.target.value); setErasing(false) }}
                    style={{ width: 22, height: 22, padding: 0, border: 'none', background: 'none', cursor: 'pointer' }} title="Custom color" />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
                  <label className="text-dim text-sm">Brush</label>
                  <input type="range" min={3} max={48} value={brush} onChange={e => setBrush(parseInt(e.target.value))} style={{ flex: 1 }} />
                  <button className={`btn ${erasing ? 'btn-gold' : ''}`} onClick={() => setErasing(x => !x)} style={{ fontSize: '0.72rem' }}>Eraser</button>
                  <button className="btn" onClick={clearCanvas} style={{ fontSize: '0.72rem' }}>Clear</button>
                  <label className="btn" style={{ fontSize: '0.72rem', cursor: 'pointer' }}>
                    Import PNG…
                    <input type="file" accept="image/png,image/jpeg,image/webp" onChange={handleImport} style={{ display: 'none' }} />
                  </label>
                </div>
                <div className="text-dim" style={{ fontSize: '0.7rem', fontStyle: 'italic' }}>Paint on the pennant in the preview →</div>
              </div>
            )}

            <Field label="SIGIL" hint="Pick a glyph, or drop your own emblem PNG onto the pennant.">
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                {SIGILS.map(s => (
                  <button key={s.id || 'none'} onClick={() => { setSigil(s.id); if (s.id) setEmblem(null) }}
                    style={{
                      width: 36, height: 36, cursor: 'pointer', fontSize: '0.95rem', color: 'var(--text-hi)',
                      background: 'rgba(255,255,255,.03)',
                      border: sigil === s.id && !emblem ? '1px solid var(--gold)' : '1px solid var(--border)',
                    }}>{s.glyph}</button>
                ))}
              </div>
            </Field>

            <Field label="MY EMBLEMS" hint="Your saved crests — one on the pennant flies it. Lodges love a matching set.">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(52px, 1fr))', gap: '0.35rem' }}>
                {(data.emblems || []).map(e => (
                  <button key={e} onClick={() => { setEmblem(emblem === e ? null : e); setSigil(null) }}
                    style={{ aspectRatio: '1', padding: '0.25rem', cursor: 'pointer', background: 'rgba(255,255,255,.02)', border: emblem === e ? '1px solid var(--gold)' : '1px solid var(--border)' }}>
                    <img src={`/icons/emblems/${e}.png`} alt={e} style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }} />
                  </button>
                ))}
              </div>
            </Field>

            <Field label="TAIL CUT">
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {CUTS.map(c => (
                  <button key={c} onClick={() => setCut(c)}
                    style={{ padding: '0.5rem 0.6rem 0.35rem', cursor: 'pointer', background: 'rgba(255,255,255,.02)', border: cut === c ? '1px solid var(--gold)' : '1px solid var(--border)', textAlign: 'center' }}>
                    <div style={{
                      width: 26, height: 38, margin: '0 auto 4px', background: cut === c ? 'var(--gold-hi)' : 'var(--muted)',
                      WebkitMaskImage: `url(/icons/banners/mask_${c}.svg)`, maskImage: `url(/icons/banners/mask_${c}.svg)`,
                      WebkitMaskSize: 'contain', maskSize: 'contain', WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat', WebkitMaskPosition: 'center', maskPosition: 'center',
                    }} />
                    <span className="ilm-micro" style={{ color: cut === c ? 'var(--gold-hi)' : 'var(--muted)' }}>{CUT_LABEL[c]}</span>
                  </button>
                ))}
              </div>
            </Field>

            <Field label="TIER FRAME" hint="Flying the higher frame — trim is earned by renown, never bought.">
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {FRAME_TIERS.map(f => {
                  const locked = f.tier > unlocked
                  return (
                    <button key={f.tier} disabled={locked} onClick={() => setFrame(f.tier)}
                      title={locked ? 'Earned at higher renown' : ''}
                      style={{
                        flex: 1, padding: '0.45rem 0.2rem', cursor: locked ? 'not-allowed' : 'pointer', opacity: locked ? 0.32 : 1,
                        background: 'rgba(255,255,255,.02)', border: frame === f.tier ? '1px solid var(--gold)' : '1px solid var(--border)', textAlign: 'center',
                      }}>
                      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, color: f.metal }}>{ROMAN[f.tier - 1]}</div>
                      <div className="ilm-micro" style={{ color: frame === f.tier ? 'var(--gold-hi)' : 'var(--muted)' }}>{f.name}</div>
                    </button>
                  )
                })}
              </div>
            </Field>

            <Field label="SAVED BANNERS" hint={`${presets.length} saved · tap to fly · + to keep this one`}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                {presets.map((p, i) => (
                  <button key={i} onClick={() => applyPreset(p)} title="Fly this design"
                    style={{ background: 'none', border: '1px solid var(--border)', padding: '4px 6px 2px', cursor: 'pointer' }}>
                    <Pennant cloth={p.cloth} cut={p.cut} frameTier={p.frame_tier} sigil={p.sigil} emblem={p.emblem} width={26} />
                  </button>
                ))}
                <button onClick={savePreset} title="Save the current design"
                  style={{ width: 38, height: 52, background: 'none', border: '1px dashed var(--gold-dim)', color: 'var(--gold-hi)', fontSize: '1.1rem', cursor: 'pointer' }}>+</button>
                <div style={{ flex: 1 }} />
                <button className="ilm-btn ilm-btn-ghost" onClick={shareCode} style={{ fontSize: '0.62rem', padding: '0.4rem 0.7rem' }}>⛿ SHARE CODE</button>
                <button className="ilm-btn ilm-btn-ghost" onClick={importCode} style={{ fontSize: '0.62rem', padding: '0.4rem 0.7rem' }}>LOAD</button>
              </div>
            </Field>

            {msg && <div style={{ color: 'var(--gold-hi)', fontSize: '0.85rem', marginTop: '0.5rem' }}>{msg}</div>}

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
              <span className="text-dim" style={{ fontStyle: 'italic', fontSize: '0.75rem', flex: 1 }}>Recut anytime — the sky remembers only the newest cloth.</span>
              <button className="ilm-btn ilm-btn-gold" disabled={saving} onClick={handleSave} style={{ padding: '0.7rem 1.6rem' }}>
                {saving ? 'RAISING…' : 'RAISE THE STANDARD'}
              </button>
            </div>
          </div>

          {/* ═══ live preview (right panel of the mockup) ═══ */}
          <div style={{ flex: '0 0 300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at 50% 35%, rgba(64,34,110,.45), rgba(10,7,19,.9))', border: '1px solid var(--border)', padding: '2.2rem 1rem' }}>
            <div className="ilm-micro" style={{ color: 'var(--muted)', letterSpacing: '.4em', marginBottom: 14 }}>YOUR STANDARD</div>
            <div style={{ position: 'relative' }}>
              <Pennant cloth={cloth} cut={cut} frameTier={frame} sigil={sigil} emblem={emblem} paint={paintData} width={150} />
              {/* paint surface sits exactly over the pennant while painting */}
              {painting && (
                <canvas
                  ref={canvasRef}
                  width={CANVAS_SIZE} height={CANVAS_SIZE}
                  style={{
                    position: 'absolute', inset: 0, width: '100%', height: '100%', cursor: 'crosshair', touchAction: 'none',
                    WebkitMaskImage: `url(/icons/banners/mask_${cut}.svg)`, maskImage: `url(/icons/banners/mask_${cut}.svg)`,
                    WebkitMaskSize: 'contain', maskSize: 'contain', WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat', WebkitMaskPosition: 'center', maskPosition: 'center',
                  }}
                  onMouseDown={handleDown} onMouseMove={handleMove} onMouseUp={handleUp} onMouseLeave={handleUp}
                  onTouchStart={handleDown} onTouchMove={handleMove} onTouchEnd={handleUp}
                />
              )}
            </div>
            <div className="text-dim" style={{ marginTop: 18, fontSize: '0.78rem', textAlign: 'center', fontStyle: 'italic' }}>
              This banner flies over your base, your battleship, and beside your name in the World.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
