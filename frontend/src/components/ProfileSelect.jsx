import React, { useState, useEffect } from 'react'
import { listProfiles, switchProfile, renameProfile, deleteProfile } from '../api/client'

export default function ProfileSelect({ onSelect }) {
  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [newProfile, setNewProfile] = useState('')
  const [selectedProfile, setSelectedProfile] = useState(null)
  const [msg, setMsg] = useState(null)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    try {
      const data = await listProfiles()
      setProfiles(data.profiles)
      // Clear selection if it no longer exists
      if (selectedProfile && !data.profiles.includes(selectedProfile)) {
        setSelectedProfile(null)
      }
    } catch (e) {
      setMsg(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleLoadSelected() {
    if (!selectedProfile) return
    try {
      setLoading(true)
      await switchProfile(selectedProfile)
      onSelect(selectedProfile)
    } catch (e) {
      setMsg(e.message)
      setLoading(false)
    }
  }

  async function handleCreate(e) {
    e.preventDefault()
    const name = newProfile.trim()
    if (!name) return
    try {
      setLoading(true)
      await switchProfile(name)
      onSelect(name)
    } catch (e) {
      setMsg(e.message)
      setLoading(false)
    }
  }

  async function handleRename() {
    if (!selectedProfile) return
    const newName = prompt(`Enter new name for profile "${selectedProfile}":`, selectedProfile)
    if (!newName || newName === selectedProfile) return
    
    try {
      setLoading(true)
      await renameProfile(selectedProfile, newName)
      setSelectedProfile(newName)
      await load()
      setMsg(`Profile renamed to ${newName}`)
    } catch(e) {
      setMsg(e.message)
      setLoading(false)
    }
  }

  async function handleDelete() {
    if (!selectedProfile) return
    const confirmed = window.confirm(`Are you sure you want to permanently delete the profile "${selectedProfile}"?`)
    if (!confirmed) return
    
    try {
      setLoading(true)
      await deleteProfile(selectedProfile)
      setSelectedProfile(null)
      await load()
      setMsg(`Profile deleted.`)
    } catch(e) {
      setMsg(e.message)
      setLoading(false)
    }
  }

  if (loading && profiles.length === 0) return <div className="page" style={{display: 'flex', justifyContent: 'center', alignItems: 'center'}}>Loading saves...</div>

  return (
    <div className="page" style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh',
      position: 'relative', overflow: 'hidden', background: '#000',
    }}>
      {/* Full-bleed tower art behind everything — the same logo image, just
          given room to actually read as "insanely huge" on the splash
          screen instead of being squeezed into a small header icon.
          "contain" (not "cover") so the whole spire — tip to base forest —
          stays visible instead of being cropped down to just the middle. */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'url(/tower_logo.png)',
        backgroundSize: 'cover', backgroundPosition: 'center 42%', backgroundRepeat: 'no-repeat',
      }} />
      <div style={{
        position: 'absolute', inset: 0,
        background: 'linear-gradient(to bottom, rgba(10,10,14,0.1) 0%, rgba(10,10,14,0.2) 50%, rgba(10,10,14,0.7) 78%, rgba(10,10,14,0.95) 100%)',
      }} />

      <div style={{ textAlign: 'center', marginBottom: '2rem', position: 'relative', zIndex: 1 }}>
        <h1 style={{ fontFamily: 'Cinzel, serif', fontSize: '2.6rem', color: 'var(--text)', margin: '0.5rem 0', textShadow: '0 2px 12px rgba(0,0,0,0.8)' }}>Tower of Eternity</h1>
        <div className="text-dim" style={{ fontSize: '0.9rem', letterSpacing: '2px' }}>SELECT SAVE PROFILE</div>
      </div>

      <div className="card" style={{ width: '450px', maxWidth: '90vw', padding: '2rem', position: 'relative', zIndex: 1 }}>
        {msg && <div className="text-red text-sm" style={{ marginBottom: '1rem', textAlign: 'center' }}>{msg}</div>}
        
        {/* Create Bar at the top */}
        <form onSubmit={handleCreate} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1.5rem' }}>
          <input 
            type="text" 
            placeholder="New Profile Name..." 
            value={newProfile}
            onChange={e => setNewProfile(e.target.value)}
            style={{ flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', padding: '0.5rem 1rem', color: '#fff', borderRadius: 4 }}
          />
          <button type="submit" className="btn btn-gold" disabled={!newProfile.trim()}>
            Create
          </button>
        </form>

        {/* Save List */}
        <div className="text-dim text-sm" style={{ marginBottom: '0.5rem', fontFamily: 'Cinzel, serif' }}>Existing Profiles</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.5rem', maxHeight: '30vh', overflowY: 'auto', paddingRight: '0.5rem' }}>
          {profiles.length === 0 && <div className="text-dim text-sm" style={{ fontStyle: 'italic' }}>No profiles found. Create one above!</div>}
          {profiles.map(p => {
            const isSelected = selectedProfile === p;
            return (
              <button 
                key={p} 
                className="btn" 
                onClick={() => setSelectedProfile(p)}
                style={{ 
                  padding: '1rem', 
                  fontSize: '1.1rem', 
                  background: isSelected ? 'rgba(201,168,76,0.2)' : 'rgba(255,255,255,0.05)', 
                  border: isSelected ? '1px solid var(--gold)' : '1px solid rgba(255,255,255,0.1)', 
                  textAlign: 'left', 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  transition: 'all 0.2s'
                }}
              >
                <span style={{ fontFamily: 'Cinzel, serif', fontWeight: 'bold', color: isSelected ? 'var(--gold)' : 'inherit' }}>{p}</span>
                {isSelected && <span style={{ fontSize: '0.8rem', color: 'var(--gold)' }}>Selected ✓</span>}
              </button>
            );
          })}
        </div>

        {/* Action Buttons for Selected Profile */}
        <div style={{ display: 'flex', gap: '0.5rem', opacity: selectedProfile ? 1 : 0.3, pointerEvents: selectedProfile ? 'auto' : 'none', transition: 'opacity 0.2s' }}>
          <button className="btn btn-gold" style={{ flex: 2, padding: '0.75rem', fontWeight: 'bold' }} onClick={handleLoadSelected}>
            Load Profile
          </button>
          <button className="btn" style={{ flex: 1, padding: '0.75rem' }} onClick={handleRename}>
            Rename
          </button>
          <button className="btn text-red" style={{ flex: 1, padding: '0.75rem', background: 'rgba(150,0,0,0.15)', border: '1px solid rgba(255,0,0,0.3)' }} onClick={handleDelete}>
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
