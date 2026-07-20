let audioCtx = null
let bgmOscillators = []
let soundEnabled = localStorage.getItem('soundEnabled') !== 'false'
let globalBgmVolume = parseFloat(localStorage.getItem('bgmVolume') || '0.5')
let globalSfxVolume = parseFloat(localStorage.getItem('sfxVolume') || '0.5')

export function setSoundEnabled(enabled) {
  soundEnabled = enabled
  localStorage.setItem('soundEnabled', enabled)
  if (!enabled) {
    stopBgm()
  } else {
    playBgm()
  }
}

export function isSoundEnabled() {
  return soundEnabled
}

export function setBgmVolume(vol) {
  globalBgmVolume = vol
  localStorage.setItem('bgmVolume', vol)
  if (masterBgmGain && audioCtx) {
    const now = audioCtx.currentTime
    masterBgmGain.gain.cancelScheduledValues(now)
    masterBgmGain.gain.setValueAtTime(Math.max(0.0001, masterBgmGain.gain.value), now)
    masterBgmGain.gain.linearRampToValueAtTime(Math.max(0.0001, _bedVol()), now + 0.1)
  }
}

export function setSfxVolume(vol) {
  globalSfxVolume = vol
  localStorage.setItem('sfxVolume', vol)
}

export function initAudio() {
  if (audioCtx) {
    if (audioCtx.state === 'suspended') audioCtx.resume()
    return
  }
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    
    _ensureGraph()

    // Ensure it resumes on any user interaction, and (re)start BGM if the
    // browser's autoplay policy blocked the initial start.
    const resumeAudio = () => {
      if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume()
      if (soundEnabled && !curVoice && !takeoverActive) playBgm()
      document.removeEventListener('click', resumeAudio)
    }
    document.addEventListener('click', resumeAudio)

    if (soundEnabled) {
      if (audioCtx.state === 'suspended') audioCtx.resume()
      playBgm()
    }
  } catch (e) {
    console.error("Web Audio API not supported", e)
  }
}

export function playClick() {
  if (!soundEnabled || !audioCtx) return
  if (globalSfxVolume === 0) return
  if (audioCtx.state === 'suspended') audioCtx.resume()

  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  
  osc.type = 'sine'
  osc.frequency.setValueAtTime(800, audioCtx.currentTime)
  osc.frequency.exponentialRampToValueAtTime(1200, audioCtx.currentTime + 0.05)
  
  gain.gain.setValueAtTime(0.02 * globalSfxVolume, audioCtx.currentTime)
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05)
  
  osc.connect(gain)
  gain.connect(audioCtx.destination)
  
  osc.start()
  osc.stop(audioCtx.currentTime + 0.05)
}

// kind: 'melee' | 'caster' | 'ranged' | 'enemy' — a rough archetype bucket
// derived from the attacker's existing power_stat/is_ranged combat fields
// (see CombatArena's classifyAttacker), not a separate per-class sound list.
export function playHitSound(kind, isCrit = false) {
  if (!soundEnabled || !audioCtx) return
  if (globalSfxVolume === 0) return
  if (audioCtx.state === 'suspended') audioCtx.resume()

  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  const vol = (isCrit ? 0.05 : 0.03) * globalSfxVolume
  const now = audioCtx.currentTime

  if (kind === 'caster') {
    osc.type = 'sine'
    osc.frequency.setValueAtTime(isCrit ? 1100 : 900, now)
    osc.frequency.exponentialRampToValueAtTime(isCrit ? 1900 : 1400, now + 0.12)
    gain.gain.setValueAtTime(vol, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18)
    osc.connect(gain); gain.connect(audioCtx.destination)
    osc.start(); osc.stop(now + 0.18)
  } else if (kind === 'ranged') {
    osc.type = 'triangle'
    osc.frequency.setValueAtTime(700, now)
    osc.frequency.exponentialRampToValueAtTime(200, now + 0.08)
    gain.gain.setValueAtTime(vol, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09)
    osc.connect(gain); gain.connect(audioCtx.destination)
    osc.start(); osc.stop(now + 0.09)
  } else if (kind === 'enemy') {
    osc.type = 'sawtooth'
    osc.frequency.setValueAtTime(150, now)
    osc.frequency.exponentialRampToValueAtTime(90, now + 0.1)
    gain.gain.setValueAtTime(vol, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12)
    osc.connect(gain); gain.connect(audioCtx.destination)
    osc.start(); osc.stop(now + 0.12)
  } else { // melee
    osc.type = 'square'
    osc.frequency.setValueAtTime(isCrit ? 320 : 220, now)
    osc.frequency.exponentialRampToValueAtTime(isCrit ? 180 : 130, now + 0.07)
    gain.gain.setValueAtTime(vol, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08)
    osc.connect(gain); gain.connect(audioCtx.destination)
    osc.start(); osc.stop(now + 0.08)
  }
}

