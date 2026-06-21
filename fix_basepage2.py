import re

with open('frontend/src/pages/BasePage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Logic to add inside render body
gen_logic = """
  let goldGen = 0;
  let suppliesGen = 0;
  if (facilitiesData && facilitiesData.built) {
    facilitiesData.built.forEach(f => {
      let base_amt = 50 * f.level;
      let multiplier = 1.0 + ((f.assigned?.length || 0) * 0.10);
      if (f.type === 'The Market') goldGen += Math.floor(base_amt * multiplier);
      if (f.type === 'The Farm') suppliesGen += Math.floor(base_amt * multiplier);
    });
  }

  const renderTabs = () => ("""

content = content.replace("const renderTabs = () => (", gen_logic)

# Replace the lobby block
old_lobby_regex = r"\{activeTab === 'lobby' && \((.*?)\)\}\s*\{activeTab === 'facilities'"

new_lobby = """{activeTab === 'lobby' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Top Row: Base Stats & Recovery */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
            
            {/* The Lobby Profile */}
            <div className="card" style={{ padding: '2rem' }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.8rem', color: 'var(--gold)', marginBottom: '0.5rem' }}>{base.name}</div>
              <div className="text-dim" style={{ fontSize: '1.1rem', marginBottom: '1.5rem' }}>
                Lobby Level {base.level} | Max Roster Size: {base.max_roster_size || 10}
              </div>
              
              <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem' }}>
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
                Assign heroes to the Infirmary to passively increase healing rates over time.
              </div>
              <button className="btn btn-gold" onClick={handleRest} disabled={resting} style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', marginTop: '2rem' }}>
                {resting ? 'Resting...' : 'Rest All Heroes'}
              </button>
              {msg && <div className="text-green" style={{ marginTop: '1rem', fontSize: '1.1rem', textAlign: 'center' }}>{msg}</div>}
            </div>

          </div>

          {/* Bottom Row: Hero Chatter Box */}
          <div className="card" style={{ padding: '1.5rem', minHeight: '250px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.4rem', color: 'var(--gold)', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
              Hero Chatter
            </div>
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              {chats && chats.length > 0 ? chats.map(chat => (
                <div key={chat.id} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                  <span className="text-dim" style={{ fontSize: '0.9rem', whiteSpace: 'nowrap' }}>[{new Date(chat.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}]</span>
                  <span style={{ color: 'var(--gold)', fontSize: '0.9rem', whiteSpace: 'nowrap' }}>[{chat.location}]</span>
                  <span style={{ fontSize: '1.05rem' }}>{chat.message}</span>
                </div>
              )) : (
                <div className="text-dim" style={{ fontStyle: 'italic', textAlign: 'center', marginTop: '2rem' }}>The lobby is quiet...</div>
              )}
            </div>
          </div>

        </div>
      )}

      {activeTab === 'facilities'"""

content = re.sub(old_lobby_regex, new_lobby, content, flags=re.DOTALL)

with open('frontend/src/pages/BasePage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
