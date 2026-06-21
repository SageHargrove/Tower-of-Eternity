import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

new_header = '''
      <header className="app-header" style={{ display: 'flex', justifyContent: 'space-between', width: '100%', padding: '1rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <h1 style={{ fontSize: '2.5rem', margin: 0 }}>⬡ Tower Gacha</h1>
          <div className="text-dim" style={{ borderLeft: '2px solid var(--border)', paddingLeft: '2rem', fontSize: '1.4rem' }}>
            Profile: <span className="text-gold" style={{ fontSize: '1.6rem' }}>{activeProfile}</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '3rem' }}>
          <button className="btn" style={{ padding: '0.8rem 1.5rem', fontSize: '1.2rem' }} onClick={() => setShowSettings(true)}>
            ⚙️ Settings
          </button>
          {gold !== null && (
            <div className="gold-display" style={{ display: 'flex', gap: '2rem', fontSize: '1.4rem' }}>
              <span style={{ color: 'var(--gold)', fontWeight: 'bold' }}>🪙 {gold.toLocaleString()} GOLD</span>
              {supplies !== null && <span style={{ color: 'var(--subtext)', fontWeight: 'bold' }}>📦 {supplies.toLocaleString()} SUPPLIES</span>}
            </div>
          )}
        </div>
      </header>
'''

c = re.sub(r'<header className="app-header">.*?</header>', new_header.strip(), c, flags=re.DOTALL)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