// ─── Summoning / ritual SFX kit ─────────────────────────────────────
// All synthesized in WebAudio (same approach as playHitSound) — zero asset
// files, ships instantly, respects the SFX volume slider. If real samples
// arrive later, each of these is one function-body swap.

function _ready() {
  if (!soundEnabled || !audioCtx || globalSfxVolume === 0) return false
  if (audioCtx.state === 'suspended') audioCtx.resume()
  return true
}

let _noiseBuf = null
function _noise() {
  if (!_noiseBuf) {
    _noiseBuf = audioCtx.createBuffer(1, audioCtx.sampleRate * 0.5, audioCtx.sampleRate)
    const d = _noiseBuf.getChannelData(0)
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1
  }
  const src = audioCtx.createBufferSource()
  src.buffer = _noiseBuf
  return src
}

function _tone(freq, { type = 'sine', vol = 0.03, at = 0, dur = 0.15, slideTo = null } = {}) {
  const now = audioCtx.currentTime + at
  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  osc.type = type
  osc.frequency.setValueAtTime(freq, now)
  if (slideTo) osc.frequency.exponentialRampToValueAtTime(slideTo, now + dur)
  gain.gain.setValueAtTime(vol * globalSfxVolume, now)
  gain.gain.exponentialRampToValueAtTime(0.0008, now + dur)
  osc.connect(gain); gain.connect(audioCtx.destination)
  osc.start(now); osc.stop(now + dur)
}

// Card flip: a short air-whoosh (band-passed noise sweep) + a paper snap.
export function playFlip() {
  if (!_ready()) return
  const now = audioCtx.currentTime
  const noise = _noise()
  const bp = audioCtx.createBiquadFilter()
  bp.type = 'bandpass'
  bp.frequency.setValueAtTime(600, now)
  bp.frequency.exponentialRampToValueAtTime(2600, now + 0.16)
  bp.Q.value = 1.2
  const g = audioCtx.createGain()
  g.gain.setValueAtTime(0.05 * globalSfxVolume, now)
  g.gain.exponentialRampToValueAtTime(0.001, now + 0.18)
  noise.connect(bp); bp.connect(g); g.connect(audioCtx.destination)
  noise.start(now); noise.stop(now + 0.2)
  _tone(1900, { type: 'triangle', vol: 0.025, at: 0.14, dur: 0.05 })
}

// Rarity stinger, played on top of the flip. Escalates with impact tier
// (hero birth star / equipment tier bucket): 1-3 a soft pluck, 4-5 a gold
// two-note chime, 6+ a rising three-note arpeggio with shimmer.
export function playRevealStinger(tier = 1) {
  if (!_ready()) return
  if (tier >= 6) {
    _tone(523, { vol: 0.05, at: 0.10, dur: 0.35 })
    _tone(784, { vol: 0.05, at: 0.24, dur: 0.35 })
    _tone(1046, { vol: 0.06, at: 0.38, dur: 0.6 })
    _tone(2093, { type: 'triangle', vol: 0.02, at: 0.38, dur: 0.8 })
    _tone(3136, { type: 'sine', vol: 0.012, at: 0.5, dur: 0.9 })
  } else if (tier >= 4) {
    _tone(659, { vol: 0.045, at: 0.10, dur: 0.3 })
    _tone(988, { vol: 0.05, at: 0.26, dur: 0.5 })
    _tone(1976, { type: 'triangle', vol: 0.015, at: 0.26, dur: 0.6 })
  } else {
    _tone(740, { type: 'triangle', vol: 0.03, at: 0.10, dur: 0.22 })
  }
}

