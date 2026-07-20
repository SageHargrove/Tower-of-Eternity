/*
 * THE ATHENAEUM — the research map (mockup 2A, Research & Chatter explorations).
 *
 * Five disciplines as horizontal rows of four studies, second-order
 * confluence knots on the far right that unseal when both parent
 * disciplines are mastered. One node is IN STUDY at a time — the scholars'
 * whole Insight rate flows into it (see backend athenaeum_service.py).
 *
 * Interactions per the design pass: click a node to load it into the
 * SELECTED panel on the left (that's where RESEARCH lives), drag to pan,
 * scroll to zoom, and the bottom-right minimap is live — it shows the
 * viewport and drags/clicks to move it. Connector lines are progress-aware:
 * solid into completed studies, proportionally solid-then-dotted into the
 * node in study (62% studied = 62% of its line solid), dotted beyond.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { getAthenaeumState, studyAthenaeumNode } from '../api/client'
import { useBgmScene } from '../useBgmScene'
import { alertDialog } from './DialogHost'

// ── canvas geometry (unscaled units) ──────────────────────────────────────
const ROW_Y0 = 100, ROW_GAP = 200
const NODE_W = 240, NODE_H = 76, NODE_X0 = 250, NODE_XGAP = 300
const ROW_END_X = NODE_X0 + 3 * NODE_XGAP + NODE_W // right edge of tier-4 nodes
const KNOT_X = 1520                                 // confluence knot center
const CONF_X0 = 1650                                // confluence tree first node
const CANVAS_W = 3000, CANVAS_H = 1120
const MINIMAP_W = 210
const MM_SCALE = MINIMAP_W / CANVAS_W

const rowCenterY = (i) => ROW_Y0 + i * ROW_GAP + NODE_H / 2

// Knot centers are hand-placed so the three confluence trees never crowd
// each other, whatever rows their parents sit on.
const KNOT_Y = { war_sorcery: 240, warders_march: 640, wild_arcana: 880 }

const STATE_STYLE = {
  complete:  { border: '1px solid rgba(120,200,180,.55)', title: '#9fd6c8', bg: 'rgba(16,28,26,.55)' },
  studying:  { border: '1px solid var(--gold)', title: 'var(--gold-hi)', bg: 'rgba(30,22,10,.6)', glow: '0 0 14px rgba(184,151,98,.35)' },
  paused:    { border: '1px solid rgba(214,178,110,.45)', title: '#d6b26e', bg: 'rgba(24,18,10,.5)' },
  available: { border: '1px solid rgba(150,130,190,.45)', title: '#b9a8d8', bg: 'rgba(18,12,30,.55)' },
  locked:    { border: '1px dashed rgba(150,130,190,.3)', title: '#6f6488', bg: 'rgba(12,8,22,.4)' },
}

function nodeHeader(n) {
  if (n.status === 'complete') return n.name.toUpperCase()
  if (n.status === 'studying') return `IN STUDY · ${n.pct}%`
  if (n.status === 'paused') return `PAUSED · ${n.pct}%`
  if (n.status === 'locked') return n.aether_cost > 0 ? `LOCKED · ${n.aether_cost} AETHER` : 'LOCKED'
  return n.name.toUpperCase()
}

/* Progress-aware connector into a node: solid for the studied fraction,
 * dotted for the rest. Complete = all solid; untouched = all dotted. */
function Connector({ x, y, width, node, prevComplete }) {
  let solidPct = 0
  if (node.status === 'complete') solidPct = 100
  else if (node.status === 'studying' || node.status === 'paused') solidPct = node.pct
  else if (node.status === 'available' && prevComplete) solidPct = 0
  const solidW = Math.round(width * solidPct / 100)
  return (
    <div style={{ position: 'absolute', left: x, top: y, width, height: 1, pointerEvents: 'none' }}>
      {solidW > 0 && <span style={{ position: 'absolute', left: 0, top: 0, width: solidW, height: 1, background: node.status === 'complete' ? 'rgba(120,200,180,.5)' : 'var(--gold)' }} />}
      {solidW < width && <span style={{ position: 'absolute', left: solidW, top: 0, width: width - solidW, height: 0, borderTop: '1px dotted rgba(150,130,190,.4)' }} />}
    </div>
  )
}

