/*
 * THE HERALD — live. Editorial notices + featured edition come from
 * /herald/ (backend/data/herald_news.json), plus "tidings" aggregated
 * from game state (legacies, tower record, recruits, daily gates).
 * Falls back to the static shell if the backend is older than the endpoint.
 */
import React, { useState, useEffect } from 'react'
import { getHeraldFeed } from '../api/client'

const FALLBACK = {
  featured: {
    title: 'THE GATES OPEN',
    edition: 'VOL. I — THE FIRST ASCENT',
    body: 'The Tower stands open at last. What you carry into it is yours to lose — heroes die, and their deaths are not undone. But legacies endure, and the climb remembers every name. Climb well.',
    signoff: '— The Keepers',
  },
  notices: [
    { title: 'THE GATES OPEN', desc: 'The playtest begins — the Tower takes its first climbers', tag: 'NEW' },
    { title: 'KNOWN CRACKS IN THE STONE', desc: 'Issues the keepers are already mending' },
    { title: 'HOW TO REPORT A HAUNTING', desc: 'Found a bug? Send word through the mail raven' },
  ],
  tidings: [],
}

const TIDING_GLYPH = { legacy: '✝', record: '▲', recruit: '★', fallen: '◈', gates: '✦' }

function fmtCountdown(sec) {
  if (sec == null) return ''
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60)
  return ` Reseal in ${h}H ${String(m).padStart(2, '0')}M.`
}

export default function Herald({ onClose }) {
  const [feed, setFeed] = useState(FALLBACK)

  useEffect(() => {
    getHeraldFeed().then(setFeed).catch(() => { /* backend older than /herald */ })
  }, [])

  const featured = feed.featured || FALLBACK.featured

  return (
    <div className="ilm-herald">
      <button className="ilm-close" style={{ position: 'absolute', top: 18, right: 24, zIndex: 10 }} onClick={onClose}>✕</button>
      <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>TIDINGS</div>
      <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.4rem', color: 'var(--text-hi)', letterSpacing: '.04em', textShadow: '0 6px 40px rgba(124,58,214,.4)' }}>THE HERALD</div>
      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', marginTop: 2 }}>Word from the keepers of the Tower — read before you climb.</div>

      <div className="ilm-herald-grid">
        {/* notices + tidings */}
        <div>
          <div className="ilm-guild-sec"><span className="ilm-guild-secdot" /><span className="ilm-guild-seclabel">NOTICES</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {(feed.notices || []).map(n => (
              <div key={n.title} className="ilm-herald-notice">
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.82rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{n.title}</span>
                    {n.tag && <span className="ilm-chip" style={{ padding: '1px 7px', color: '#120c04', background: 'var(--gold)' }}>{n.tag}</span>}
                  </div>
                  <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.84rem' }}>{n.desc}</div>
                </div>
                <span style={{ color: 'var(--gold-dim)' }}>›</span>
              </div>
            ))}
          </div>

          {(feed.tidings || []).length > 0 && (
            <>
              <div className="ilm-guild-sec" style={{ marginTop: 18 }}><span className="ilm-guild-secdot" /><span className="ilm-guild-seclabel">TIDINGS FROM THE CLIMB</span></div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {feed.tidings.map((t, i) => (
                  <div key={`${t.kind}-${i}`} className="ilm-herald-notice">
                    <span style={{ color: 'var(--lavender)', width: 18, textAlign: 'center' }}>{TIDING_GLYPH[t.kind] || '◈'}</span>
                    <div style={{ flex: 1 }}>
                      <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: '0.78rem', letterSpacing: '.06em', color: 'var(--text-hi)' }}>{t.title}</span>
                      <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: '0.84rem' }}>
                        {t.desc}{t.kind === 'gates' ? fmtCountdown(t.resets_in_seconds) : ''}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
          <div className="ilm-micro" style={{ color: 'var(--muted)', marginTop: 8, fontStyle: 'italic' }}>Older editions are kept in the archive below.</div>
        </div>

        {/* featured */}
        <div className="ilm-herald-featured">
          <span className="ilm-corner" /><span className="ilm-corner ilm-corner-r" />
          <div className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>FEATURED NOTICE · LATEST EDITION</div>
          <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '1.8rem', color: 'var(--text-hi)', marginTop: 8 }}>{featured.title}</div>
          <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.2em', fontSize: '0.6rem', color: 'var(--gold-hi)', marginTop: 4 }}>{featured.edition}</div>
          <div style={{ fontStyle: 'italic', color: '#c8b8dd', marginTop: 14, lineHeight: 1.7 }}>{featured.body}</div>
          <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.16em', fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: 16, textAlign: 'right' }}>{featured.signoff}</div>
          <button className="ilm-btn ilm-btn-gold ilm-btn-block" style={{ marginTop: 18 }} onClick={onClose}>CONTINUE TO THE TOWER</button>
        </div>
      </div>
    </div>
  )
}
