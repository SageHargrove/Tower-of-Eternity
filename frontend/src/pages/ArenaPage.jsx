import React, { useState, useEffect } from 'react'
import GameIcon from '../components/GameIcon'
import { getAllTeams, getArenaSnapshot } from '../api/client'
import {
  getArenaServerUrl, setArenaServerUrl, getArenaToken, getArenaUsername, clearArenaSession,
  arenaRegister, arenaLogin, arenaSubmitTeam, arenaChallenge, arenaMatchmake, arenaLeaderboard,
  arenaMyRewards, arenaClaimReward, arenaMarketList, arenaMarketGet, arenaMarketHire
} from '../api/arenaServerClient'
import { receiveMail, applyTraining, listHeroes } from '../api/client'

export default function ArenaPage() {
  const [serverUrl, setServerUrl] = useState(getArenaServerUrl())
  const [token, setToken] = useState(getArenaToken())
  const [username, setUsername] = useState(getArenaUsername())

  const [authUsername, setAuthUsername] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authMode, setAuthMode] = useState('login') // 'login' | 'register'
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)

  const [teams, setTeams] = useState({})
  const [teamId, setTeamId] = useState(1)
  const [teamSubmitted, setTeamSubmitted] = useState(false)

  const [opponent, setOpponent] = useState('')
  const [fightResult, setFightResult] = useState(null)

  const [leaderboard, setLeaderboard] = useState([])
  const [pveLeaderboard, setPveLeaderboard] = useState([])
  const [activeTab, setActiveTab] = useState('pvp')

  // Training Market
  const [marketListings, setMarketListings] = useState([])
  const [allHeroes, setAllHeroes] = useState([])
  const [marketStudentId, setMarketStudentId] = useState('')
  const [marketTeacherId, setMarketTeacherId] = useState('')
  const [marketGemCost, setMarketGemCost] = useState(100)

  useEffect(() => {
    getAllTeams().then(setTeams).catch(() => {})
    listHeroes(true).then(setAllHeroes).catch(() => {})
  }, [])

  useEffect(() => {
    if (serverUrl) refreshLeaderboard()
  }, [serverUrl])

  // null = still trying, true = reachable, false = unreachable. The page
  // renders its full layout regardless — sections just get a "Connecting…"
  // veil while this isn't true.
  const [serverOnline, setServerOnline] = useState(null)

  function refreshLeaderboard() {
    arenaLeaderboard().then(data => {
      setLeaderboard(data.leaderboard)
      setPveLeaderboard(data.pve_leaderboard || [])
      setServerOnline(true)
    }).catch(() => setServerOnline(false))
    arenaMarketGet().then(data => {
      setMarketListings(data.listings || [])
    }).catch(() => {})
  }

  // Check for season rewards
  useEffect(() => {
    if (token) {
      arenaMyRewards().then(async data => {
        if (data.rewards && data.rewards.length > 0) {
          let claimedCount = 0;
          for (const rew of data.rewards) {
            try {
              // Claim it on the remote server
              await arenaClaimReward(rew.id);
              // Send it to the local mail inbox
              await receiveMail(
                "Arena Master", 
                "Arena Season Rewards", 
                `Congratulations on your performance this season!\nHere are your rewards.`, 
                { [rew.reward_type]: rew.amount }
              );
              claimedCount++;
            } catch (e) {
              console.error("Failed to claim reward", e);
            }
          }
          if (claimedCount > 0) {
            setMsg(`Received ${claimedCount} season reward(s) in your local Mailbox!`);
          }
        }
      }).catch(() => {});
    }
  }, [token])

  function handleSaveUrl() {
    setArenaServerUrl(serverUrl)
    setMsg('Arena server address saved.')
    refreshLeaderboard()
  }

  async function handleAuth(e) {
    e.preventDefault()
    if (!serverUrl) { setMsg('Set the Arena server address first.'); return }
    setBusy(true)
    setMsg(null)
    try {
      if (authMode === 'register') {
        await arenaRegister(authUsername.trim(), authPassword)
        setMsg('Registered. Now log in.')
        setAuthMode('login')
      } else {
        await arenaLogin(authUsername.trim(), authPassword)
        setToken(getArenaToken())
        setUsername(getArenaUsername())
        setMsg(`Logged in as ${getArenaUsername()}.`)
        refreshLeaderboard()
      }
    } catch (err) {
      setMsg(err.message)
    } finally {
      setBusy(false)
    }
  }

  function handleLogout() {
    clearArenaSession()
    setToken('')
    setUsername('')
  }

  async function handleSubmitTeam() {
    setBusy(true)
    setMsg(null)
    setTeamSubmitted(false)
    try {
      const snapshot = await getArenaSnapshot(teamId)
      await arenaSubmitTeam(snapshot.team)
      setTeamSubmitted(true)
      setMsg(`Submitted Team ${teamId} (${snapshot.team.length} heroes) to the Arena.`)
    } catch (err) {
      setMsg(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleChallenge(e) {
    e.preventDefault()
    setBusy(true)
    setMsg(null)
    setFightResult(null)
    try {
      const result = await arenaChallenge(opponent.trim())
      setFightResult(result)
      refreshLeaderboard()
    } catch (err) {
      setMsg(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleMatchmake() {
    setBusy(true)
    setMsg(null)
    setFightResult(null)
    try {
      const result = await arenaMatchmake()
      setFightResult(result)
      setMsg(`Matched against ${result.opponent}!`)
      refreshLeaderboard()
    } catch (err) {
      setMsg(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleListTeacher() {
    if (!marketTeacherId) return;
    setBusy(true)
    setMsg(null)
    try {
      const h = allHeroes.find(x => x.id === Number(marketTeacherId))
      if (!h) throw new Error("Hero not found.")
      
      const stats = { max_health: h.max_health, attack: h.attack, defense: h.defense, speed: h.speed }
      const skills = h.skills ? JSON.parse(h.skills) : []
      
      await arenaMarketList(h.name, h.hero_class, stats, skills, Number(marketGemCost))
      setMsg(`Listed ${h.name} on the Training Market!`)
      refreshLeaderboard()
    } catch (err) {
      setMsg(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleHireTeacher(listingId) {
    if (!marketStudentId) {
      setMsg("Please select a student hero to train.");
      return;
    }
    setBusy(true)
    setMsg(null)
    try {
      // Step 1: Hire on server (verifies cost & pays lister)
      const res = await arenaMarketHire(listingId);
      
      // Step 2: Apply locally
      const applyRes = await applyTraining(Number(marketStudentId), res.teacher.gem_cost, res.teacher.hero_stats, res.teacher.hero_skills);
      
      const st = allHeroes.find(x => x.id === Number(marketStudentId));
      let report = `${st.name} trained under ${res.teacher.hero_name} and gained ${applyRes.xp} XP! `;
      for (const [k, v] of Object.entries(applyRes.stats)) {
        if (v > 0) report += `+${v} ${k}. `;
      }
      if (applyRes.skills && applyRes.skills.length > 0) {
        report += `Skills: ${applyRes.skills.join(', ')}.`;
      }
      setMsg(report);
      refreshLeaderboard()
    } catch (err) {
      setMsg(err.message)
    } finally {
      setBusy(false)
    }
  }

  const teamEntries = Object.entries(teams).filter(([, heroes]) => heroes.length > 0)

  // Veils a section with a "Connecting…" overlay while the server isn't
  // reachable — the layout stays fully visible either way.
  const SectionVeil = ({ children }) => (
    <div style={{ position: 'relative' }}>
      {children}
      {serverOnline !== true && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 5, borderRadius: 6,
          background: 'rgba(5,5,8,0.72)', backdropFilter: 'blur(1.5px)',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.4rem',
        }}>
          <div style={{ fontFamily: 'Cinzel, serif', letterSpacing: '0.2em', color: 'var(--text-dim)', animation: 'pulse-live 1.6s ease-in-out infinite' }}>
            {serverOnline === null ? 'CONNECTING…' : 'SERVER OFFLINE'}
          </div>
          {serverOnline === false && (
            <div className="text-dim" style={{ fontSize: '0.72rem' }}>Set the World Server address below to go online.</div>
          )}
        </div>
      )}
    </div>
  )

  return (
    <div className="page">
      <div className="section-header" style={{ fontSize: '1.4rem' }}>World</div>
      <div className="text-dim text-sm" style={{ marginBottom: '1rem' }}>
        Everything beyond your Tower: PvP arenas, leaderboards, raids, and server-wide tournaments.
        Nothing here ever touches your save — heroes never truly die in the World.
      </div>

      {msg && <div className="text-sm" style={{ marginBottom: '1rem', color: 'var(--gold)' }}>{msg}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.4fr) minmax(0, 1fr)', gap: '1.2rem', alignItems: 'start' }}>
        {/* ── Left column: Arena (live PvP) ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          <SectionVeil>
          <div className="card" style={{ padding: '1rem' }}>
            <div className="section-header">⚔ Arena</div>

      {!token ? (
        <div style={{ maxWidth: 400 }}>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <button className={`btn ${authMode === 'login' ? 'btn-gold' : ''}`} onClick={() => setAuthMode('login')}>Login</button>
            <button className={`btn ${authMode === 'register' ? 'btn-gold' : ''}`} onClick={() => setAuthMode('register')}>Register</button>
          </div>
          <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <input type="text" className="input" placeholder="Username" value={authUsername} onChange={e => setAuthUsername(e.target.value)}
              style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', padding: '0.5rem', color: '#fff', borderRadius: 4 }} />
            <input type="password" className="input" placeholder="Password" value={authPassword} onChange={e => setAuthPassword(e.target.value)}
              style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', padding: '0.5rem', color: '#fff', borderRadius: 4 }} />
            <button type="submit" className="btn btn-gold" disabled={busy || !authUsername.trim() || !authPassword}>
              {authMode === 'login' ? 'Log In' : 'Register'}
            </button>
          </form>
        </div>
      ) : (
        <>
          <div className="card" style={{ marginBottom: '1rem', padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>Logged in as <span className="text-gold" style={{ fontWeight: 'bold' }}>{username}</span></div>
            <button className="btn" onClick={handleLogout}>Log Out</button>
          </div>

          <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
            <div className="text-dim text-sm" style={{ marginBottom: '0.5rem' }}>Submit a Team to the Arena</div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <select className="input" value={teamId} onChange={e => setTeamId(Number(e.target.value))}
                style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', padding: '0.5rem', color: '#fff', borderRadius: 4 }}>
                {teamEntries.length === 0 && <option value={1}>Team 1 (empty)</option>}
                {teamEntries.map(([id, heroes]) => (
                  <option key={id} value={id}>Team {id} — {heroes.map(h => h.name).join(', ')}</option>
                ))}
              </select>
              <button className="btn btn-gold" disabled={busy} onClick={handleSubmitTeam}>Submit Team</button>
              {teamSubmitted && <span style={{ color: 'var(--green)' }}>✓ Submitted</span>}
            </div>
          </div>

          <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
            <div className="text-dim text-sm" style={{ marginBottom: '0.5rem' }}>Challenge a Player</div>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <button className="btn btn-gold" disabled={busy} onClick={handleMatchmake}>Find Ranked Match</button>
              <span className="text-dim text-sm">or</span>
              <form onSubmit={handleChallenge} style={{ display: 'flex', gap: '0.5rem', flex: 1 }}>
                <input type="text" className="input" placeholder="Opponent's username" value={opponent} onChange={e => setOpponent(e.target.value)}
                  style={{ flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', padding: '0.5rem', color: '#fff', borderRadius: 4 }} />
                <button type="submit" className="btn btn-gold" disabled={busy || !opponent.trim()}>Direct Fight</button>
              </form>
            </div>
          </div>

          {fightResult && (
            <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: '1.2rem', marginBottom: '0.5rem', color: fightResult.winner === username ? 'var(--green)' : 'var(--red)' }}>
                {fightResult.winner === username ? '✓ Victory' : '✗ Defeat'} — {fightResult.winner} defeated {fightResult.loser}
                {fightResult.elo_change?.[username] != null && (
                  <span style={{ marginLeft: '0.8rem', fontSize: '0.9rem', color: 'var(--gold)' }}>
                    ELO: {fightResult.elo_change[username]}
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', maxHeight: '40vh', overflowY: 'auto' }}>
                {fightResult.log.map((line, i) => (
                  <div key={i} className="text-dim text-sm">{line}</div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
          </div>
          </SectionVeil>

          {/* ── Raids — coming soon ── */}
          <div className="card" style={{ padding: '1rem', position: 'relative', overflow: 'hidden' }}>
            <div className="section-header">🏰 Raids</div>
            <div className="text-dim text-sm" style={{ lineHeight: 1.6 }}>
              Every base has coordinates on the World map. Raid other players to steal resources —
              or their heroes. Build defensive facilities (the Magic Engineer's arcane cannons let even
              1★ heroes hold a wall), and keep your roster loyal: a captured hero with low affinity
              may not stay yours for long.
            </div>
            {/* Placeholder map grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: 3, marginTop: '0.9rem', opacity: 0.5 }}>
              {Array.from({ length: 24 }).map((_, i) => (
                <div key={i} style={{
                  aspectRatio: '1', borderRadius: 3,
                  background: i === 11 ? 'rgba(201,168,76,0.4)' : 'rgba(255,255,255,0.04)',
                  border: i === 11 ? '1px solid var(--gold)' : '1px solid rgba(255,255,255,0.06)',
                }} title={i === 11 ? 'Your base' : undefined} />
              ))}
            </div>
            <div style={{ position: 'absolute', top: '0.9rem', right: '1rem', fontFamily: 'Cinzel, serif', fontSize: '0.68rem', letterSpacing: '0.15em', color: '#b06aff', border: '1px solid rgba(160,80,255,0.5)', borderRadius: 999, padding: '0.15rem 0.7rem' }}>
              COMING SOON
            </div>
          </div>

          {/* ── Tournaments — coming soon ── */}
          <div className="card" style={{ padding: '1rem', position: 'relative' }}>
            <div className="section-header">🏆 Tournaments & Events</div>
            <div className="text-dim text-sm" style={{ lineHeight: 1.6, marginBottom: '0.8rem' }}>
              Server-wide event cycles across four brackets. Placements earn points; the cycle's top
              scorers take home massive rewards.
            </div>
            <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
              {['1v1 Duels', '2v2 Pairs', '4v4 Warbands', 'Battle Royale'].map(b => (
                <span key={b} style={{
                  fontFamily: 'Cinzel, serif', fontSize: '0.75rem', letterSpacing: '0.08em',
                  border: '1px solid var(--border-hi)', borderRadius: 999, padding: '0.3rem 0.9rem',
                  color: 'var(--text-dim)', background: 'rgba(255,255,255,0.03)',
                }}>{b}</span>
              ))}
            </div>
            <div style={{ position: 'absolute', top: '0.9rem', right: '1rem', fontFamily: 'Cinzel, serif', fontSize: '0.68rem', letterSpacing: '0.15em', color: '#b06aff', border: '1px solid rgba(160,80,255,0.5)', borderRadius: 999, padding: '0.15rem 0.7rem' }}>
              COMING SOON
            </div>
          </div>
        </div>

        {/* ── Right column: leaderboards/market + server config ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          <SectionVeil>
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', overflowX: 'auto' }}>
              <button className={`btn ${activeTab === 'pvp' ? 'btn-gold' : ''}`} onClick={() => setActiveTab('pvp')}>PvP Leaderboard</button>
              <button className={`btn ${activeTab === 'pve' ? 'btn-gold' : ''}`} onClick={() => setActiveTab('pve')}>PvE Leaderboard</button>
              <button className={`btn ${activeTab === 'market' ? 'btn-gold' : ''}`} onClick={() => setActiveTab('market')}>Training Market</button>
            </div>
            
            {activeTab === 'pvp' && (
              <>
                {leaderboard.length === 0 && <div className="text-dim text-sm">No matches recorded yet.</div>}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  {leaderboard.map((p, i) => (
                    <div key={p.username} style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                      <span className="text-dim" style={{ minWidth: 30 }}>#{i + 1}</span>
                      <span style={{ color: p.username === username ? 'var(--gold)' : 'inherit', flex: 1 }}>{p.username}</span>
                      <span style={{ color: 'var(--gold)', fontWeight: 'bold', minWidth: 50, textAlign: 'right' }}>{p.elo ?? 1000}</span>
                      <span className="text-dim">{p.wins}W / {p.losses}L</span>
                    </div>
                  ))}
                </div>
              </>
            )}

            {activeTab === 'pve' && (
              <>
                {pveLeaderboard.length === 0 && <div className="text-dim text-sm">No highest floor records yet.</div>}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <div className="text-dim text-sm" style={{ marginBottom: '0.5rem' }}>Highest Floor</div>
                  {pveLeaderboard.map((p, i) => (
                    <div key={p.username} style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                      <span className="text-dim" style={{ minWidth: 30 }}>#{i + 1}</span>
                      <span style={{ color: p.username === username ? 'var(--gold)' : 'inherit', flex: 1 }}>{p.username}</span>
                      <span className="text-dim">Floor {p.highest_floor}</span>
                    </div>
                  ))}
                </div>
              </>
            )}

            {activeTab === 'market' && (
              <div>
                <div className="text-dim text-sm" style={{ marginBottom: '1rem' }}>
                  Rent out your strongest heroes as Teachers, or hire a Teacher for your heroes. You earn gems when someone hires your Teacher!
                </div>
                
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1 }}>
                    <div className="text-hi text-sm" style={{ marginBottom: '0.5rem' }}>List a Teacher</div>
                    <select className="input" value={marketTeacherId} onChange={e => setMarketTeacherId(e.target.value)} style={{ width: '100%', marginBottom: '0.5rem' }}>
                      <option value="">Select Hero...</option>
                      {allHeroes.map(h => <option key={h.id} value={h.id}>{h.name} (Lv.{h.level})</option>)}
                    </select>
                    <input type="number" className="input" value={marketGemCost} onChange={e => setMarketGemCost(e.target.value)} placeholder="Gem Cost" style={{ width: '100%', marginBottom: '0.5rem' }} />
                    <button className="btn btn-gold" style={{ width: '100%' }} onClick={handleListTeacher} disabled={busy || !marketTeacherId}>List Teacher</button>
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div className="text-hi text-sm" style={{ marginBottom: '0.5rem' }}>Your Student</div>
                    <select className="input" value={marketStudentId} onChange={e => setMarketStudentId(e.target.value)} style={{ width: '100%', marginBottom: '0.5rem' }}>
                      <option value="">Select Hero to Train...</option>
                      {allHeroes.map(h => <option key={h.id} value={h.id}>{h.name} (Lv.{h.level})</option>)}
                    </select>
                  </div>
                </div>

                <div className="text-hi text-sm" style={{ marginBottom: '0.5rem' }}>Available Teachers</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {marketListings.length === 0 && <div className="text-dim text-sm">No teachers available right now.</div>}
                  {marketListings.map(listing => (
                    <div key={listing.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: 4 }}>
                      <div>
                        <div style={{ color: 'var(--gold)' }}>{listing.hero_name} <span className="text-dim" style={{ fontSize: '0.8rem' }}>({listing.hero_class})</span></div>
                        <div className="text-dim text-sm">Master: {listing.username}</div>
                        <div className="text-dim" style={{ fontSize: '0.75rem', marginTop: '0.2rem' }}>
                          Stats: HP {listing.hero_stats.max_health} · ATK {listing.hero_stats.attack} · DEF {listing.hero_stats.defense} · SPD {listing.hero_stats.speed}
                        </div>
                      </div>
                      <button className="btn btn-gold" onClick={() => handleHireTeacher(listing.id)} disabled={busy || listing.username === username} style={{ padding: '0.4rem 0.8rem' }}>
                        Hire ({listing.gem_cost} <GameIcon name="gem" size={14} />)
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          </SectionVeil>

          {/* Server config — setup detail, lives at the bottom of the column */}
          <details className="card" open={!serverUrl} style={{ padding: '0.8rem 1rem' }}>
            <summary className="text-dim text-sm" style={{ cursor: 'pointer', userSelect: 'none' }}>
              ⚙ World Server {serverOnline === true
                ? <span style={{ color: 'var(--green)' }}>· online — {serverUrl}</span>
                : serverUrl
                  ? <span style={{ color: 'var(--red)' }}>· unreachable — {serverUrl}</span>
                  : <span style={{ color: 'var(--red)' }}>· not configured</span>}
            </summary>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.8rem' }}>
              <input
                type="text"
                className="input"
                placeholder="http://your-server-address:8001"
                value={serverUrl}
                onChange={e => setServerUrl(e.target.value)}
                style={{ flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', padding: '0.5rem', color: '#fff', borderRadius: 4 }}
              />
              <button className="btn" onClick={handleSaveUrl}>Save</button>
            </div>
          </details>
        </div>
      </div>
    </div>
  )
}
