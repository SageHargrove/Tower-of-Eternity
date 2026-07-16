# Tower of Eternity — Sound Design Plan

Music: **Suno**. SFX + voice barks: **ElevenLabs** (its music is weak, but its SFX/voice generation is genuinely good — clean division of labor).

---

## 1. The style anchor

**Not straight JRPG.** Bright Uematsu-style synth-orchestra JRPG music would fight the illuminated-manuscript / gold-leaf / gothic-sacred art everywhere in the game (Athenaeum, Reliquary, Shrine, Death Ceremony...). What we want is:

> **Sacred dark-fantasy orchestral with early-music instrumentation, and JRPG melodic sensibility.**

Steal from JRPGs the thing they do best — clear, hummable motifs per screen — but voice it with medieval/sacred instruments. Reference points: Octopath Traveler's quieter tracks, Elden Ring menu themes, Pentiment, old Fable.

### House instrument palette (reuse in every prompt)
- harp, lute, wordless choir, church bells, low strings, solo cello
- ceremonial drums / frame drum for rhythm, organ reserved for boss & death
- hurdy-gurdy / fiddle only for tavern, expeditions, low-floor combat (the "folk" corner)

### House prompt prefix — start EVERY Suno style prompt with this:

```
dark fantasy orchestral, medieval sacred atmosphere, cathedral reverb, cinematic, instrumental, no lyrics,
```

### Consistency tricks
1. **Suno Personas**: take the existing track you like most (probably tavern or boss), create a Persona from it, and generate the rest of the soundtrack under that Persona. This is the single strongest consistency lever Suno has.
2. Keep one key family: ask for **D minor / D dorian** on most tracks. Shared tonality makes screen transitions feel intentional.
3. Tempo bands: menus 60–85 BPM, exploration 95–110, combat 120–140, boss 140–160.
4. Menus loop for hours — generate them **understated** ("background music that never tires"), not epic. Epic hub music is the #1 mistake.
5. Loudness-normalize everything to the same level after download (ffmpeg `loudnorm`, ≈ −16 LUFS for loops, stingers ~3 dB hotter).

---

## 2. Track list + Suno prompts

Prepend the house prefix to each. Generate 1:30–2:30 for loops (shorter loop = smaller file, and nobody notices under 2 min if the track is understated).

### Tier 1 — must-have (existing ✓ marked)

| # | Track | Status |
|---|-------|--------|
| 1 | Title / Login | needed |
| 2 | Base hub (most-heard track in the game) | needed |
| 3 | Tavern | ✓ have |
| 4 | Summon Altar (remake) | redo |
| 5 | Synthesis Chamber | needed |
| 6 | Combat — standard | ✓ have |
| 7 | Boss | ✓ have |
| 8 | Victory stinger | needed |
| 9 | Defeat stinger | needed |
| 10 | 5★ reveal stinger | needed |

**1. Title / Login**
```
solemn and awe-inspiring, slow build from a single low drone, harp arpeggios, distant wordless choir swelling, church bells, a lone female vocalise carrying the main theme, 70 BPM, D minor, mysterious but inviting, like standing at the foot of an infinite tower
```

**2. Base hub**
```
warm and understated, gentle lute and harp interplay, soft string pads, occasional small bells, unhurried 80 BPM, D dorian, hopeful medieval court ambience, background music that never tires, calm homecoming feeling
```

