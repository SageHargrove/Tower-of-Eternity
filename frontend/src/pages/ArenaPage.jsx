import React, { useState, useEffect } from 'react'
import { getAllTeams, getArenaSnapshot, getBanner } from '../api/client'
import { StackedTitle, SectionHeader, Panel, IlmButton, Diamond } from '../components/ilm/Ilm'
import {
  getArenaServerUrl, setArenaServerUrl, getArenaToken, getArenaUsername, clearArenaSession,
  arenaRegister, arenaLogin, arenaSubmitTeam, arenaChallenge, arenaMatchmake, arenaLeaderboard,
  arenaMyRewards, arenaClaimReward, arenaMarketList, arenaMarketGet, arenaMarketHire, arenaSetBanner,
  socialAllies, arenaMyMatches
} from '../api/arenaServerClient'
import Pennant from '../components/Pennant'
import StakesBanner from '../components/StakesBanner'
import { TournamentRegistration, ScoutReport } from '../components/FeatureModals'
import { receiveMail, applyTraining, listHeroes, recordArenaResult } from '../api/client'

export default function ArenaPage() {
  const [serverUrl, setServerUrl] = useState(getArenaServerUrl())
  const [banner, setBanner] = useState(null)
  useEffect(() => { getBanner().then(setBanner).catch(() => {}) }, [])
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
  // Session bout ledger — the RECENT BOUTS column. The server keeps no
  // history endpoint yet, so this remembers the bouts fought this sitting.
  const [bouts, setBouts] = useState([])
  const [expandedBout, setExpandedBout] = useState(null)
  const [marketOpen, setMarketOpen] = useState(false)
  const [showTournament, setShowTournament] = useState(false)
  const [showScout, setShowScout] = useState(false)

  const [leaderboard, setLeaderboard] = useState([])
  const [pveLeaderboard, setPveLeaderboard] = useState([])
  const [activeTab, setActiveTab] = useState('pvp')
  // Board scope (spec: GLOBAL / FRIENDS toggle on its own row, same RANK #x OF y format).
  const [scope, setScope] = useState('global')
  const [allies, setAllies] = useState([])

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

  // Carry the local Banner Studio standard to the world server so opponents
  // see it on the boards and the raid map. Fire-and-forget on login.
  useEffect(() => {
    if (!token) return
    getBanner().then(b => {
      if (b && (b.cloth || b.emblem || b.paint)) arenaSetBanner(b).catch(() => {})
    }).catch(() => {})
    socialAllies().then(d => setAllies((d?.allies || d || []).map(a => a.username || a))).catch(() => {})
    // Seed the RECENT BOUTS ledger from server history so it survives reloads.
    arenaMyMatches(8).then(d => {
      setBouts(prev => prev.length ? prev : (d.matches || []).map(m => ({
        winner: m.winner, loser: m.won ? m.opponent : getArenaUsername(), opponent: m.opponent,
      })))
    }).catch(() => {})
  }, [token])

  // null = still trying, true = reachable, false = unreachable.
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
              await arenaClaimReward(rew.id);
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
      setBouts(b => [result, ...b].slice(0, 8))
      if (result.winner === username && result.elo_change?.[username] != null) {
        recordArenaResult(true, result.elo_change[username]).catch(() => {})
      } else if (result.loser === username && result.elo_change?.[username] != null) {
        recordArenaResult(false, result.elo_change[username]).catch(() => {})
      }
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
      setBouts(b => [result, ...b].slice(0, 8))
      setMsg(`Matched against ${result.opponent}!`)
      if (result.winner === username && result.elo_change?.[username] != null) {
        recordArenaResult(true, result.elo_change[username]).catch(() => {})
      } else if (result.loser === username && result.elo_change?.[username] != null) {
        recordArenaResult(false, result.elo_change[username]).catch(() => {})
      }
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
      const stats = {
        max_health: h.max_health, strength: h.strength, intelligence: h.intelligence,
        agility: h.agility, endurance: h.endurance, willpower: h.willpower,
      }
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
      const res = await arenaMarketHire(listingId);
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

  // The player's own standing, derived from the live board.
  const myRank = leaderboard.findIndex(p => p.username === username)
  const me = myRank >= 0 ? leaderboard[myRank] : null
  const myWins = me?.wins ?? 0
  const myLosses = me?.losses ?? 0

  const fieldStyle = { background: 'rgba(0,0,0,0.35)', border: '1px solid var(--border)', padding: '0.55rem 0.65rem', color: '#efe8da', width: '100%' }

  const micro = { fontFamily: "'Cinzel',serif", letterSpacing: '.16em', fontSize: 9 }

  // Podium diamonds for the board: gold / silver / bronze, then hollow.
  const RankDiamond = ({ i }) => {
    const fills = [
      'linear-gradient(135deg,#ffd88a,#b89762)',
      'linear-gradient(135deg,#e6ebf2,#9aa6b8)',
      'linear-gradient(135deg,#e0a06a,#9a6032)',
    ]
    const filled = i < 3
    return (
      <span style={{ width: 26, height: 26, transform: 'rotate(45deg)', flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: filled ? fills[i] : 'transparent', border: filled ? 'none' : '1px solid rgba(150,110,230,.4)' }}>
        <span style={{ transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontWeight: filled ? 900 : 500, fontSize: 12, color: filled ? '#0a0710' : 'var(--muted)' }}>{i + 1}</span>
      </span>
    )
  }

  const fullBoard = activeTab === 'pvp' ? leaderboard : pveLeaderboard
  const board = scope === 'friends'
    ? fullBoard.filter(p => p.username === username || allies.includes(p.username))
    : fullBoard
  const meIdx = board.findIndex(p => p.username === username)

  return (
    <div className="page">
      {showTournament && <TournamentRegistration onClose={() => setShowTournament(false)} />}
      {showScout && <ScoutReport onClose={() => setShowScout(false)} />}

      <div style={{ display: 'flex', gap: 26, alignItems: 'flex-start', flexWrap: 'wrap' }}>

        {/* ═══ LEFT — the console ═══ */}
        <div className="ent-1" style={{ width: 320, flex: '1 1 300px', maxWidth: 380 }}>
          <div className="ilm-eyebrow" style={{ marginBottom: 2 }}>BEYOND THE TOWER</div>
          <div className="ilm-title-stack">
            <div className="ghost">ARENA</div>
            <div className="solid">WORLD</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2, marginBottom: 14 }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', flex: 'none',
              background: serverOnline === true ? '#4a9a6a' : serverOnline === null ? '#c9a84c' : '#c04040',
              boxShadow: `0 0 8px ${serverOnline === true ? '#4a9a6a' : serverOnline === null ? '#c9a84c' : '#c04040'}`,
              animation: 'pulse-live 2s ease-in-out infinite' }} />
            <span style={{ ...micro, letterSpacing: '.2em', fontSize: 10, color: serverOnline === true ? '#8fbf9f' : serverOnline === null ? 'var(--gold-hi)' : '#e08585' }}>
              {serverOnline === true ? 'CONNECTED · WORLD SERVER' : serverOnline === null ? 'LISTENING · WORLD SERVER' : 'NO SIGNAL · WORLD SERVER'}
            </span>
          </div>

          {!token ? (
            <Panel tone="violet" corner style={{ padding: '1rem 1.1rem' }}>
              <div style={{ fontStyle: 'italic', color: 'var(--muted)', marginBottom: 12 }}>Enlist under your banner to enter the Lists.</div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <IlmButton variant={authMode === 'login' ? 'gold' : 'ghost'} onClick={() => setAuthMode('login')}>LOGIN</IlmButton>
                <IlmButton variant={authMode === 'register' ? 'gold' : 'ghost'} onClick={() => setAuthMode('register')}>REGISTER</IlmButton>
              </div>
              <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <input type="text" placeholder="Username" value={authUsername} onChange={e => setAuthUsername(e.target.value)} style={fieldStyle} />
                <input type="password" placeholder="Password" value={authPassword} onChange={e => setAuthPassword(e.target.value)} style={fieldStyle} />
                <IlmButton variant="gold" block type="submit" disabled={busy || !authUsername.trim() || !authPassword}>
                  {authMode === 'login' ? 'LOG IN' : 'REGISTER'}
                </IlmButton>
              </form>
            </Panel>
          ) : (
            <>
              {/* manager plate */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, border: '1px solid rgba(184,151,98,.35)', background: 'rgba(12,7,24,.5)', padding: '11px 14px' }}>
                <span style={{ ...micro, letterSpacing: '.2em', fontSize: 10, color: 'var(--muted)' }}>MANAGER</span>
                <span style={{ flex: 1 }} />
                <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.1em', fontSize: 13, color: 'var(--text-hi)' }}>{String(username).toUpperCase()}</span>
                <button onClick={handleLogout} title="Log out" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', fontSize: 11, padding: 0 }}>✎</button>
              </div>

              {/* rating panel */}
              <div style={{ marginTop: 14, border: '1px solid rgba(150,110,230,.35)', background: 'linear-gradient(160deg,rgba(42,22,80,.32),rgba(12,7,24,.6))', padding: '14px 18px', clipPath: 'polygon(0 0,100% 0,100% 100%,12px 100%)' }}>
                <div style={{ display: 'flex', alignItems: 'baseline' }}>
                  <span style={{ ...micro, letterSpacing: '.22em', fontSize: 10, color: 'var(--muted)' }}>ARENA RATING</span>
                  <span style={{ flex: 1 }} />
                  <span style={{ ...micro, letterSpacing: '.18em', fontSize: 10, color: 'var(--gold-hi)' }}>{myRank >= 0 ? `RANK #${myRank + 1}` : 'UNRANKED'}</span>
                </div>
                <div style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 40, color: 'var(--gold-hi)', lineHeight: 1.15 }}>
                  {(me?.elo ?? 1000).toLocaleString()}
                </div>
                <div style={{ fontStyle: 'italic', fontSize: 14, color: 'var(--muted)' }}>{myWins} W · {myLosses} L this season</div>
              </div>

              {/* deploy row */}
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 12 }}>
                <select value={teamId} onChange={e => setTeamId(Number(e.target.value))} style={{ ...fieldStyle, flex: 1, fontFamily: "'Cinzel',serif", fontSize: '0.72rem', letterSpacing: '.08em' }}>
                  {teamEntries.length === 0 && <option value={1}>TEAM 1 (EMPTY)</option>}
                  {teamEntries.map(([id, hs]) => <option key={id} value={id}>TEAM {id} — {hs.length} HEROES</option>)}
                </select>
                <IlmButton variant="ghost" disabled={busy} onClick={handleSubmitTeam}>{teamSubmitted ? 'DEPLOYED ◆' : 'DEPLOY'}</IlmButton>
              </div>

              {/* find match */}
              <button className="btn btn-primary" disabled={busy} onClick={handleMatchmake}
                style={{ width: '100%', marginTop: 12, padding: '13px 0', fontSize: '0.95rem', letterSpacing: '.28em' }}>
                {busy ? 'SEARCHING…' : 'FIND MATCH'}
              </button>
              <form onSubmit={handleChallenge} style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <input type="text" placeholder="Challenge a manager by name…" value={opponent} onChange={e => setOpponent(e.target.value)} style={{ ...fieldStyle, flex: 1, fontStyle: 'italic' }} />
                <IlmButton variant="ghost" type="submit" disabled={busy || !opponent.trim()}>DUEL</IlmButton>
              </form>

              <StakesBanner variant="echo" compact style={{ marginTop: 12 }} />
              <div style={{ textAlign: 'center', fontStyle: 'italic', fontSize: 15, color: 'var(--muted)', marginTop: 12, lineHeight: 1.6 }}>
                You fight snapshots of rival teams.<br />No hero ever truly dies here.
              </div>
            </>
          )}

          {msg && <div style={{ marginTop: 12, fontStyle: 'italic', fontSize: 14, color: 'var(--gold-hi)' }}>{msg}</div>}
        </div>

        {/* ═══ CENTER — bouts, market, halls beyond ═══ */}
        <div className="ent-2" style={{ flex: '1.3 1 400px', minWidth: 360 }}>
          <SectionHeader style={{ marginBottom: 12 }}>Recent Bouts</SectionHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {bouts.length === 0 && (
              <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 14, padding: '10px 2px' }}>
                No bouts fought this sitting — deploy a team and find a match.
              </div>
            )}
            {bouts.map((b, i) => {
              const won = b.winner === username
              const delta = b.elo_delta?.[username]
              const open = expandedBout === i
              return (
                <div key={i}>
                  <button onClick={() => setExpandedBout(open ? null : i)}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 14, padding: '12px 16px', cursor: 'pointer', textAlign: 'left',
                      background: 'rgba(12,7,24,.55)', border: '1px solid rgba(184,151,98,.25)',
                      borderLeft: `3px solid ${won ? '#4a9a6a' : '#c04040'}` }}>
                    <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.16em', fontSize: 13, color: won ? '#8fbf9f' : '#e08585', width: 84 }}>
                      {won ? 'VICTORY' : 'DEFEAT'}
                    </span>
                    <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.08em', fontSize: 13, color: 'var(--text-hi)', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      vs {(won ? b.loser : b.winner) || b.opponent || 'UNKNOWN'}
                    </span>
                    {delta != null && (
                      <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 18, color: won ? '#8fbf9f' : '#e08585' }}>
                        {delta > 0 ? '+' : ''}{delta}
                      </span>
                    )}
                  </button>
                  {open && b.log && (
                    <div style={{ border: '1px solid rgba(184,151,98,.2)', borderTop: 'none', background: 'rgba(8,6,14,.6)', padding: '10px 16px', maxHeight: 220, overflowY: 'auto' }}>
                      {b.log.map((line, li) => (
                        <div key={li} style={{ fontStyle: 'italic', fontSize: 13, color: 'var(--muted)', lineHeight: 1.6 }}>{line}</div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* training market */}
          <div style={{ marginTop: 18, border: '1px solid rgba(184,151,98,.35)', background: 'rgba(12,7,24,.5)', padding: '14px 18px' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
              <span style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 17, letterSpacing: '.06em', color: 'var(--text-hi)' }}>TRAINING MARKET</span>
              <span style={{ flex: 1 }} />
              <button onClick={() => setMarketOpen(o => !o)} style={{ background: 'none', border: 'none', cursor: 'pointer', ...micro, letterSpacing: '.18em', fontSize: 11, color: 'var(--gold-hi)' }}>
                {marketOpen ? 'CLOSE ▾' : 'ENTER ›'}
              </button>
            </div>
            <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 15, marginTop: 4, lineHeight: 1.5 }}>
              Pay rival managers' veterans to drill your roster — teaching skill carries lineage.
            </div>
            {marketOpen && (
              <div style={{ marginTop: 14, borderTop: '1px solid rgba(184,151,98,.2)', paddingTop: 14 }}>
                <div style={{ display: 'flex', gap: 14, marginBottom: 16, flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 170 }}>
                    <div style={{ ...micro, color: 'var(--gold-hi)', marginBottom: 6 }}>LIST A TEACHER</div>
                    <select value={marketTeacherId} onChange={e => setMarketTeacherId(e.target.value)} style={{ ...fieldStyle, marginBottom: 6 }}>
                      <option value="">Select hero…</option>
                      {allHeroes.map(h => <option key={h.id} value={h.id}>{h.name} (Lv.{h.level})</option>)}
                    </select>
                    <input type="number" value={marketGemCost} onChange={e => setMarketGemCost(e.target.value)} placeholder="Gem cost" style={{ ...fieldStyle, marginBottom: 6 }} />
                    <IlmButton variant="violet" block onClick={handleListTeacher} disabled={busy || !marketTeacherId}>LIST TEACHER</IlmButton>
                  </div>
                  <div style={{ flex: 1, minWidth: 170 }}>
                    <div style={{ ...micro, color: 'var(--gold-hi)', marginBottom: 6 }}>YOUR STUDENT</div>
                    <select value={marketStudentId} onChange={e => setMarketStudentId(e.target.value)} style={fieldStyle}>
                      <option value="">Select hero to train…</option>
                      {allHeroes.map(h => <option key={h.id} value={h.id}>{h.name} (Lv.{h.level})</option>)}
                    </select>
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {marketListings.length === 0 && <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 14 }}>No teachers on the market right now.</div>}
                  {marketListings.map(listing => (
                    <div key={listing.id} style={{ display: 'flex', alignItems: 'center', gap: 12, border: '1px solid rgba(184,151,98,.25)', background: 'rgba(8,6,14,.5)', padding: '9px 12px' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 12, letterSpacing: '.06em', color: 'var(--gold-hi)' }}>
                          {listing.hero_name} <span style={{ color: 'var(--muted)', fontWeight: 500 }}>· {listing.hero_class}</span>
                        </div>
                        <div style={{ fontStyle: 'italic', fontSize: 12, color: 'var(--muted)' }}>Master: {listing.username}</div>
                      </div>
                      <IlmButton variant="gold" onClick={() => handleHireTeacher(listing.id)} disabled={busy || listing.username === username}>
                        HIRE · {listing.gem_cost} ◆
                      </IlmButton>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Expeditions moved to the Skydock (Base) — they were never a
              multiplayer/World feature; you launch them from the docked hull. */}

          {/* raids + tournament */}
          <div style={{ display: 'flex', gap: 14, marginTop: 14, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 220, border: '1px dashed rgba(150,110,230,.4)', background: 'rgba(12,7,24,.3)', padding: '16px 18px' }}>
              <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 15, letterSpacing: '.08em', color: 'var(--text-hi)' }}>BASE RAIDS</div>
              <div style={{ ...micro, letterSpacing: '.2em', color: 'var(--muted)', marginTop: 4 }}>COMING SOON</div>
              <button onClick={() => setShowScout(true)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, marginTop: 10, ...micro, letterSpacing: '.16em', fontSize: 10, color: 'var(--lavender)' }}>
                PREVIEW A SCOUT REPORT ›
              </button>
            </div>
            <div style={{ flex: 1, minWidth: 220, border: '1px dashed rgba(184,151,98,.4)', background: 'rgba(12,7,24,.3)', padding: '16px 18px' }}>
              <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 900, fontSize: 15, letterSpacing: '.08em', color: 'var(--text-hi)' }}>GRAND TOURNAMENT</div>
              <div style={{ ...micro, letterSpacing: '.2em', color: 'var(--muted)', marginTop: 4 }}>SEASONAL BRACKETS</div>
              <button onClick={() => setShowTournament(true)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, marginTop: 10, ...micro, letterSpacing: '.16em', fontSize: 10, color: 'var(--gold-hi)' }}>
                REGISTRATION ›
              </button>
            </div>
          </div>
        </div>

        {/* ═══ RIGHT — leaderboard ═══ */}
        <div className="ent-3" style={{ width: 380, flex: '1 1 340px', maxWidth: 440, border: '1px solid rgba(184,151,98,.3)', background: 'rgba(12,7,24,.45)', padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ width: 7, height: 7, transform: 'rotate(45deg)', background: 'var(--gold)', display: 'inline-block' }} />
            <span style={{ fontFamily: "'Cinzel',serif", letterSpacing: '.24em', fontSize: 11, color: 'var(--gold)' }}>LEADERBOARD</span>
            <span style={{ height: 1, flex: 1, background: 'rgba(184,151,98,.2)' }} />
            {[['pvp', 'PVP'], ['pve', 'PVE']].map(([id, label]) => (
              <button key={id} onClick={() => setActiveTab(id)}
                style={{ cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 9, letterSpacing: '.14em', padding: '3px 12px',
                  color: activeTab === id ? '#0a0710' : 'var(--muted)',
                  background: activeTab === id ? 'linear-gradient(120deg,#c8a9f5,#8b46d6)' : 'none',
                  border: activeTab === id ? 'none' : '1px solid rgba(150,110,230,.35)',
                  clipPath: 'polygon(5px 0,100% 0,calc(100% - 5px) 100%,0 100%)' }}>
                {label}
              </button>
            ))}
          </div>
          {/* scope row — GLOBAL / FRIENDS, same RANK #x OF y format in both */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '10px 0 2px' }}>
            <span style={{ ...micro, letterSpacing: '.18em', fontSize: 9, color: 'var(--muted)' }}>VIEW</span>
            {[['global', 'GLOBAL'], ['friends', 'FRIENDS']].map(([id, label]) => (
              <button key={id} onClick={() => setScope(id)}
                style={{ cursor: 'pointer', fontFamily: "'Cinzel',serif", fontWeight: scope === id ? 700 : 500, fontSize: 9, letterSpacing: '.14em', padding: '3px 12px',
                  color: scope === id ? '#0a0710' : 'var(--muted)',
                  background: scope === id ? 'linear-gradient(120deg,#8fbf9f,#4a9a6a)' : 'none',
                  border: scope === id ? 'none' : '1px solid rgba(150,110,230,.35)',
                  clipPath: 'polygon(5px 0,100% 0,calc(100% - 5px) 100%,0 100%)' }}>
                {label}
              </button>
            ))}
            <span style={{ flex: 1 }} />
            {meIdx >= 0 && <span style={{ ...micro, letterSpacing: '.14em', fontSize: 9, color: 'var(--gold-hi)' }}>RANK #{meIdx + 1} OF {board.length.toLocaleString()}</span>}
          </div>
          <div style={{ margin: '6px 0 6px' }}>
            <span style={{ ...micro, letterSpacing: '.18em', fontSize: 9, color: 'var(--muted)' }}>{activeTab === 'pvp' ? 'MANAGER · RATING' : 'CLIMBER · HIGH FLOOR'}</span>
          </div>

          {serverOnline === false && (
            <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 14, padding: '18px 2px', textAlign: 'center' }}>
              No signal from the world server — the boards are dark.
            </div>
          )}
          {serverOnline === null && (
            <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 14, padding: '18px 2px', textAlign: 'center', animation: 'pulse-live 2s ease-in-out infinite' }}>
              Listening for the world server…
            </div>
          )}
          {serverOnline === true && board.length === 0 && (
            <div style={{ fontStyle: 'italic', color: 'var(--muted)', fontSize: 14, padding: '18px 2px', textAlign: 'center' }}>
              The board stands empty — be the first name carved on it.
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginTop: 8 }}>
            {board.slice(0, 8).map((p, i) => {
              const isMe = p.username === username
              return (
                <div key={p.username} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 10px',
                  border: isMe ? '1px solid rgba(216,187,132,.55)' : '1px solid transparent',
                  background: isMe ? 'linear-gradient(90deg,rgba(184,151,98,.1),transparent)' : 'transparent' }}>
                  <RankDiamond i={i} />
                  <span style={{ width: 16, flex: 'none', display: 'inline-flex', justifyContent: 'center' }}>
                    {p.banner?.cloth
                      ? <Pennant cloth={p.banner.cloth} cut={p.banner.cut || 'swallow'} frameTier={p.banner.frame_tier || 1} sigil={p.banner.sigil} emblem={p.banner.emblem} paint={p.banner.paint} width={13} />
                      : <span style={{ width: 8, height: 12, border: '1px solid rgba(150,110,230,.35)', display: 'inline-block' }} />}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.08em', fontSize: 13, color: isMe ? 'var(--gold-hi)' : 'var(--text-hi)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {String(p.username).toUpperCase()}{isMe ? ' — YOU' : ''}
                    </div>
                    {activeTab === 'pvp' && <div style={{ ...micro, letterSpacing: '.14em', fontSize: 8, color: 'var(--muted)', marginTop: 2 }}>{p.wins ?? 0}W · {p.losses ?? 0}L</div>}
                  </div>
                  <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 20, color: isMe ? 'var(--gold-hi)' : 'var(--text-hi)' }}>
                    {activeTab === 'pvp' ? (p.elo ?? 1000).toLocaleString() : `F${p.highest_floor ?? 0}`}
                  </span>
                </div>
              )
            })}

            {meIdx >= 8 && (
              <>
                <div style={{ textAlign: 'center', color: 'var(--muted)', letterSpacing: '.4em', fontSize: 10 }}>···</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 10px', border: '1px solid rgba(216,187,132,.55)', background: 'linear-gradient(90deg,rgba(184,151,98,.1),transparent)' }}>
                  <span style={{ width: 26, height: 26, transform: 'rotate(45deg)', flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(216,187,132,.6)' }}>
                    <span style={{ transform: 'rotate(-45deg)', fontFamily: "'Cinzel',serif", fontWeight: 700, fontSize: 10, color: 'var(--gold-hi)' }}>{meIdx + 1}</span>
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: "'Cinzel',serif", fontWeight: 700, letterSpacing: '.08em', fontSize: 13, color: 'var(--gold-hi)' }}>{String(username).toUpperCase()} — YOU</div>
                  </div>
                  <span style={{ fontFamily: "'Cormorant Garamond',serif", fontWeight: 700, fontSize: 20, color: 'var(--gold-hi)' }}>
                    {activeTab === 'pvp' ? (board[meIdx].elo ?? 1000).toLocaleString() : `F${board[meIdx].highest_floor ?? 0}`}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

