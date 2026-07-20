/*
 * DEATH CEREMONY — the rite when a hero dies permanently: portrait, epitaph,
 * final tally, and the legacy they forge for the living. Fired from
 * TowerPage on combat dead_heroes; a real hero object is normalized to the
 * ceremony's fields, no hero at all falls back to the preview mock (MoreHub).
 */
import React from 'react'

export default function DeathCeremony({ hero, onClose }) {
  const h = hero ? {
    id: hero.id,
    name: hero.name,
    title: hero.title || 'the Unnamed',
    hero_class: hero.hero_class || 'Classless',
    level: hero.level || 1,
    floor: hero.floor ?? hero.floors_survived ?? '?',
    eulogy: hero.eulogy || hero.personality ||
      'The Tower does not give back what it takes. But the climb remembers every name carved into it — and this one is carved deep.',
    kills: hero.lifetime_kills ?? hero.kills ?? 0,
    floors: hero.floors_survived ?? 0,
    missions: hero.missions_completed ?? 0,
    loyalty: hero.affinity ?? 0,
    legacy: hero.legacy || 'A legacy being written',
  } : {
    name: 'ORION SHADOW', title: 'the Silent Blade', hero_class: 'Rogue', level: 62, floor: 47,
    eulogy: 'He took the blow meant for Sable and smiled, the way he always did — as if death itself were just one more door to slip through.',
    kills: 188, floors: 42, missions: 41, loyalty: 88, legacy: 'The Silent Step',
  }
  return (
    <div className="ilm-death-scrim" onClick={onClose}>
      <div className="ilm-death" onClick={e => e.stopPropagation()}>
        {/* rising embers */}
        {[16, 38, 60, 80].map((l, i) => <span key={i} className="ilm-death-ember" style={{ left: `${l}%`, animationDelay: `${i * 1.3}s` }} />)}

        <div style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.5em', fontSize: '0.66rem', color: 'var(--gold-hi)', textAlign: 'center' }}>FLOOR {h.floor} · THE ASHEN COURT</div>

        <div className="ilm-death-portrait">
          {h.id ? <img src={h.portrait_path ? `/${h.portrait_path}` : `/heroes/${h.id}/card-image?mini=1`} alt={h.name} onError={e => { e.target.style.display = 'none' }} /> : <span className="ilm-death-silhouette">☙</span>}
          <div className="ilm-death-fade" />
        </div>

        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: '2.4rem', color: 'var(--text-hi)', textAlign: 'center', letterSpacing: '.04em', textShadow: '0 4px 40px rgba(192,64,64,.4)' }}>{h.name}</div>
        <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', textAlign: 'center', marginTop: 2 }}>“{h.title}” · {h.hero_class} · Level {h.level}</div>

        <div className="ilm-death-fellrow">
          <span style={{ height: 1, flex: 1, background: 'linear-gradient(90deg,transparent,rgba(192,64,64,.5))' }} />
          <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.3em', fontSize: '0.62rem', color: 'var(--red-hi)' }}>FELL ON THE {h.floor}TH FLOOR</span>
          <span style={{ height: 1, flex: 1, background: 'linear-gradient(90deg,rgba(192,64,64,.5),transparent)' }} />
        </div>

        <div style={{ fontStyle: 'italic', color: '#c8b8dd', textAlign: 'center', lineHeight: 1.7, fontSize: '1.05rem', margin: '0 auto', maxWidth: 520 }}>{h.eulogy}</div>

        <div className="ilm-death-tally">{h.kills} KILLS · {h.floors} FLOORS · {h.missions} MISSIONS · LOYALTY {h.loyalty}</div>

        <div className="ilm-death-legacy">
          <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
          <span className="ilm-micro" style={{ color: 'var(--gold-hi)' }}>A LEGACY IS FORGED</span>
          <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, color: 'var(--text-hi)', letterSpacing: '.06em' }}>“{h.legacy}”</span>
        </div>

        <button className="ilm-btn ilm-btn-gold ilm-btn-block" style={{ marginTop: 18, maxWidth: 320, marginLeft: 'auto', marginRight: 'auto' }} onClick={onClose}>LAY THEM TO REST</button>
      </div>
    </div>
  )
}
