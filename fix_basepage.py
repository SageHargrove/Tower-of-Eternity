import re

with open('frontend/src/pages/BasePage.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update Tooltips
tooltips_repl = '''
const FACILITY_TOOLTIPS = {
  "Forge": "Crafts powerful weapons and armor. Assign Blacksmiths to increase crafting speed and quality.",
  "Infirmary": "Heals trauma and severe injuries passively over time. Assign Medics and Priests for better results.",
  "Vault": "Increases max gold capacity and provides interest. Quartermasters manage the Vault effectively.",
  "Restaurant": "Cooks advanced meals to increase morale. Assign Chefs to maximize food quality.",
  "Alchemist Lab": "Brews potions and elixirs. Alchemists and Mages excel in this facility.",
  "Workshop": "Builds base upgrades and gadgets. Magic Engineers are the best fit.",
  "The Market": "Generates passive gold over time. Merchants, Alchemists, and Quartermasters excel here.",
  "The Farm": "Generates passive supplies over time. Merchants, Chefs, and Druids excel here.",
  "Training Grounds": "Allows heroes to spar for EXP. Warriors, Spearmen, and Tacticians thrive here.",
  "Mage Tower": "Conducts magical research. Mages and Spellswords are required."
}
'''
c = re.sub(r'const FACILITY_TOOLTIPS = \{.*?\n\}', tooltips_repl.strip(), c, flags=re.DOTALL)

# 2. Add Base Upgrade Logic
upgrade_logic = '''
  const handleRest = async () => {
    setResting(true)
    try {
      const res = await fetch('/api/base/rest', { method: 'POST' })
      const data = await res.json()
      if (!res.ok) {
        addToast(data.detail || "Cannot rest.", "error")
        return
      }
      addToast(`Rested ${data.rested} heroes. Cost: ${data.cost} supplies.`, "success")
      getBase()
    } catch (e) {
      console.error(e)
    } finally {
      setResting(false)
    }
  }

  const handleUpgradeBase = async () => {
    try {
      const res = await fetch('/api/base/upgrade', { method: 'POST' })
      if (!res.ok) {
         const data = await res.json()
         addToast(data.detail || "Failed to upgrade", 'error')
         return
      }
      addToast("Base Upgraded! Max Roster Size increased.", 'success')
      getBase()
      if (onGoldChange) onGoldChange()
    } catch(e) { console.error(e) }
  }
'''
c = re.sub(r'const handleRest = async \(\) => \{.*?\n  \}', upgrade_logic.strip(), c, flags=re.DOTALL)


# 3. Update getGenRate
getgen_repl = '''
  function getGenRate(f) {
    if (f.type === 'The Market') return `Generating: ${100 * f.level} Gold / 5 mins`
    if (f.type === 'The Farm') return `Generating: ${5 * f.level} Supplies / 5 mins`
    return null
  }
'''
c = re.sub(r'function getGenRate\(f\) \{.*?\n  \}', getgen_repl.strip(), c, flags=re.DOTALL)

# 4. Lobby UI update for base upgrade and rest cooldown
lobby_repl = '''
              <div className="card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', color: 'var(--text-hi)' }}>The Lobby (Lv.{baseData?.level || 1})</div>
                  <button className="btn btn-gold" onClick={handleUpgradeBase}>
                    Upgrade ({baseData?.level ? 5000 * baseData.level : 5000}G)
                  </button>
                </div>
                <div className="text-dim" style={{ fontSize: '1.1rem', lineHeight: 1.6, marginBottom: 'auto' }}>
                  The central hub of your operations. Upgrading the base increases your maximum hero roster capacity.
                </div>
                <div style={{ marginTop: '2rem', fontSize: '1.2rem' }}>
                  Max Heroes: <span className="text-hi">{baseData?.max_roster_size || 50}</span>
                </div>
              </div>

            {/* Rest & Recovery */}
              <div className="card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
                <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', color: 'var(--text-hi)', marginBottom: '1rem' }}>Rest & Recovery</div>
                <div className="text-dim" style={{ fontSize: '1.1rem', lineHeight: 1.6, marginBottom: 'auto' }}>
                  Resting at base recovers morale (+25), reduces stress (-20), and slowly heals trauma (-5) for all living heroes.<br/><br/>
                  Resting has a 5-minute cooldown.
                </div>
                {(() => {
                  const now = Date.now() / 1000;
                  const lastRest = baseData?.last_rest_time || 0;
                  const cd = 300;
                  const rem = Math.max(0, cd - (now - lastRest));
                  const isCooldown = rem > 0;
                  return (
                    <button className="btn btn-gold" onClick={handleRest} disabled={resting || isCooldown} style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', marginTop: '2rem' }}>
                      {resting ? 'Resting...' : isCooldown ? `Cooldown (${Math.ceil(rem)}s)` : 'Rest All Heroes (Costs 50 Supplies)'}
                    </button>
                  )
                })()}
              </div>
'''

c = re.sub(r'<div className="card" style=\{\{ padding: \'2rem\', display: \'flex\', flexDirection: \'column\' \}\}>\s*<div style=\{\{ fontFamily: \'Cinzel, serif\', fontSize: \'1\.8rem\', color: \'var\(--text-hi\)\', marginBottom: \'1rem\' \}\}>The Lobby \(Lv\.1\)</div>.*?</div>\s*</div>', lobby_repl.strip() + '\n            </div>', c, flags=re.DOTALL)

with open('frontend/src/pages/BasePage.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

