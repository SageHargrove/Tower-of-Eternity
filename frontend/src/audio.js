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
  if (bgmAudio) {
    bgmAudio.volume = globalBgmVolume
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
    
    // Ensure it resumes on any user interaction
    const resumeAudio = () => {
      if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume()
      }
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

let bgmAudio = null

function stopBgm() {
  if (bgmAudio) {
    bgmAudio.pause()
    bgmAudio = null
  }
}

function playBgm() {
  if (!soundEnabled) return
  stopBgm() // Stop existing
  
  bgmAudio = new Audio('/bgm.mp3')
  bgmAudio.loop = true
  bgmAudio.volume = globalBgmVolume
  bgmAudio.play().catch(e => console.error("BGM blocked by browser", e))
}