// Heavy thud when the summoning array slams in under the spread.
export function playArrayThud() {
  if (!_ready()) return
  const now = audioCtx.currentTime
  _tone(120, { type: 'sine', vol: 0.09, dur: 0.5, slideTo: 38 })
  const noise = _noise()
  const lp = audioCtx.createBiquadFilter()
  lp.type = 'lowpass'
  lp.frequency.value = 240
  const g = audioCtx.createGain()
  g.gain.setValueAtTime(0.06 * globalSfxVolume, now)
  g.gain.exponentialRampToValueAtTime(0.001, now + 0.4)
  noise.connect(lp); lp.connect(g); g.connect(audioCtx.destination)
  noise.start(now); noise.stop(now + 0.45)
  // faint arcane after-ring
  _tone(392, { type: 'sine', vol: 0.015, at: 0.15, dur: 0.9 })
}

// Gift reaction: loved = bright ascending pair, neutral = single soft note,
// disliked = flat descending pair.
export function playGiftChime(reaction = 'neutral') {
  if (!_ready()) return
  if (reaction === 'loved') {
    _tone(784, { vol: 0.04, dur: 0.2 })
    _tone(1175, { vol: 0.045, at: 0.14, dur: 0.4 })
    _tone(2349, { type: 'triangle', vol: 0.012, at: 0.14, dur: 0.5 })
  } else if (reaction === 'disliked') {
    _tone(392, { vol: 0.035, dur: 0.25 })
    _tone(311, { vol: 0.03, at: 0.2, dur: 0.4 })
  } else {
    _tone(659, { type: 'triangle', vol: 0.03, dur: 0.3 })
  }
}

// Synthesis rite: a low ominous swell that lasts roughly the consume
// animation (~2.3s).
export function playRiteHum() {
  if (!_ready()) return
  const now = audioCtx.currentTime
  const osc = audioCtx.createOscillator()
  const osc2 = audioCtx.createOscillator()
  const g = audioCtx.createGain()
  osc.type = 'sawtooth'; osc.frequency.setValueAtTime(55, now)
  osc.frequency.linearRampToValueAtTime(110, now + 2.0)
  osc2.type = 'sine'; osc2.frequency.setValueAtTime(220, now)
  osc2.frequency.linearRampToValueAtTime(440, now + 2.0)
  g.gain.setValueAtTime(0.0001, now)
  g.gain.exponentialRampToValueAtTime(0.05 * globalSfxVolume, now + 1.6)
  g.gain.exponentialRampToValueAtTime(0.0008, now + 2.4)
  osc.connect(g); osc2.connect(g); g.connect(audioCtx.destination)
  osc.start(now); osc2.start(now)
  osc.stop(now + 2.4); osc2.stop(now + 2.4)
}

// ─── Event-cue SFX (same synth approach — swap for samples anytime) ───

// Deed recorded: a quiet, proud two-note horn.
export function playDeedChime() {
  if (!_ready()) return
  _tone(587, { type: 'triangle', vol: 0.035, dur: 0.25 })
  _tone(880, { type: 'triangle', vol: 0.04, at: 0.18, dur: 0.5 })
  _tone(1760, { type: 'sine', vol: 0.012, at: 0.18, dur: 0.6 })
}

// Boss phase change: a low brass-like warning swell.
export function playPhaseHorn() {
  if (!_ready()) return
  _tone(98, { type: 'sawtooth', vol: 0.05, dur: 0.7, slideTo: 147 })
  _tone(196, { type: 'square', vol: 0.02, at: 0.1, dur: 0.6 })
  _tone(294, { type: 'sine', vol: 0.025, at: 0.35, dur: 0.5 })
}

// Floor cleared: short ascending fanfare.
export function playVictoryFanfare() {
  if (!_ready()) return
  _tone(523, { vol: 0.04, dur: 0.18 })
  _tone(659, { vol: 0.04, at: 0.14, dur: 0.18 })
  _tone(784, { vol: 0.045, at: 0.28, dur: 0.4 })
  _tone(1568, { type: 'triangle', vol: 0.015, at: 0.28, dur: 0.55 })
}

// Defeat: a slow low toll.
export function playDefeatToll() {
  if (!_ready()) return
  _tone(220, { type: 'sine', vol: 0.05, dur: 0.9, slideTo: 110 })
  _tone(110, { type: 'sine', vol: 0.04, at: 0.5, dur: 1.2, slideTo: 82 })
}

// Craft complete: anvil clang + metallic ring.
export function playCraftClang() {
  if (!_ready()) return
  const now = audioCtx.currentTime
  const noise = _noise()
  const hp = audioCtx.createBiquadFilter()
  hp.type = 'highpass'; hp.frequency.value = 1800
  const g = audioCtx.createGain()
  g.gain.setValueAtTime(0.06 * globalSfxVolume, now)
  g.gain.exponentialRampToValueAtTime(0.001, now + 0.12)
  noise.connect(hp); hp.connect(g); g.connect(audioCtx.destination)
  noise.start(now); noise.stop(now + 0.14)
  _tone(1245, { type: 'triangle', vol: 0.035, dur: 0.6 })
  _tone(2490, { type: 'sine', vol: 0.012, at: 0.02, dur: 0.8 })
}

