import React, { useState, useEffect } from 'react'

// Promise-based replacement for native confirm()/alert() — the OS popups
// broke theme immersion completely inside the desktop shell. Call sites
// just `await confirmDialog(msg)` / `alertDialog(msg)`; if the host isn't
// mounted yet (e.g. very early startup) they fall back to the native ones.
let dialogHandler = null

export function confirmDialog(message, opts = {}) {
  if (!dialogHandler) return Promise.resolve(window.confirm(message))
  return dialogHandler({ type: 'confirm', message, ...opts })
}

export function alertDialog(message, opts = {}) {
  if (!dialogHandler) { window.alert(message); return Promise.resolve(true) }
  return dialogHandler({ type: 'alert', message, ...opts })
}

export default function DialogHost() {
  const [dialog, setDialog] = useState(null)

  useEffect(() => {
    dialogHandler = (opts) => new Promise(resolve => setDialog({ ...opts, resolve }))
    return () => { dialogHandler = null }
  }, [])

  useEffect(() => {
    if (!dialog) return
    const onKey = (e) => {
      if (e.key === 'Escape') close(dialog.type !== 'confirm')
      if (e.key === 'Enter') close(true)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [dialog])

  if (!dialog) return null

  function close(value) {
    dialog.resolve(value)
    setDialog(null)
  }

  const isConfirm = dialog.type === 'confirm'
  // Destructive confirmations get red accents without every call site
  // having to say so explicitly.
  const danger = dialog.danger ?? /permanent|delete|dismiss|wipe|destroy|scrap|cannot be undone|warning/i.test(dialog.message)
  const accent = danger ? 'var(--red)' : 'var(--gold)'

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 2000,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        backdropFilter: 'blur(4px)',
      }}
      onClick={() => close(!isConfirm)}
    >
      <div
        className="card"
        style={{ width: 440, maxWidth: '92vw', padding: '1.8rem', borderColor: accent, borderWidth: 1 }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.05rem', letterSpacing: '0.06em', color: accent, marginBottom: '0.9rem' }}>
          {dialog.title || (isConfirm ? (danger ? 'Are You Sure?' : 'Confirm') : 'Notice')}
        </div>
        <div style={{ whiteSpace: 'pre-line', lineHeight: 1.6, marginBottom: '1.5rem', color: 'var(--text-hi)' }}>
          {dialog.message}
        </div>
        <div style={{ display: 'flex', gap: '0.8rem', justifyContent: 'flex-end' }}>
          {isConfirm && (
            <button className="btn" onClick={() => close(false)}>
              {dialog.cancelLabel || 'Cancel'}
            </button>
          )}
          <button
            className={`btn ${danger ? 'btn-danger' : 'btn-gold'}`}
            autoFocus
            onClick={() => close(true)}
          >
            {dialog.confirmLabel || (isConfirm ? 'Confirm' : 'OK')}
          </button>
        </div>
      </div>
    </div>
  )
}
