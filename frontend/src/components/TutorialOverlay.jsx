import React, { useState } from 'react'
import { setMasterName, completeTutorial } from '../api/client'

// This is the fairy's main stage — a few small contextual popups exist
// elsewhere (see FairyGuide.jsx), but this full onboarding walkthrough is
// the one place she's guaranteed to actually appear for every new profile.
export default function TutorialOverlay({ fairyGender, onComplete }) {
  const [step, setStep] = useState(0)
  const [nameInput, setNameInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const fairyImg = `/static/portraits/fairy/${fairyGender === 'male' ? 'male' : 'female'}.png`

  const steps = [
    {
      title: 'A Fairy Appears',
      body: "Oh! You're here. I've been waiting for someone to wander into the Hollow Spire. I'm your guide — I'll help you make sense of all this, step by step.",
    },
    {
      title: 'Who Are You?',
      body: "Before we go any further — what should the heroes call you? You're the one summoning them, training them, and sending them up the tower, after all. They'll want a name for their Master.",
      isNameStep: true,
    },
    {
      title: 'Summoning Heroes',
      body: "The Tower can't be climbed alone. Head to the Summoning Gate to call heroes into this world — gold and gems both work, though gems pull from a much wider, much stronger pool. Every hero is unique: their own face, their own past, their own stats.",
    },
    {
      title: 'The Tower Itself',
      body: "Once you've got a team, the Tower is where you'll spend most of your time. Each floor is its own fight — sometimes worse than a fight. Clear floors to push higher, earn rewards, and grow stronger. Losing a fight isn't always the end, but it's never free.",
    },
    {
      title: 'One Last Thing',
      body: "That's the basics — you'll pick up the rest as you go, and I'll pop in again whenever something new shows up. Here's something to get you started.",
      isFinalStep: true,
    },
  ]

  const current = steps[step]
  const isLast = step === steps.length - 1

  async function handleNext() {
    if (current.isNameStep) {
      const trimmed = nameInput.trim()
      if (!trimmed) {
        setError('Tell me what to call you first.')
        return
      }
      setBusy(true)
      setError(null)
      try {
        await setMasterName(trimmed)
        setStep(s => s + 1)
      } catch (e) {
        setError(e.message)
      } finally {
        setBusy(false)
      }
      return
    }
    if (isLast) {
      await handleFinish()
      return
    }
    setStep(s => s + 1)
  }

  async function handleFinish() {
    setBusy(true)
    try {
      const res = await completeTutorial()
      onComplete(res.gems_granted || 0)
    } catch (e) {
      setError(e.message)
      onComplete(0)
    } finally {
      setBusy(false)
    }
  }

  async function handleSkip() {
    setBusy(true)
    try {
      const res = await completeTutorial()
      onComplete(res.gems_granted || 0)
    } catch (e) {
      onComplete(0)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(5, 5, 8, 0.92)', zIndex: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        width: '560px', maxWidth: '90vw',
        background: 'rgba(15, 20, 25, 0.97)',
        border: '2px solid #a88be0',
        borderRadius: '10px',
        padding: '2rem',
        boxShadow: '0 12px 48px rgba(168, 139, 224, 0.25)',
      }}>
        <div style={{ display: 'flex', gap: '1.2rem', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div style={{
            width: '84px', height: '84px', borderRadius: '50%', overflow: 'hidden',
            border: '2px solid #a88be0', background: '#222', flexShrink: 0,
          }}>
            <img src={fairyImg} style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }} />
            <div style={{ width: '100%', height: '100%', display: 'none', alignItems: 'center', justifyContent: 'center', fontSize: '2.5rem' }}>
              🧚
            </div>
          </div>
          <div>
            <div style={{ fontFamily: 'Cinzel, serif', color: '#a88be0', fontWeight: 'bold', fontSize: '1.3rem', marginBottom: '0.4rem' }}>
              {current.title}
            </div>
            <div style={{ fontSize: '1rem', lineHeight: 1.6, color: '#e0e0e0' }}>
              {current.body}
            </div>
          </div>
        </div>

        {current.isNameStep && (
          <input
            autoFocus
            type="text"
            value={nameInput}
            onChange={e => setNameInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleNext() }}
            placeholder="Your name..."
            maxLength={24}
            style={{
              width: '100%', padding: '0.7rem 0.9rem', fontSize: '1rem',
              background: 'var(--bg)', color: '#fff', border: '1px solid #a88be0',
              borderRadius: 6, marginBottom: '1rem', fontFamily: 'inherit',
            }}
          />
        )}

        {error && <div className="text-red" style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>{error}</div>}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button className="btn" onClick={handleSkip} disabled={busy} style={{ fontSize: '0.85rem', opacity: 0.7 }}>
            Skip Tutorial
          </button>
          <div style={{ display: 'flex', gap: '0.4rem' }}>
            {steps.map((_, i) => (
              <div key={i} style={{
                width: 7, height: 7, borderRadius: '50%',
                background: i === step ? '#a88be0' : 'rgba(168,139,224,0.25)',
              }} />
            ))}
          </div>
          <button className="btn btn-primary" onClick={handleNext} disabled={busy} style={{ padding: '0.6rem 1.4rem' }}>
            {busy ? '...' : isLast ? 'Finish' : 'Continue'}
          </button>
        </div>
      </div>
    </div>
  )
}