// Evolution chosen: a rising arcane surge.
export function playEvolveSurge() {
  if (!_ready()) return
  _tone(262, { vol: 0.03, dur: 0.5, slideTo: 523 })
  _tone(523, { vol: 0.04, at: 0.35, dur: 0.5, slideTo: 1046 })
  _tone(2093, { type: 'triangle', vol: 0.015, at: 0.6, dur: 0.8 })
}

// ─── BGM manager (scene-based, Web Audio, gapless-capable) ──────────────────
// Real music now lives in /public/audio/*.ogg (see scripts/encode_audio.mjs).
// Screens set a SCENE; each scene maps to one or more tracks that rotate
// (shuffled, no immediate repeat). Switching scenes crossfades. Combat is
// session-persistent: re-asserting the same scene never restarts it.

const AUDIO_BASE = '/audio/'
// Ceiling on BGM so the volume slider's top end sits at a comfortable level
// rather than blasting the -16 LUFS masters at full gain. Effective bed volume
// = slider (0..1) × this.
const BGM_MASTER = 0.45
const _bedVol = () => globalBgmVolume * BGM_MASTER

// scene id → rotation pool of track slugs
const SCENES = {
  title:       ['title'],
  hub:         ['hub_1', 'hub_2', 'hub_3', 'hub_4'],
  summon:      ['summon_altar'],
  towerAscent: ['tower_ascent'],
  combat:      ['combat'],
  elite:       ['elite'],
  boss:        ['boss'],
  world:       ['world_1', 'world_2'],
  arena:       ['arena_1', 'arena_2'],
  tavern:      ['tavern_1', 'tavern_2'],
  synthesis:   ['synthesis_chamber'],
  athenaeum:   ['athenaeum'],
  memorial:    ['memorial'],
  expeditions: ['expeditions'],
  herald:      ['herald'],
}
// Optional per-track seamless loop points {slug: [startSec, endSec]} — tune
// later without re-encoding; default loops the whole buffer.
const LOOP_POINTS = {}

const _bufCache = new Map()   // slug -> Promise<AudioBuffer>
let masterBgmGain = null      // all BGM voices route through here (= volume)
let curVoice = null           // { slug, source, gain }
let curScene = null
let lastPlayed = {}           // scene -> last slug (avoid immediate repeat)
let takeoverActive = false
let pendingScene = null       // scene to resume after a takeover ends
let sceneGen = 0              // bumped every switch; stale async starts self-cancel

function _ensureGraph() {
  if (!audioCtx) return false
  if (!masterBgmGain) {
    masterBgmGain = audioCtx.createGain()
    masterBgmGain.gain.value = _bedVol()
    masterBgmGain.connect(audioCtx.destination)
  }
  return true
}

function _loadBuffer(slug) {
  if (_bufCache.has(slug)) return _bufCache.get(slug)
  const p = fetch(`${AUDIO_BASE}${slug}.ogg`)
    .then(r => { if (!r.ok) throw new Error(`missing ${slug}.ogg`); return r.arrayBuffer() })
    .then(ab => audioCtx.decodeAudioData(ab))
    .catch(e => { _bufCache.delete(slug); console.warn('[bgm] load failed', slug, e.message); throw e })
  _bufCache.set(slug, p)
  return p
}

function _pick(scene) {
  const pool = SCENES[scene]
  if (!pool || !pool.length) return null
  if (pool.length === 1) return pool[0]
  let choice = pool[Math.floor(Math.random() * pool.length)]
  if (choice === lastPlayed[scene]) choice = pool[(pool.indexOf(choice) + 1) % pool.length]
  lastPlayed[scene] = choice
  return choice
}

