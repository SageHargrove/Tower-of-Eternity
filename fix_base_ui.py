import re

with open('frontend/src/pages/BasePage.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Fix getGenRate
get_gen_repl = '''
  const getGenRate = (fac) => {
    if (fac.type !== 'The Market' && fac.type !== 'The Farm') return null;
    let base_amt = fac.type === 'The Market' ? 100 * fac.level : 5 * fac.level;
    let multiplier = 1.0 + ((fac.heroes || []).length * 0.10);
    let amt = Math.floor(base_amt * multiplier);
    let resName = fac.type === 'The Market' ? 'Gold' : 'Supplies';
    return `Generating: +${amt} ${resName} / 5 mins`;
  };
'''
c = re.sub(r'  const getGenRate = \(fac\) => \{.*?\};', get_gen_repl.strip(), c, flags=re.DOTALL)

# 2. Add handleRename
rename_logic = '''
  const handleRenameBase = async () => {
    const newName = prompt("Enter a new name for your base:", base.name);
    if (!newName) return;
    try {
      const res = await fetch('/api/base/rename', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName })
      });
      if (!res.ok) {
        alert("Failed to rename base.");
        return;
      }
      loadAll();
    } catch(e) { console.error(e); }
  };

  const handleRest = async () => {
'''
c = c.replace('  const handleRest = async () => {', rename_logic.strip())

# 3. Replace The Lobby Profile UI and Rest & Recovery UI
lobby_ui_repl = '''
            {/* The Lobby Profile */}
            <div className="card" style={{ padding: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '2.0rem', color: 'var(--gold)' }}>
                    {base.name} <span style={{ fontSize: '1.4rem', color: 'var(--text-dim)' }}>(Lv.{base.level})</span>
                  </div>
                  <button className="btn" style={{ padding: '0.4rem', fontSize: '0.9rem' }} onClick={handleRenameBase} title="Rename Base">✎ Edit</button>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button className="btn" style={{ fontSize: '1.1rem', background: 'var(--bg-lighter)' }} title="Max Roster Size">
                    👥 Max Roster: <span className="text-hi">{base.max_roster_size || 10}</span>
                  </button>
                  <button className="btn btn-gold" style={{ fontSize: '1.1rem' }} onClick={handleUpgradeBase}>
                    Upgrade Base ({5000 * base.level}G)
                  </button>
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem', marginTop: '1rem' }}>
                <div>
                  <div className="text-dim" style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Total Treasury</div>
                  <div className="text-gold" style={{ fontFamily: 'Cinzel, serif', fontSize: '1.5rem' }}>{base.gold.toLocaleString()} Gold</div>
                </div>
                <div>
                  <div className="text-dim" style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Total Supplies</div>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.5rem', color: '#c7e0f4' }}>{base.supplies?.toLocaleString()} Supplies</div>
                </div>
              </div>
              
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.5rem' }}>
                <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', color: 'var(--text-hi)', marginBottom: '1rem' }}>Resource Generation</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '1.1rem' }}>
                  <span className="text-dim">The Market:</span>
                  <span className="text-gold">+{goldGen} Gold / 5 mins</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem' }}>
                  <span className="text-dim">The Farm:</span>
                  <span style={{ color: '#c7e0f4' }}>+{suppliesGen} Supplies / 5 mins</span>
                </div>
              </div>
            </div>

            {/* Rest & Recovery */}
            <div className="card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', color: 'var(--text-hi)', marginBottom: '1rem' }}>Rest & Recovery</div>
              <div className="text-dim" style={{ fontSize: '1.1rem', lineHeight: 1.6, marginBottom: 'auto' }}>
                Resting at base recovers morale (+25), reduces stress (-20), and slowly heals trauma (-5) for all living heroes.<br/><br/>
                Resting costs 50 supplies and has a 5-minute cooldown.
              </div>
              {(() => {
                const now = Date.now() / 1000;
                const lastRest = base.last_rest_time || 0;
                const cd = 300;
                const rem = Math.max(0, cd - (now - lastRest));
                const isCooldown = rem > 0;
                return (
                  <button className="btn btn-gold" onClick={handleRest} disabled={resting || isCooldown} style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', marginTop: '2rem' }}>
                    {resting ? 'Resting...' : isCooldown ? `Cooldown (${Math.ceil(rem)}s)` : 'Rest All Heroes (Costs 50 Supplies)'}
                  </button>
                )
              })()}
              {msg && <div className="text-green" style={{ marginTop: '1rem', fontSize: '1.1rem', textAlign: 'center' }}>{msg}</div>}
            </div>
'''
c = re.sub(r'\{\/\* The Lobby Profile \*\/\}.*?\{\/\* Bottom Row: Hero Chatter Box \*\/\}', lobby_ui_repl.strip() + '\n\n            {/* Bottom Row: Hero Chatter Box */}', c, flags=re.DOTALL)

with open('frontend/src/pages/BasePage.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
