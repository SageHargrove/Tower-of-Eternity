// Encodes the WAV masters in ../../audio_masters into loudness-normalized OGG
// Vorbis files in ../public/audio, ready for the in-game Web Audio BGM manager.
// Run: node scripts/encode_audio.mjs
import { execFileSync } from 'node:child_process'
import { readdirSync, mkdirSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import ffmpegPath from 'ffmpeg-static'

const here = dirname(fileURLToPath(import.meta.url))
const MASTERS = join(here, '..', '..', 'audio_masters')
const OUT = join(here, '..', 'public', 'audio')
if (!existsSync(OUT)) mkdirSync(OUT, { recursive: true })

// Hotter targets for one-shots that need to punch over ducked BGM.
const HOT = new Set(['victory', 'defeat', '6_star_pull', 'ascension'])

const slug = (name) =>
  name.replace(/\.wav$/i, '').replace(/^OST\s*-\s*/i, '').trim().toLowerCase()
      .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')

const files = readdirSync(MASTERS).filter(f => /\.wav$/i.test(f))
const manifest = []
for (const f of files) {
  const s = slug(f)
  const I = HOT.has(s) ? '-14' : '-16'
  const out = join(OUT, `${s}.ogg`)
  process.stdout.write(`encoding ${f} -> ${s}.ogg (I=${I}) ... `)
  try {
    execFileSync(ffmpegPath, [
      '-y', '-i', join(MASTERS, f),
      '-af', `loudnorm=I=${I}:TP=-1.5:LRA=11`,
      '-c:a', 'libvorbis', '-q:a', '5', '-ar', '44100',
      out,
    ], { stdio: ['ignore', 'ignore', 'ignore'] })
    manifest.push(s)
    console.log('ok')
  } catch (e) {
    console.log('FAILED')
    console.error(e.message)
  }
}
console.log(`\nDone: ${manifest.length}/${files.length} encoded to public/audio/`)
console.log(manifest.sort().join(', '))
