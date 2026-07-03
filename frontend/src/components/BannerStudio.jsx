import React, { useState, useEffect, useRef } from 'react'
import { getBanner, saveBanner } from '../api/client'

// Full banner customization: pick a cloth tier (unlocked by the Wall's art
// tier, lower tiers always equippable — tattered-cloth mind games are a
// feature), then either mount a pre-made emblem or PAINT your own design
// on an HTML5 canvas (or import a PNG) — the painted layer is saved as a
// dataURL and composited over the cloth wherever the banner shows.

const CANVAS_SIZE = 512
const PALETTE = ['#e8e0d0', '#c9a84c', '#d4364e', '#3f7fd0', '#3fae5a', '#a83dff', '#f0f0f0', '#1a1a1a', '#e07830', '#00b8b8']

export default function BannerStudio({ onClose, onSaved }) {
  const [data, setData] = useState(null)
  const [tier, setTier] = useState(1)
  const [emblem, setEmblem] = useState(null)
  const [mode, setMode] = useState('emblem') // 'emblem' | 'paint'
  const [color, setColor] = useState(PALETTE[1])
  const [brush, setBrush] = useState(14)
  const [erasing, setErasing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)
  const canvasRef = useRef(null)
  const drawing = useRef(false)
  const last = useRef(null)
  const dirty = useRef(false)

  useEffect(() => {
    getBanner().then(b => {
      setData(b)
      setTier(b.template_tier || 1)
      setEmblem(b.emblem || null)
      if (b.paint) {
        setMode('paint')
        // hydrate the canvas with the saved paint layer
        requestAnimationFrame(() => {
          const cv = canvasRef.current
          if (!cv) return
          const img = new Image()
          img.onload = () => { cv.getContext('2d').drawImage(img, 0, 0, CANVAS_SIZE, CANVAS_SIZE) }
          img.src = b.paint
        })
      }
    }).catch(e => setMsg(e.message))
  }, [])

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
    dirty.current = true
  }

  function handleDown(e) {
    e.preventDefault()
    drawing.current = true
    last.current = canvasPos(e)
    strokeTo({ x: last.current.x + 0.01, y: last.current.y })
  }
  function handleMove(e) {
    if (!drawing.current) return
    e.preventDefault()
    strokeTo(canvasPos(e))
  }
  function handleUp() { drawing.current = false }

  function clearCanvas() {
    const cv = canvasRef.current
    cv.getContext('2d').clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
    dirty.current = true
  }

  function handleImport(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const img = new Image()
    img.onload = () => {
      const ctx = canvasRef.current.getContext('2d')
      ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
      // fit the import into the cloth's usable middle
      const scale = Math.min((CANVAS_SIZE * 0.6) / img.width, (CANVAS_SIZE * 0.6) / img.height)
      const w = img.width * scale, h = img.height * scale
      ctx.drawImage(img, (CANVAS_SIZE - w) / 2, CANVAS_SIZE * 0.18, w, h)
      dirty.current = true
    }
    img.src = URL.createObjectURL(file)
    e.target.value = ''
  }

  function canvasIsEmpty() {
    const ctx = canvasRef.current.getContext('2d')
    const px = ctx.getImageData(0, 0, CANVAS_SIZE, CANVAS_SIZE).data
    for (let i = 3; i < px.length; i += 4) if (px[i] > 0) return false
    return true
  }

  async function handleSave() {
    setSaving(true)
    setMsg(null)
    try {
      let paint = null
      if (canvasRef.current && !canvasIsEmpty()) {
        paint = canvasRef.current.toDataURL('image/png')
      }
      await saveBanner(tier, emblem, paint)
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
    <div style={{
      position: 'fixed', inset: 0, zIndex: 300, background: 'rgba(5,5,10,0.92)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onClose}>
      <div className="card" style={{ width: 'min(880px, 94vw)', maxHeight: '92vh', overflowY: 'auto', padding: '1.5rem' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', margin: 0 }}>Banner Studio</h2>
          <button className="btn" onClick={onClose}>✕</button>
        </div>

        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
          {/* Live preview / paint surface */}
          <div style={{ flex: '0 0 320px' }}>
            <div style={{ position: 'relative', width: 320, height: 320, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
              <img src={`/icons/banners/banner_tier${tier}.png`} alt="" draggable={false}
                style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }} />
              <canvas
                ref={canvasRef}
                width={CANVAS_SIZE}
                height={CANVAS_SIZE}
                style={{
                  position: 'absolute', inset: 0, width: '100%', height: '100%',
                  cursor: mode === 'paint' ? 'crosshair' : 'default',
                  pointerEvents: mode === 'paint' ? 'auto' : 'none',
                  display: 'block',
                  touchAction: 'none',
                  WebkitMaskImage: `url(/icons/banners/banner_tier${tier}.png)`,
                  WebkitMaskSize: 'contain',
                  WebkitMaskPosition: 'center',
                  WebkitMaskRepeat: 'no-repeat',
                  maskImage: `url(/icons/banners/banner_tier${tier}.png)`,
                  maskSize: 'contain',
                  maskPosition: 'center',
                  maskRepeat: 'no-repeat'
                }}
                onMouseDown={handleDown} onMouseMove={handleMove} onMouseUp={handleUp} onMouseLeave={handleUp}
                onTouchStart={handleDown} onTouchMove={handleMove} onTouchEnd={handleUp}
              />
              {emblem && (
                <img src={`/icons/emblems/${emblem}.png`} alt="" draggable={false}
                  style={{ position: 'absolute', left: '28%', top: '28%', width: '44%', height: '44%', objectFit: 'contain', pointerEvents: 'none', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.6))' }} />
              )}
            </div>
            <div className="text-dim text-sm" style={{ marginTop: '0.5rem', textAlign: 'center' }}>
              This banner flies over your base, your battleship, and beside your name in the World.
            </div>
          </div>

          {/* Controls */}
          <div style={{ flex: 1, minWidth: 280 }}>
            {/* Cloth tier */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontFamily: 'Cinzel, serif', color: 'var(--text-hi)', marginBottom: '0.4rem' }}>Cloth</div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {[1, 2, 3, 4].map(t => (
                  <button key={t} className="btn" disabled={t > unlocked} onClick={() => setTier(t)}
                    title={t > unlocked ? `Unlocks when the Wall reaches its tier-${t} look` : ''}
                    style={{ padding: '0.2rem', border: tier === t ? '2px solid var(--gold)' : '2px solid transparent', opacity: t > unlocked ? 0.35 : 1 }}>
                    <img src={`/icons/banners/banner_tier${t}.png`} alt={`Tier ${t}`} width={52} height={52} style={{ objectFit: 'contain', display: 'block' }} />
                  </button>
                ))}
              </div>
              <div className="text-dim text-sm" style={{ marginTop: '0.3rem' }}>
                Higher cloth unlocks as the Wall's look evolves — but flying humble cloth at high level is a time-honored bait.
              </div>
            </div>

            {/* Mode toggle */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              <button className={`btn ${mode === 'emblem' ? 'btn-gold' : ''}`} onClick={() => setMode('emblem')} style={{ fontSize: '0.85rem' }}>Emblem</button>
              <button className={`btn ${mode === 'paint' ? 'btn-gold' : ''}`} onClick={() => setMode('paint')} style={{ fontSize: '0.85rem' }}>Paint Your Own</button>
            </div>

            {mode === 'emblem' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(64px, 1fr))', gap: '0.4rem' }}>
                <button className="btn" onClick={() => setEmblem(null)}
                  style={{ aspectRatio: '1', border: !emblem ? '2px solid var(--gold)' : '2px solid transparent', fontSize: '0.7rem' }}>
                  None
                </button>
                {(data.emblems || []).map(e => (
                  <button key={e} className="btn" onClick={() => setEmblem(e)}
                    style={{ aspectRatio: '1', padding: '0.3rem', border: emblem === e ? '2px solid var(--gold)' : '2px solid transparent' }}>
                    <img src={`/icons/emblems/${e}.png`} alt={e} style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }} />
                  </button>
                ))}
              </div>
            )}

            {mode === 'paint' && (
              <div>
                <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '0.6rem' }}>
                  {PALETTE.map(c => (
                    <button key={c} onClick={() => { setColor(c); setErasing(false) }}
                      style={{
                        width: 26, height: 26, borderRadius: '50%', background: c, cursor: 'pointer',
                        border: color === c && !erasing ? '2px solid var(--gold)' : '2px solid rgba(255,255,255,0.2)',
                      }} />
                  ))}
                  <input type="color" value={color} onChange={e => { setColor(e.target.value); setErasing(false) }}
                    style={{ width: 26, height: 26, padding: 0, border: 'none', background: 'none', cursor: 'pointer' }} title="Custom color" />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.6rem' }}>
                  <label className="text-dim text-sm">Brush</label>
                  <input type="range" min={3} max={48} value={brush} onChange={e => setBrush(parseInt(e.target.value))} style={{ flex: 1 }} />
                  <button className={`btn ${erasing ? 'btn-gold' : ''}`} onClick={() => setErasing(x => !x)} style={{ fontSize: '0.75rem' }}>Eraser</button>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="btn" onClick={clearCanvas} style={{ fontSize: '0.8rem' }}>Clear</button>
                  <label className="btn" style={{ fontSize: '0.8rem', cursor: 'pointer' }}>
                    Import PNG…
                    <input type="file" accept="image/png,image/jpeg,image/webp" onChange={handleImport} style={{ display: 'none' }} />
                  </label>
                </div>
                <div className="text-dim text-sm" style={{ marginTop: '0.5rem' }}>
                  Paint directly on the banner — or import a design your clan made. (Transparent PNGs work best!) Great bonding, questionable art optional.
                </div>
              </div>
            )}

            {msg && <div style={{ color: '#f87', fontSize: '0.85rem', marginTop: '0.75rem' }}>{msg}</div>}

            <button className="btn btn-gold" disabled={saving} onClick={handleSave}
              style={{ marginTop: '1rem', width: '100%', padding: '0.7rem' }}>
              {saving ? 'Raising the banner…' : 'Raise This Banner'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