function _startVoice(slug, { loop = true, fadeIn = 0.8 } = {}) {
  return _loadBuffer(slug).then(buf => {
    if (audioCtx.state === 'suspended') audioCtx.resume()
    const source = audioCtx.createBufferSource()
    source.buffer = buf
    source.loop = loop
    const lp = LOOP_POINTS[slug]
    if (loop && lp) { source.loopStart = lp[0]; source.loopEnd = lp[1] }
    const gain = audioCtx.createGain()
    const now = audioCtx.currentTime
    gain.gain.setValueAtTime(0.0001, now)
    gain.gain.exponentialRampToValueAtTime(1, now + fadeIn)
    source.connect(gain); gain.connect(masterBgmGain)
    source.start(now)
    return { slug, source, gain }
  }).catch(() => null)
}

function _fadeOutVoice(voice, dur = 0.8) {
  if (!voice) return
  try {
    const now = audioCtx.currentTime
    voice.gain.gain.cancelScheduledValues(now)
    voice.gain.gain.setValueAtTime(Math.max(0.0001, voice.gain.gain.value), now)
    voice.gain.gain.exponentialRampToValueAtTime(0.0001, now + dur)
    voice.source.stop(now + dur + 0.05)
  } catch {}
}

// Public: route the BGM to a scene. Same-scene calls are ignored (this is what
// makes combat music continuous across floors). Called by screens.
export function setBgmScene(scene) {
  if (!SCENES[scene]) return
  if (takeoverActive) { pendingScene = scene; return }
  if (scene === curScene && curVoice) return
  curScene = scene
  if (!soundEnabled) return
  if (!_ensureGraph()) return
  const slug = _pick(scene)
  if (!slug) return
  // Generation guard: a track load is async, so rapid scene switches can have
  // several starts in flight. Stamp this switch; when a start resolves, adopt
  // it only if it's still the latest — otherwise stop it so nothing stacks.
  const gen = ++sceneGen
  _fadeOutVoice(curVoice, 1.0)
  curVoice = null
  _startVoice(slug).then(v => {
    if (!v) return
    if (gen !== sceneGen) { try { v.source.stop() } catch {} return }
    curVoice = v
  })
}

// Full-track takeover for the biggest moments (6★ pull, 7★ ascension): ducks
// and stops BGM, plays the whole track once, keeps playing even if the player
// navigates away, then restores the scene BGM. One per event.
export function playTakeover(slug) {
  if (!soundEnabled || !_ensureGraph() || takeoverActive) return
  takeoverActive = true
  pendingScene = curScene
  _fadeOutVoice(curVoice, 0.4); curVoice = null
  _loadBuffer(slug).then(buf => {
    if (audioCtx.state === 'suspended') audioCtx.resume()
    const source = audioCtx.createBufferSource()
    source.buffer = buf
    const gain = audioCtx.createGain()
    gain.gain.value = 1
    source.connect(gain); gain.connect(masterBgmGain)
    source.onended = () => {
      takeoverActive = false
      const resume = pendingScene; curScene = null
      if (resume) setBgmScene(resume)
    }
    source.start()
  }).catch(() => { takeoverActive = false })
}

// One-shot MUSIC stinger (victory/defeat) that ducks the BGM under it.
export function playMusicStinger(slug, { duckTo = 0.3, duckMs = 250 } = {}) {
  if (!soundEnabled || !_ensureGraph()) return
  _loadBuffer(slug).then(buf => {
    if (audioCtx.state === 'suspended') audioCtx.resume()
    const now = audioCtx.currentTime
    // duck the bed
    masterBgmGain.gain.cancelScheduledValues(now)
    masterBgmGain.gain.setValueAtTime(masterBgmGain.gain.value, now)
    masterBgmGain.gain.linearRampToValueAtTime(_bedVol() * duckTo, now + duckMs / 1000)
    const source = audioCtx.createBufferSource()
    source.buffer = buf
    const gain = audioCtx.createGain()
    gain.gain.value = globalBgmVolume
    source.connect(gain); gain.connect(audioCtx.destination)
    source.onended = () => {
      const t = audioCtx.currentTime
      masterBgmGain.gain.cancelScheduledValues(t)
      masterBgmGain.gain.setValueAtTime(masterBgmGain.gain.value, t)
      masterBgmGain.gain.linearRampToValueAtTime(_bedVol(), t + 0.6)
    }
    source.start()
  }).catch(() => {})
}

function stopBgm() {
  _fadeOutVoice(curVoice, 0.3)
  curVoice = null
}

// Resume/assert the current scene (used by sound-enable + autoplay-resume).
function playBgm() {
  if (!soundEnabled || takeoverActive) return
  if (!_ensureGraph()) return
  const scene = curScene || 'title'
  curScene = null           // force setBgmScene to (re)start it
  setBgmScene(scene)
}