**4. Summon Altar (remake — see §3 for why the old one didn't work)**
```
ritual anticipation, deep ceremonial drums, low sustained drone, fragments of gregorian chant, rising tension that never fully resolves, sparse melody, dark and sacred, 90 BPM, D minor, the moment before something answers the call
```

**5. Synthesis Chamber**
```
reverent and transformative, glassy harmonics, harp glissandi, slow choir swells that bloom and recede, sense of sacred alchemy, 65 BPM, D major borrowed warmth over D minor, quiet miracle
```

**8. Victory stinger** (see §4 — generate 30s, keep the opening fanfare)
```
short triumphant medieval fanfare, bright brass, pealing bells, one big wordless choir hit, resolves cleanly and completely within the first ten seconds, D major
```

**9. Defeat stinger**
```
somber descending string phrase, single tolling church bell, breath of choir fading to silence, grief without despair, ends unresolved, D minor
```

**10. 5★ reveal stinger**
```
massive sacred choir hit with cathedral bell bloom and harp cascade, radiant, five seconds of pure arrival, golden light in sound form
```

### Tier 2 — strong wants

**11. Athenaeum / research**
```
quiet candlelit study, music box and harp, very sparse, soft choir pad underneath, contemplative and scholarly, 60 BPM, ink and parchment, patience
```

**12. Combat variant — mid-tower (ashen bands)**
```
urgent medieval battle, driving low strings ostinato, war drums, low brass swells, male chant accents, 130 BPM, D minor, relentless ascent
```

**13. Combat variant — high-tower (celestial/abyssal bands)**
```
dreadful and majestic battle, full choir, pipe organ stabs, tremolo strings, cavernous percussion, 140 BPM, the tower itself is watching, sacred terror
```

**14. Elite / miniboss**
```
aggressive sacred battle, string ostinato, pounding war drums, chanting male choir, brass stabs, 145 BPM, D minor, a wall that must be broken
```

**15. Arena / PvP / tournaments**
```
martial tournament energy, crisp snare drums, heraldic brass fanfares, galloping string rhythm, competitive and bright but still medieval, 130 BPM, banners in the wind
```

**16. Expeditions / world map**
```
wandering folk adventure, fiddle and frame drum, wooden recorder melody, open road under a wide sky, 100 BPM, D dorian, optimistic momentum
```

**17. Memorial / Death Ceremony**
```
requiem, solo boy soprano vocalise, quiet pipe organ, slow single bells, long silences between phrases, grief and honor, 50 BPM, D minor, a name carved in stone
```

**18. Herald / seasonal (Emberfall example)**
```
smoldering festival, low strings, crackling hand percussion, minor-key warmth, embers rising into a night sky, 85 BPM, ceremonial but ominous
```

### Reuse map (don't make more tracks than this)
- Forge / Market / Facilities / Farm → **Base hub** track
- Guild Hall → **Tavern**; Guild War → **Elite/miniboss**
- All 10 tower zones → 3 combat tracks by climb tier (low = existing combat, mid = #12, high = #13). Per-zone unique music is a v2 luxury.
- Chat drawer, modals, codex → whatever screen is behind them (no switch)

---

## 3. Why the summon music probably feels wrong

A summon screen isn't a *song* moment — it's a **bed + payoff** moment. If you generated a melodic track, it competes with the reveal. The fix is structural, not a better melody:

1. Altar screen plays the **ritual bed** (#4) — drone + drums, tension, no melodic resolution.
2. The card-flip/reveal moment cuts the bed and fires a **rarity stinger** (#10 for 5★, a smaller shimmer for 4★, near-silence + soft chime for 3★). The music resolving *is* the reward. This mirrors every big gacha (Genshin/FGO do exactly this).

---

## 4. Looping — the practical recipe

Suno will not give you a perfect loop; you make one in post:

1. Generate ~2 min, instrumental.
2. In Audacity (or ffmpeg): find two points where the music is on the same chord/bar boundary, cut there, and **crossfade the tail into the head** (200–500 ms). Export.
3. **Do not rely on MP3 + `loop=true`** — MP3 encoding pads silence at the start/end, so [audio.js](frontend/src/audio.js) `bgmAudio.loop = true` will always click/gap. Two fixes:
   - Encode loops as **OGG Vorbis** (gapless-capable, smaller files), and/or
   - Better: play BGM through the **Web Audio API** (`decodeAudioData` → `AudioBufferSourceNode` with `loop`, `loopStart`, `loopEnd`) — sample-accurate gapless, and we already have an `AudioContext`. Also enables the intro-then-loop pattern (play intro once, loop the body) which makes tracks feel far less repetitive.
4. Stingers (victory/defeat/reveal): trim tight, no loop, export as-is.

### Suno stinger tip
Suno is bad at "make me 6 seconds." Generate a 30s piece whose *opening* is the fanfare, then trim to the first phrase.

## 5. Engine work needed (I can build all of this)

- **BGM manager** in `audio.js`: per-screen track routing, 1s crossfades between screens, gapless Web Audio looping, preload/caching, duck BGM −8 dB under stingers and VO. Files live in `frontend/public/audio/bgm/` and `.../stingers/`.
- **ffmpeg prep script**: batch loudness-normalize + convert everything Suno exports.

## 6. SFX verdict

**Keep the synth kit as the base layer** — it was built swap-ready and covers clicks/hits fine. Upgrade only the ~10 hero moments with real samples (ElevenLabs SFX gen, or Sonniss GDC free packs):

card flip, 5★/4★ reveal whoosh, crit hit, chest/reward open, currency gain, evolution/capstone, quest complete, banner pull button, error/denied thunk, chat pop.

## 7. Voice acting verdict

- **Announcer barks: YES.** Cheapest audio-to-hype ratio in the genre. One voice — a deep, solemn herald/monk narrator (ElevenLabs) — and ~10 lines, reused forever: "Victory." "Defeat." "The Tower acknowledges your ascent." (floor milestones) "A legend answers the call." (5★) "Your legend grows." (evolution). Same voice everywhere = brand.
- **Fairy full VA: NO.** Every future dialogue line would need matching VO, and mismatched/partial VO reads cheaper than none. Middle ground that works great: 3–5 **wordless vocal chirps** (curious hm?, excited!, giggle, gasp) + text-blip sounds, Animal Crossing / Banjo style. Charm without the treadmill.
- **Per-hero summon voices: hard no** for ~90 heroes. v3 dream.

## 8. Order of operations

1. Remake summon as ritual bed + build the 3 reveal stingers
2. Title, Base hub, Victory/Defeat stingers
3. BGM manager + Web Audio gapless looping (engine)
4. Synthesis, Athenaeum, Memorial
5. Combat variants, Arena, Expeditions, Herald
6. Announcer VO pass + hero-moment SFX swap
