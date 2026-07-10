/*
 * MISSIVES — the Mailbox modal (Illuminated). Two-pane: list of mail on the
 * left, selected message + enclosed rewards on the right. Wired to the real
 * /base/mail endpoints.
 */
import React, { useEffect, useState } from 'react'
import { getMailList, claimMail } from '../api/client'
import { Diamond, SectionHeader, IlmButton } from './ilm/Ilm'

function parseRewards(m) {
  try { return JSON.parse(m.rewards_json || '{}') } catch { return {} }
}
function hasRewards(m) {
  const r = parseRewards(m)
  return Object.values(r).some(v => Number(v) > 0)
}

const REWARD_META = {
  gems:        { label: 'GEMS',        color: 'var(--violet)',  glow: true },
  gold:        { label: 'GOLD',        color: 'var(--gold-hi)' },
  ingredients: { label: 'INGREDIENTS', color: 'var(--green-hi)' },
  aether:      { label: 'AETHER',      color: 'var(--lavender)' },
}

export default function Mailbox({ onClose, onChange }) {
  const [mail, setMail] = useState([])
  const [sel, setSel] = useState(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      const rows = await getMailList()
      const list = Array.isArray(rows) ? rows : (rows.mail || [])
      setMail(list)
      setSel(prev => list.find(m => m.id === prev?.id) || list[0] || null)
    } catch { setMail([]) }
  }
  useEffect(() => { load() }, [])

  const unread = mail.filter(m => !m.is_read).length
  const claimable = mail.filter(m => hasRewards(m) && !m.is_claimed)

  async function claim(id) {
    if (busy) return
    setBusy(true)
    try { await claimMail(id) } catch {}
    setBusy(false)
    await load(); onChange && onChange()
  }
  async function claimAll() {
    if (busy) return
    setBusy(true)
    for (const m of claimable) { try { await claimMail(m.id) } catch {} }
    setBusy(false)
    await load(); onChange && onChange()
  }

  const selRewards = sel ? parseRewards(sel) : {}

  return (
    <div className="ilm-modal-scrim" onClick={onClose}>
      <div className="ilm-mailbox ent-fade" onClick={e => e.stopPropagation()}>
        <span className="ilm-corner" />
        <span className="ilm-corner ilm-corner-r" />

        {/* header */}
        <div className="ilm-mailbox-head">
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}>
            <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.4rem', color: 'var(--text-hi)' }}>MISSIVES</span>
            <span style={{ fontFamily: "'Cinzel',serif", fontSize: '0.62rem', letterSpacing: '0.24em', color: 'var(--gold-hi)' }}>
              {unread} UNREAD
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {claimable.length > 0 && (
              <IlmButton variant="gold" onClick={claimAll} disabled={busy} style={{ animation: 'claim-glow 3s ease-in-out infinite' }}>
                CLAIM ALL
              </IlmButton>
            )}
            <button className="ilm-close" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* body */}
        <div className="ilm-mailbox-body">
          {/* list */}
          <div className="ilm-mailbox-list">
            {mail.length === 0 && (
              <div className="text-dim" style={{ padding: '2rem 1rem', textAlign: 'center', fontStyle: 'italic' }}>
                No missives. The raven rests.
              </div>
            )}
            {mail.map(m => {
              const rewards = hasRewards(m) && !m.is_claimed
              return (
                <div
                  key={m.id}
                  className={`ilm-mail-row ${sel?.id === m.id ? 'sel' : ''} ${m.is_read ? 'read' : ''}`}
                  onClick={() => setSel(m)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {!m.is_read && <span className="ilm-mail-unread" />}
                    <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.72rem', letterSpacing: '0.08em', color: m.is_read ? 'var(--text)' : 'var(--text-hi)', flex: 1 }}>
                      {m.subject}
                    </span>
                  </div>
                  <div className="text-dim" style={{ fontSize: '0.78rem', marginTop: 4 }}>
                    {m.sender}{rewards ? ' · gifts enclosed' : ''}
                  </div>
                </div>
              )
            })}
          </div>

          {/* detail */}
          <div className="ilm-mailbox-detail">
            {sel ? (
              <>
                <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '0.3em', fontSize: '0.56rem', color: 'var(--gold-hi)' }}>
                  FROM {sel.sender?.toUpperCase()}
                </div>
                <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.3rem', color: 'var(--text-hi)', marginTop: 6 }}>
                  {sel.subject}
                </div>
                <div style={{ fontSize: '1rem', fontStyle: 'italic', color: '#c8b8dd', lineHeight: 1.6, marginTop: 12 }}>
                  {sel.body}
                </div>

                {hasRewards(sel) && (
                  <div style={{ marginTop: 20 }}>
                    <SectionHeader style={{ marginBottom: 12 }}>ENCLOSED</SectionHeader>
                    <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
                      {Object.entries(selRewards).filter(([, v]) => Number(v) > 0).map(([k, v]) => {
                        const meta = REWARD_META[k] || { label: k.toUpperCase(), color: 'var(--gold-hi)' }
                        return (
                          <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 10, border: '1px solid var(--border)', background: 'rgba(12,7,24,.5)', padding: '10px 16px' }}>
                            <Diamond size={12} color={meta.color} glow={meta.glow ? meta.color : false} />
                            <span style={{ fontWeight: 700, fontSize: '1.25rem', color: '#efe8da' }}>×{Number(v).toLocaleString()}</span>
                            <span className="ilm-micro">{meta.label}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                <div className="ilm-mailbox-actions">
                  {hasRewards(sel) && (
                    sel.is_claimed
                      ? <span className="text-dim" style={{ fontFamily: "'Cinzel',serif", letterSpacing: '0.22em', fontSize: '0.68rem', color: 'var(--green-hi)' }}>CLAIMED</span>
                      : <IlmButton variant="gold" onClick={() => claim(sel.id)} disabled={busy} style={{ animation: 'claim-glow 3s ease-in-out infinite' }}>CLAIM</IlmButton>
                  )}
                </div>
              </>
            ) : (
              <div className="text-dim" style={{ margin: 'auto', fontStyle: 'italic' }}>Select a missive.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