function NodeBox({ node, x, y, selected, active, onSelect }) {
  const st = STATE_STYLE[node.status] || STATE_STYLE.locked
  return (
    <div
      onClick={(e) => { e.stopPropagation(); onSelect() }}
      style={{
        position: 'absolute', left: x, top: y, width: NODE_W, height: NODE_H,
        border: st.border, background: st.bg, cursor: 'pointer', padding: '10px 14px',
        boxShadow: (node.status === 'studying' ? st.glow : 'none') + (selected ? ', 0 0 0 1px var(--gold-hi)' : ''),
        opacity: node.status === 'locked' ? 0.75 : 1, boxSizing: 'border-box',
      }}
    >
      <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.18em', fontSize: '0.56rem', color: st.title, whiteSpace: 'nowrap', overflow: 'hidden' }}>
        {nodeHeader(node)}
      </div>
      <div style={{ fontStyle: 'italic', fontSize: '0.78rem', color: node.status === 'locked' ? '#7d7295' : '#cfc2e2', marginTop: 4, whiteSpace: 'nowrap', overflow: 'hidden' }}>
        {node.status === 'studying' || node.status === 'paused' ? node.name : node.desc}
      </div>
      {(node.status === 'studying' || node.status === 'paused') && (
        <div style={{ marginTop: 7, height: 4, background: 'rgba(255,255,255,.08)', position: 'relative' }}>
          <span style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${node.pct}%`, background: 'linear-gradient(90deg, var(--violet), var(--gold))' }} />
        </div>
      )}
    </div>
  )
}

function EmblemDiamond({ x, y, sigil, name, sub, lit, onSelect, selected }) {
  return (
    <div onClick={(e) => { e.stopPropagation(); onSelect?.() }} style={{ position: 'absolute', left: x - 55, top: y - 55, width: 110, textAlign: 'center', cursor: onSelect ? 'pointer' : 'default' }}>
      <div style={{
        width: 62, height: 62, margin: '0 auto', transform: 'rotate(45deg)',
        border: `1px solid ${lit ? 'var(--gold)' : 'rgba(150,130,190,.4)'}`,
        background: lit ? 'rgba(30,22,10,.5)' : 'rgba(14,9,26,.5)',
        boxShadow: (lit ? '0 0 16px rgba(184,151,98,.3)' : 'none') + (selected ? ', 0 0 0 1px var(--gold-hi)' : ''),
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ transform: 'rotate(-45deg)', fontSize: 20, color: lit ? 'var(--gold-hi)' : '#8d80ab' }}>{sigil}</span>
      </div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.14em', fontSize: '0.62rem', color: 'var(--text-hi)', marginTop: 14 }}>{name.toUpperCase()}</div>
      <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: '0.5rem', color: lit ? 'var(--gold)' : 'var(--muted)', marginTop: 3 }}>{sub}</div>
    </div>
  )
}

const TIER_ROMAN = ['I', 'II', 'III', 'IV']
const tierLabel = (t) => t.mastered ? 'MASTERED' : `TIER ${TIER_ROMAN[Math.min(t.tiers_done, 3)]}`

export default function AthenaeumPanel({ aether, onResourceChange }) {
  useBgmScene('athenaeum')  // candlelit study bed
  const [state, setState] = useState(null)
  const [selected, setSelected] = useState(null) // {treeId, nodeId} | {treeId, knot:true}
  const [busy, setBusy] = useState(false)
  const [pan, setPan] = useState({ x: 20, y: 10 })
  const [zoom, setZoom] = useState(0.8)
  const [flying, setFlying] = useState(false)
  const viewRef = useRef(null)
  const dragRef = useRef(null)
  const draggedRef = useRef(false)
  const [viewSize, setViewSize] = useState({ w: 900, h: 560 })

  const load = useCallback(async () => {
    try {
      const s = await getAthenaeumState()
      setState(s)
      // Default selection: the active study, else stay on the user's pick.
      setSelected(sel => sel || (s.active_node ? { nodeId: s.active_node } : null))
    } catch (e) { console.error(e) }
  }, [])

  useEffect(() => {
    load()
    const iv = setInterval(load, 20000)
    return () => clearInterval(iv)
  }, [load])

  useEffect(() => {
    const el = viewRef.current
    if (!el) return
    const measure = () => setViewSize({ w: el.clientWidth, h: el.clientHeight })
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [])

  const clampPan = useCallback((p, z) => ({
    x: Math.min(120, Math.max(-(CANVAS_W * z - viewSize.w + 120), p.x)),
    y: Math.min(80, Math.max(-(CANVAS_H * z - viewSize.h + 80), p.y)),
  }), [viewSize])

  // Wheel zoom around the cursor — attached manually so preventDefault works
  // (React's synthetic wheel listeners are passive).
  useEffect(() => {
    const el = viewRef.current
    if (!el) return
    const onWheel = (e) => {
      e.preventDefault()
      const rect = el.getBoundingClientRect()
      const mx = e.clientX - rect.left, my = e.clientY - rect.top
      setZoom(z => {
        const nz = Math.min(1.6, Math.max(0.35, z * (e.deltaY > 0 ? 0.9 : 1.111)))
        setPan(p => clampPan({ x: mx - (mx - p.x) * (nz / z), y: my - (my - p.y) * (nz / z) }, nz))
        return nz
      })
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [clampPan])

  function startDrag(e) {
    dragRef.current = { sx: e.clientX, sy: e.clientY, px: pan.x, py: pan.y }
    draggedRef.current = false
    const move = (ev) => {
      const d = dragRef.current
      if (!d) return
      const dx = ev.clientX - d.sx, dy = ev.clientY - d.sy
      if (Math.abs(dx) + Math.abs(dy) > 4) draggedRef.current = true
      if (draggedRef.current) setPan(clampPan({ x: d.px + dx, y: d.py + dy }, zoom))
    }
    const up = () => {
      dragRef.current = null
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseup', up)
      setTimeout(() => { draggedRef.current = false }, 0)
    }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
  }

  function select(nodeId) {
    if (draggedRef.current) return
    setSelected({ nodeId })
  }

  function flyTo(cx, cy) {
    setFlying(true)
    setPan(clampPan({ x: viewSize.w / 2 - cx * zoom, y: viewSize.h / 2 - cy * zoom }, zoom))
    setTimeout(() => setFlying(false), 650)
  }

  function minimapJump(e) {
    const rect = e.currentTarget.getBoundingClientRect()
    const cx = (e.clientX - rect.left) / MM_SCALE
    const cy = (e.clientY - rect.top) / MM_SCALE
    setPan(clampPan({ x: viewSize.w / 2 - cx * zoom, y: viewSize.h / 2 - cy * zoom }, zoom))
  }
  function minimapDrag(e) {
    e.stopPropagation()
    minimapJump(e)
    const el = e.currentTarget
    const move = (ev) => minimapJump({ currentTarget: el, clientX: ev.clientX, clientY: ev.clientY })
    const up = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
  }

  async function handleStudy(nodeId) {
    setBusy(true)
    try {
      await studyAthenaeumNode(nodeId)
      await load()
      onResourceChange?.()
    } catch (e) {
      alertDialog(e.message)
    } finally { setBusy(false) }
  }

  if (!state) return <div className="text-dim" style={{ padding: '2rem', fontStyle: 'italic' }}>Unrolling the charts…</div>
  if (!state.built) return null

  const trees = [...state.disciplines, ...state.confluences]
  const findNode = (nid) => {
    for (const t of trees) { const n = t.nodes.find(n => n.id === nid); if (n) return { tree: t, node: n } }
    return null
  }
  const sel = selected?.knotId
    ? { knot: state.confluences.find(c => c.id === selected.knotId) }
    : (selected?.nodeId ? findNode(selected.nodeId) : null)

  // ── left-rail SELECTED panel content ──
  function renderSelected() {
    if (!sel) return <div className="text-dim" style={{ fontSize: '0.8rem', fontStyle: 'italic' }}>Select a study on the map.</div>
    if (sel.knot) {
      const c = sel.knot
      const cy = KNOT_Y[c.id] || 240
      return (
        <>
          <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: '0.56rem', color: c.unsealed ? 'var(--gold)' : 'var(--muted)' }}>
            {c.unsealed ? '◆ CONFLUENCE · UNSEALED' : '◇ CONFLUENCE · SEALED'}
          </div>
          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.15rem', color: 'var(--text-hi)', margin: '6px 0 4px' }}>{c.name.toUpperCase()}</div>
          <div style={{ fontStyle: 'italic', fontSize: '0.8rem', color: '#b9a8d8', lineHeight: 1.45 }}>{c.flavor}</div>
          <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: 8 }}>
            {c.unsealed ? `A tree of ${c.nodes.length} awaits.` : 'Master both parent disciplines to unseal.'}
          </div>
          {c.unsealed && (
            <button className="ilm-btn" style={{ marginTop: 10 }} onClick={() => flyTo(CONF_X0 + NODE_W, cy)}>GO TO TREE ›</button>
          )}
        </>
      )
    }
    const { tree, node } = sel
    const canAfford = node.aether_cost <= (state.aether ?? aether ?? 0)
    return (
      <>
        <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: '0.56rem', color: 'var(--gold)' }}>
          ◆ SELECTED · {tree.name.toUpperCase()} · TIER {TIER_ROMAN[node.tier - 1]}
        </div>
        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.15rem', color: 'var(--text-hi)', margin: '6px 0 4px' }}>{node.name.toUpperCase()}</div>
        <div style={{ fontStyle: 'italic', fontSize: '0.85rem', color: '#c8b8dd' }}>{node.desc}</div>
        <div style={{ fontSize: '0.7rem', color: 'var(--muted)', marginTop: 8 }}>
          {node.insight_cost} Insight{node.aether_cost > 0 ? ` · ${node.aether_cost} Aether to unseal` : ''}
        </div>
        {node.status === 'complete' && (
          <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.18em', fontSize: '0.66rem', color: '#9fd6c8', marginTop: 10 }}>✓ MASTERED</div>
        )}
        {node.status === 'studying' && (
          <div style={{ marginTop: 10 }}>
            <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.18em', fontSize: '0.66rem', color: 'var(--gold-hi)' }}>IN STUDY · {node.pct}%</div>
            <div style={{ marginTop: 6, height: 5, background: 'rgba(255,255,255,.08)' }}>
              <div style={{ height: '100%', width: `${node.pct}%`, background: 'linear-gradient(90deg, var(--violet), var(--gold))' }} />
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--muted)', marginTop: 5, fontStyle: 'italic' }}>The scholars are on it.</div>
          </div>
        )}
        {(node.status === 'available' || node.status === 'paused') && (
          <button className="ilm-btn ilm-btn-gold" disabled={busy || !canAfford} onClick={() => handleStudy(node.id)} style={{ marginTop: 10 }}>
            {node.status === 'paused' ? 'RESUME STUDY' : (node.aether_cost > 0 ? `RESEARCH · ${node.aether_cost} AETHER` : 'RESEARCH')}
          </button>
        )}
        {node.status === 'available' && !canAfford && node.aether_cost > 0 && (
          <div style={{ fontSize: '0.68rem', color: '#d98a8a', marginTop: 6 }}>Not enough Aether.</div>
        )}
        {node.status === 'locked' && (
          <div style={{ fontSize: '0.72rem', color: '#8d80ab', marginTop: 10, fontStyle: 'italic' }}>
            {node.tier === 1 ? 'The confluence is still sealed.' : 'Complete the previous study first.'}
          </div>
        )}
      </>
    )
  }

  // ── map canvas contents ──
  const canvas = []
  state.disciplines.forEach((d, i) => {
    const cy = rowCenterY(i)
    canvas.push(
      <EmblemDiamond key={`em-${d.id}`} x={110} y={cy} sigil={d.sigil} name={d.name} sub={tierLabel(d)}
        lit={d.mastered || d.nodes.some(n => n.status === 'studying')} />
    )
    d.nodes.forEach((n, t) => {
      const x = NODE_X0 + t * NODE_XGAP
      canvas.push(<Connector key={`cn-${n.id}`} x={x - 60} y={cy} width={60} node={n} prevComplete={t === 0 ? true : d.nodes[t - 1].status === 'complete'} />)
      canvas.push(<NodeBox key={n.id} node={n} x={x} y={cy - NODE_H / 2} selected={selected?.nodeId === n.id} onSelect={() => select(n.id)} />)
    })
  })

  // Confluence braids (SVG under the boxes), knots, and their trees.
  const braids = []
  state.confluences.forEach(c => {
    const ky = KNOT_Y[c.id] || 240
    c.parents.forEach(pid => {
      const pi = state.disciplines.findIndex(d => d.id === pid)
      if (pi < 0) return
      const py = rowCenterY(pi)
      const d = `M ${ROW_END_X + 8} ${py} C ${ROW_END_X + 90} ${py}, ${KNOT_X - 120} ${ky}, ${KNOT_X - 36} ${ky}`
      braids.push(
        <path key={`${c.id}-${pid}`} d={d} fill="none"
          stroke={c.unsealed ? 'var(--gold)' : 'rgba(150,130,190,.35)'}
          strokeWidth="1" strokeDasharray={c.unsealed ? 'none' : '2 5'} opacity={c.unsealed ? 0.75 : 0.6} />
      )
    })
    canvas.push(
      <EmblemDiamond key={`knot-${c.id}`} x={KNOT_X} y={ky} sigil={c.sigil} name={c.name}
        sub={c.unsealed ? (c.mastered ? 'MASTERED' : 'UNSEALED') : 'SEALED'} lit={c.unsealed}
        selected={selected?.knotId === c.id}
        onSelect={() => { if (!draggedRef.current) setSelected({ knotId: c.id }) }} />
    )
    if (c.unsealed) {
      c.nodes.forEach((n, t) => {
        const x = CONF_X0 + t * NODE_XGAP
        canvas.push(<Connector key={`cn-${n.id}`} x={x - 60} y={ky} width={60} node={n} prevComplete={t === 0 ? true : c.nodes[t - 1].status === 'complete'} />)
        canvas.push(<NodeBox key={n.id} node={n} x={x} y={ky - NODE_H / 2} selected={selected?.nodeId === n.id} onSelect={() => select(n.id)} />)
      })
      // stub from knot into its first node
      canvas.push(<Connector key={`stub-${c.id}`} x={KNOT_X + 36} y={ky} width={CONF_X0 - KNOT_X - 96} node={c.nodes[0]} prevComplete={true} />)
    }
  })

  const mmColor = { complete: 'rgba(120,200,180,.8)', studying: 'var(--gold)', paused: '#d6b26e', available: 'rgba(150,130,190,.7)', locked: 'rgba(150,130,190,.3)' }

  return (
    <div style={{ display: 'flex', gap: 20, marginTop: '1.2rem', alignItems: 'stretch' }}>
      {/* ═══ left rail ═══ */}
      <div style={{ width: 280, flex: 'none', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div>
          <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: '0.56rem', color: 'var(--gold)' }}>◆ THE WEAVE · GLOBAL RESEARCH</div>
          <div style={{ fontStyle: 'italic', fontSize: '0.82rem', color: '#b0a3c9', lineHeight: 1.5, marginTop: 8 }}>
            Where the company's scholars deepen a discipline — and weave two into a working no single school could hold.
          </div>
        </div>

        <div style={{ border: '1px solid rgba(150,130,190,.3)', background: 'rgba(12,7,24,.5)', padding: '12px 14px' }}>
          <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: '0.54rem', color: 'var(--muted)' }}>INSIGHT RATE</div>
          <div style={{ marginTop: 6, display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.3rem', color: 'var(--text-hi)' }}>+{state.insight_rate}</span>
            <span style={{ fontStyle: 'italic', fontSize: '0.72rem', color: 'var(--muted)' }}>/hr · {state.scholars} scholar{state.scholars === 1 ? '' : 's'}</span>
          </div>
          {state.scholars === 0 && (
            <div style={{ fontSize: '0.66rem', color: '#d6b26e', marginTop: 5, fontStyle: 'italic' }}>Assign scholars above — Mages and Magic Engineers study fastest.</div>
          )}
        </div>

        <div style={{ border: `1px solid ${sel && !sel.knot && (sel.node.status === 'available' || sel.node.status === 'paused') ? 'var(--gold)' : 'rgba(150,130,190,.3)'}`, background: 'linear-gradient(160deg,rgba(24,14,40,.6),rgba(12,7,24,.6))', padding: '13px 15px' }}>
          {renderSelected()}
        </div>

        <div>
          <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: '0.54rem', color: 'var(--muted)', marginBottom: 8 }}>DISCIPLINES</div>
          {trees.map(t => {
            const isConf = !!t.parents
            const status = isConf && !t.unsealed ? 'SEALED' : tierLabel(t)
            return (
              <div key={t.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0', cursor: 'pointer' }}
                onClick={() => {
                  const i = state.disciplines.findIndex(d => d.id === t.id)
                  flyTo(i >= 0 ? NODE_X0 + 1.5 * NODE_XGAP : CONF_X0 + NODE_W, i >= 0 ? rowCenterY(i) : (KNOT_Y[t.id] || 240))
                }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', display: 'inline-block', flex: 'none', background: t.mastered ? 'var(--gold)' : 'transparent', border: t.mastered ? 'none' : '1px solid rgba(150,130,190,.5)' }} />
                  <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.1em', fontSize: '0.68rem', color: isConf && !t.unsealed ? '#6f6488' : 'var(--text-hi)' }}>{t.name.toUpperCase()}</span>
                </span>
                <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.16em', fontSize: '0.54rem', color: t.mastered ? 'var(--gold)' : 'var(--muted)' }}>{status}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* ═══ map viewport ═══ */}
      <div ref={viewRef} onMouseDown={startDrag}
        style={{ flex: 1, minWidth: 0, height: 580, position: 'relative', overflow: 'hidden', border: '1px solid rgba(150,130,190,.25)', background: 'radial-gradient(ellipse at 30% 20%, rgba(30,18,52,.5), rgba(8,5,16,.7))', cursor: dragRef.current ? 'grabbing' : 'grab', userSelect: 'none' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: CANVAS_W, height: CANVAS_H, transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: '0 0', transition: flying ? 'transform .6s cubic-bezier(.25,.8,.3,1)' : 'none' }}>
          <svg width={CANVAS_W} height={CANVAS_H} style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}>{braids}</svg>
          {canvas}
        </div>

        {/* zoom buttons */}
        <div style={{ position: 'absolute', top: 12, right: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {[['+', 1.2], ['−', 1 / 1.2]].map(([label, f]) => (
            <button key={label} onMouseDown={e => e.stopPropagation()} onClick={() => {
              const nz = Math.min(1.6, Math.max(0.35, zoom * f))
              setPan(p => clampPan({ x: viewSize.w / 2 - (viewSize.w / 2 - p.x) * (nz / zoom), y: viewSize.h / 2 - (viewSize.h / 2 - p.y) * (nz / zoom) }, nz))
              setZoom(nz)
            }} style={{ width: 30, height: 30, border: '1px solid rgba(150,130,190,.4)', background: 'rgba(12,7,24,.8)', color: 'var(--text-hi)', cursor: 'pointer', fontSize: 15 }}>{label}</button>
          ))}
        </div>

        {/* hint */}
        <div style={{ position: 'absolute', left: 14, bottom: 12, display: 'flex', alignItems: 'center', gap: 10, pointerEvents: 'none' }}>
          <span style={{ width: 26, height: 14, border: '1px solid rgba(150,130,190,.4)', borderRadius: 8, display: 'inline-flex', alignItems: 'center', paddingLeft: 3 }}><span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--gold)' }} /></span>
          <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.22em', fontSize: '0.56rem', color: 'var(--muted)' }}>DRAG TO PAN · SCROLL TO ZOOM</span>
        </div>

        {/* minimap — live: shows the viewport, drag it to move */}
        <div onMouseDown={minimapDrag}
          style={{ position: 'absolute', right: 12, bottom: 12, width: MINIMAP_W, height: Math.round(CANVAS_H * MM_SCALE), border: '1px solid rgba(150,130,190,.35)', background: 'rgba(8,5,16,.85)', cursor: 'pointer', overflow: 'hidden' }}>
          {trees.flatMap(t => {
            const i = state.disciplines.findIndex(d => d.id === t.id)
            const isConf = i < 0
            if (isConf && !t.unsealed) {
              const ky = KNOT_Y[t.id] || 240
              return [<span key={`mm-${t.id}`} style={{ position: 'absolute', left: KNOT_X * MM_SCALE - 2, top: ky * MM_SCALE - 2, width: 4, height: 4, transform: 'rotate(45deg)', border: '1px solid rgba(150,130,190,.5)' }} />]
            }
            const cy = isConf ? (KNOT_Y[t.id] || 240) : rowCenterY(i)
            const x0 = isConf ? CONF_X0 : NODE_X0
            return t.nodes.map((n, ti) => (
              <span key={`mm-${n.id}`} style={{ position: 'absolute', left: (x0 + ti * NODE_XGAP) * MM_SCALE, top: cy * MM_SCALE - 2, width: NODE_W * MM_SCALE, height: 4, background: mmColor[n.status] }} />
            ))
          })}
          <span style={{ position: 'absolute', left: (-pan.x / zoom) * MM_SCALE, top: (-pan.y / zoom) * MM_SCALE, width: (viewSize.w / zoom) * MM_SCALE, height: (viewSize.h / zoom) * MM_SCALE, border: '1px solid var(--gold)', boxSizing: 'border-box', pointerEvents: 'none' }} />
        </div>
      </div>
    </div>
  )
}
