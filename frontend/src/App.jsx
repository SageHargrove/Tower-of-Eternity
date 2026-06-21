import React, { useState, useEffect } from 'react'
import SummonPage from './pages/SummonPage'
import HeroesPage from './pages/HeroesPage'
import TowerPage from './pages/TowerPage'
import BasePage from './pages/BasePage'
import LogPage from './pages/LogPage'
import InventoryPage from './pages/InventoryPage'
import ProfileSelect from './components/ProfileSelect'
import HeroChat from './components/HeroChat'
import { getBase, listProfiles } from './api/client'
import { initAudio, setSoundEnabled, isSoundEnabled, playClick, setBgmVolume, setSfxVolume } from './audio'

const TABS = [
  { id: 'summon', label: 'Summon' },
  { id: 'heroes', label: 'Heroes' },
  { id: 'inventory', label: 'Items' },
  { id: 'tower',  label: 'Tower' },
  { id: 'base',   label: 'Base' },
]

export default function App() {
  const [activeProfile, setActiveProfile] = useState(null)
  const [tab, setTab] = useState('summon')
  const [gold, setGold] = useState(null)
  const [supplies, setSupplies] = useState(null)
  const [gems, setGems] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const [soundOn, setSoundOn] = useState(true)
  const [bgmVol, setBgmVol] = useState(50)
  const [sfxVol, setSfxVol] = useState(50)

  useEffect(() => { 
    checkProfile()
    
    // Global click listener for buttons to play sound
    const handleGlobalClick = (e) => {
      if (e.target.closest('button')) {
        playClick()
      }
    }
    document.addEventListener('click', handleGlobalClick)
    return () => document.removeEventListener('click', handleGlobalClick)
  }, [])

  async function checkProfile() {
    try {
      const data = await listProfiles()
    } catch {}
  }

  async function refreshResources() {
    if (!activeProfile) return
    try {
      const data = await getBase()
      setGold(data.gold)
      setSupplies(data.supplies)
      setGems(data.gems || 0)
    } catch {}
  }

  useEffect(() => {
    if (activeProfile) refreshResources()
  }, [activeProfile])

  function toggleSound() {
    initAudio()
    const next = !soundOn
    setSoundOn(next)
    setSoundEnabled(next)
  }

  if (!activeProfile) {
    return <ProfileSelect onSelect={(p) => {
      initAudio()
      setActiveProfile(p)
    }} />
  }

  const pages = {
    summon: <SummonPage onGoldChange={refreshResources} />,
    heroes: <HeroesPage />,
    inventory: <InventoryPage />,
    tower:  <TowerPage />,
    base:   <BasePage onGoldChange={refreshResources} />,
    log:    <LogPage />,
  }

  return (
    <div className="app">
      <header className="app-header" style={{ display: 'flex', justifyContent: 'space-between', width: '100%', padding: '1rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <h1 style={{ fontSize: '2.5rem', margin: 0 }}>⬡ Tower Gacha</h1>
          <div className="text-dim" style={{ borderLeft: '2px solid var(--border)', paddingLeft: '2rem', fontSize: '1.6rem' }}>
            Profile: <span className="text-gold" style={{ fontSize: '2.2rem', fontWeight: 'bold' }}>{activeProfile}</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '3rem' }}>
          <button className="btn" style={{ padding: '0.8rem 1.5rem', fontSize: '1.2rem' }} onClick={() => setShowSettings(true)}>
            ⚙️ Settings
          </button>
          {gold !== null && (
            <div className="gold-display" style={{ display: 'flex', gap: '2rem', fontSize: '1.4rem' }}>
              <span style={{ color: 'var(--gold)', fontWeight: 'bold' }}>🪙 {gold.toLocaleString()} GOLD</span>
              {gems !== null && <span style={{ color: '#00ffff', fontWeight: 'bold', textShadow: '0 0 5px rgba(0,255,255,0.5)' }}>💎 {gems.toLocaleString()} GEMS</span>}
              {supplies !== null && <span style={{ color: 'var(--subtext)', fontWeight: 'bold' }}>📦 {supplies.toLocaleString()} SUPPLIES</span>}
            </div>
          )}
        </div>
      </header>

      <nav className="tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${tab === t.id ? 'active' : ''}`}
            onClick={() => { setTab(t.id); if (t.id === 'base' || t.id === 'summon') refreshResources() }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="main-content">
        {pages[tab]}
      </main>
      
      

      {showSettings && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.85)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(5px)'
        }} onClick={() => setShowSettings(false)}>
          <div className="card" style={{ width: '300px', textAlign: 'center' }} onClick={e => e.stopPropagation()}>
            <h2 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', marginBottom: '1.5rem' }}>Settings</h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <button className="btn" onClick={toggleSound}>
                {soundOn ? '🔊 Sound Master: ON' : '🔇 Sound Master: OFF'}
              </button>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-start' }}>
                <label className="text-dim text-sm">Music Volume</label>
                <input type="range" min="0" max="100" value={bgmVol} onChange={(e) => {
                  const val = parseInt(e.target.value)
                  setBgmVol(val)
                  setBgmVolume(val / 100)
                }} style={{ width: '100%' }} />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-start' }}>
                <label className="text-dim text-sm">SFX Volume</label>
                <input type="range" min="0" max="100" value={sfxVol} onChange={(e) => {
                  const val = parseInt(e.target.value)
                  setSfxVol(val)
                  setSfxVolume(val / 100)
                }} style={{ width: '100%' }} />
              </div>
              
              <button className="btn" onClick={() => {
                setShowSettings(false)
                setActiveProfile(null)
              }}>
                🔄 Switch Profile (Main Menu)
              </button>
              
              <button className="btn" style={{ marginTop: '1rem', background: 'var(--border)' }} onClick={() => setShowSettings(false)}>
                Close
              </button>
            </div>
            
            <div className="text-dim" style={{ fontSize: '0.65rem', marginTop: '1.5rem' }}>
              Tower Gacha Pre-Alpha
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
