import React from 'react'

// Fires once per browser (mirrors the seen_noncombat_tip localStorage
// pattern in SummonPage.jsx, not a per-profile flag) after the main
// TutorialOverlay intro finishes — walks the player through every tab
// (and Base's sub-tabs) by locking navigation to only the current
// target until they actually click into it, then revealing what's there.
export default function TabTourOverlay({ step, stepIndex, totalSteps, entered, fairyGender, onNext, onSkip }) {
  if (!step) return null

  const fairyImg = `/static/portraits/fairy/${fairyGender === 'male' ? 'male' : 'female'}.png`

  return (
    <div style={{
      position: 'fixed', bottom: '30px', left: '30px',
      zIndex: 2000, width: '360px', maxWidth: '90vw',
      background: 'rgba(15, 20, 25, 0.97)', border: '2px solid #a88be0', borderRadius: 10,
      padding: '1.2rem', boxShadow: '0 12px 40px rgba(168,139,224,0.3)',
    }}>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
        <div style={{ width: 56, height: 56, borderRadius: '50%', overflow: 'hidden', border: '1px solid #a88be0', background: '#222', flexShrink: 0 }}>
          <img src={fairyImg} style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }} />
          <div style={{ width: '100%', height: '100%', display: 'none', alignItems: 'center', justifyContent: 'center', fontSize: '1.8rem' }}>✦</div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: 'Cinzel, serif', color: '#a88be0', fontWeight: 'bold', fontSize: '1.05rem', marginBottom: '0.3rem' }}>
            {step.title} <span style={{ color: '#888', fontSize: '0.75rem', fontWeight: 'normal' }}>({stepIndex + 1}/{totalSteps})</span>
          </div>
          <div style={{ fontSize: '0.88rem', lineHeight: 1.5, color: '#e0e0e0', marginBottom: '0.8rem' }}>
            {entered ? step.body : `Click the "${step.label}" tab to continue.`}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button onClick={onSkip} style={{ background: 'none', border: 'none', color: '#888', fontSize: '0.78rem', cursor: 'pointer', opacity: 0.7 }}>
              Skip Tour
            </button>
            {entered && (
              <button className="btn btn-primary" onClick={onNext} style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}>
                {stepIndex + 1 === totalSteps ? 'Finish' : 'Next →'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
