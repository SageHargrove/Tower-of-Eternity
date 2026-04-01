import React, { useState, useEffect } from 'react'
import SummonPage from './pages/SummonPage'
import HeroesPage from './pages/HeroesPage'
import TowerPage from './pages/TowerPage'
import BasePage from './pages/BasePage'
import LogPage from './pages/LogPage'
import { getBase } from './api/client'

const TABS = [
  { id: 'summon', label: 'Summon' },
  { id: 'heroes', label: 'Heroes' },
  { id: 'tower',  label: 'Tower' },
  { id: 'base',   label: 'Base' },
  { id: 'log',    label: 'Log' },
]

export default function App() {
  const [tab, setTab] = useState('summon')
  const [gold, setGold] = useState(null)

  useEffect(() => { refreshGold() }, [])

  async function refreshGold() {
    try {
      const base = await getBase()
      setGold(base.gold)
    } catch {}
  }

  const pages = {
    summon: <SummonPage onGoldChange={refreshGold} />,
    heroes: <HeroesPage />,
    tower:  <TowerPage />,
    base:   <BasePage onGoldChange={refreshGold} />,
    log:    <LogPage />,
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>⬡ Tower Gacha</h1>
        {gold !== null && (
          <div className="gold-display">◈ {gold.toLocaleString()} gold</div>
        )}
      </header>

      <nav className="tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${tab === t.id ? 'active' : ''}`}
            onClick={() => { setTab(t.id); if (t.id === 'base' || t.id === 'summon') refreshGold() }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main style={{ flex: 1 }}>
        {pages[tab]}
      </main>
    </div>
  )
}
