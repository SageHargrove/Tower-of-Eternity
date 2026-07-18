# Tower of Eternity — Sound Design Plan (v2 — Sacred-Jazz Fusion)

Music: **Suno Pro** (v5.5). SFX: keep synth kit, upgrade hero moments later (ElevenLabs free tier if ever needed). VO: deferred indefinitely — stingers carry the payoffs.

---

## 1. The style anchor — SACRED-JAZZ FUSION (locked 2026-07-16)

Winner of the theme bake-off: **acid-jazz fusion with gothic orchestral flourishes** — funky bass and jazzy keys (the Atlus cool) under cathedral choir and bells (the illuminated art). One reference song is the DNA source: the winning combat roll ("the chorus one").

### House prompt prefix — start every prompt with:

```
Instrumental, acid-jazz fusion with gothic orchestral flourishes,
```

### The tone dial (COMMITTED 2026-07-17 after alternatives review — no more direction second-guessing)
Every track sets one dial: funk ↔ sacred. The groove is the gacha's seduction; the choir is what it costs.
- **Funk-forward**: Arena, Tavern, Expeditions, Herald
- **Balanced**: Combat, Boss, Elite, Hub, Tower Ascent, Title, Athenaeum
- **Sacred-only (no groove)**: Synthesis, Memorial, Summon ritual bed, reveal stingers, Ascension ceremony
Tonal misfits are fixed by sliding THAT track's dial darker, never by re-litigating the direction.

### House palette
- Rhythm: funky/slap bassline, tight punchy drums (brushes when quiet)
- Color: jazzy electric piano (Rhodes), brass hits, vibraphone for quiet screens
- Sacred layer: cathedral choir swells, church bells, organ (bosses only), harp
- Tempo bands: menus 60–85, exploration 95–110, combat 155–165, boss 170+

### Consistency stack (in order of strength)
1. **Cover** the winning combat roll for anything that should share its melody (boss, title) — leitmotif.
2. **+ Inspo** with the winner attached for new-melody tracks in the same family.
3. **Saved Style** — save the winner's expanded style text (right panel → Styles) and reuse it.
4. House prefix + palette words in every prompt.

### Post-production (later, in Suno Studio + Audacity/ffmpeg)
- Crop chorus → victory stinger raw material; Get Stems → drums-less low-intensity variants.
- Loop-cut at bar boundaries, crossfade tail→head.
- Engine: Web Audio gapless looping (MP3 + `loop=true` always gaps), per-screen routing, crossfades, ducking. Files → `frontend/public/audio/bgm/`, `.../stingers/`.
- Loudness-normalize: −16 LUFS loops, stingers ~3 dB hotter.

---

## 2. Track list + prompts (all get the house prefix)

### Combat family — via COVER of the winning roll (shared melody)

**Combat — standard**: the winning roll itself (loop-cut it).

**Boss** (Cover, style text:)
```
epic desperate boss battle, aggressive slap bassline, thunderous double-time drums, full cathedral choir, pipe organ stabs, urgent brass, the main melody returning bigger and darker each time, overwhelming and climactic, 172 BPM, no vocals
```

**Elite / miniboss** (Cover:)
```
aggressive relentless battle, driving slap bass, pounding drums, choir accents, brass stabs, tense and unyielding, the main melody fragmented and urgent, 165 BPM, no vocals
```

**Title screen** (Cover — the foreshadow trick:)
```
slow mysterious noir arrangement, brushed drums, upright bass, sparse glassy electric piano carrying the main melody gently, distant cathedral choir, church bells, smoky and inviting, awe at the foot of an infinite tower, 75 BPM, no vocals
```

### New-melody tracks — via + INSPO with the winner attached

**Base hub — ROTATION SET of 3** (most-heard screen; the BGM manager shuffles per-screen playlists, no back-to-back repeats. Rotation policy: Hub ×3 at launch, Tavern ×2 later, everything else ×1 — expand by exposure in live-service patches.)

*Hub A — warm noble groove:*
```
warm noble home theme, gentle memorable melody on harp and Rhodes electric piano trading phrases, soft bassline, brushed drums, church bells in the distance, quiet choir pad, hopeful and safe after a long climb, understated, background music that never tires, 80 BPM, no vocals
```
*Hub B — atmospheric sanctuary:*
```
serene majestic home theme, slow harp arpeggios, warm string pads, distant cathedral choir, occasional soft piano melody, church bells marking time, sanctuary within ancient stone walls, peaceful gravity, 70 BPM, no vocals
```
*Hub C — evening hearth (warmth with people in it):*
```
gentle homecoming theme, soft Rhodes and harp carrying a tender melody, warm upright bass, light brushed groove, distant bells and low choir pad, the stronghold at evening with fires lit and heroes resting, quiet life and comfort, 75 BPM, no vocals
```

**Tavern** (have one — regen under Pro in-theme if the old one clashes)
```
lively jazz lounge, walking upright bass, playful piano trio, brushed swing drums, warm brass, rowdy but cozy medieval tavern after a long climb, 110 BPM, no vocals
```

**Summon Altar** (ritual bed — tension, no resolution; reveal stingers do the payoff)
```
dark ambient jazz ritual, low sustained drone, sparse ominous piano voicings, deep ceremonial drums, choir fragments rising and receding, tension that never resolves, the moment before something answers, 90 BPM, no vocals
```

**Synthesis Chamber** (hero sacrifice — ominous ritual dread, NOT a happy miracle; distinct from Memorial: Memorial = grief after, Synthesis = dread during)
```
dark sacrificial ritual, low ominous drone, slow tolling bell, deep male choir chanting underneath, sparse dissonant piano notes, heartbeat-like muffled drum pulse, dread and solemn gravity, a price being paid, tension that never resolves, 55 BPM, no vocals
```

**Athenaeum / research**
```
quiet late-night jazz study, soft piano, vibraphone, upright bass, brushed drums barely there, faint choir pad, candlelit and scholarly, patient, 60 BPM, no vocals
```

**Expeditions / world map**
```
adventurous mid-tempo jazz fusion, traveling groove, warm bassline, bright electric piano, hopeful brass melody, open road under a wide sky, 105 BPM, no vocals
```

**Arena / PvP / tournaments** (v2 — less big-band show, more gladiator)
```
hard-hitting competitive battle groove, gritty slap bass, driving aggressive drums, dark brass riffs, two dueling lead melodies trading bars like opponents, choir surges on the impacts, fierce and confident, a coliseum under cathedral banners, 145 BPM, no vocals
```

**Memorial / Death Ceremony** (v2 — Suno loves resolving to a major "happy" cadence; forbid it. If a roll is perfect except the ending, just trim the last bars in post instead of discarding.)
```
mournful slow elegy, solo piano, upright bass, distant wordless choir, single tolling church bell, long silences between phrases, grief and honor, stays in minor key throughout, ends unresolved on a suspended fading chord, no triumphant resolution, 50 BPM, no vocals
```

**Tower Ascent (floor select / pre-climb)**
```
tense simmering jazz groove, pulsing bassline, ticking hi-hats, sparse electric piano stabs, low choir pad building anticipation, church bell accents, gathering resolve before the climb, restrained energy that never fully releases, 100 BPM, no vocals
```

**Herald / seasonal (Emberfall)**
```
smoldering minor-key jazz groove, low brass, crackling hand percussion, embers rising into a night sky, ceremonial but ominous, 85 BPM, no vocals
```

### Stingers (non-looping; trim tight)

**Victory** — COVER of the winning combat track (so the jingle bursts with the combat melody — FF-style), style text:
```
short triumphant victory fanfare, brass and bells over a funky bass run, one big choir hit, celebratory, resolves cleanly within ten seconds, no vocals
```
Fallback if covers come out weird at short form: plain generation with the same prompt. All OTHER stingers (Defeat, reveals, evo stings, Ascension) = plain generations, NO Inspo — the choir/bell language carries the consistency, and a funk battle reference would drag them toward groove.

**Defeat**
```
somber descending piano phrase, single tolling church bell, breath of choir fading to silence, ends unresolved, no vocals
```

**Rarity reveals — 3 musical tiers, shared by hero AND equipment banners** (the sound signals rarity, not item type; 1–3★ are SFX-kit territory, no music):

**4★ reveal**
```
short bright shimmer, small bell cascade and brief choir swell, pleasant arrival, three seconds, no vocals
```

**5★ reveal**
```
big sacred choir hit with cathedral bell bloom, harp cascade over one deep bass note, radiant arrival, five seconds of golden light, no vocals
```

**6★ reveal** (top summonable rarity — the jackpot; pair with a rising pre-reveal tell before the flip)
```
rising anticipation swell into a massive cathedral choir and organ hit, deep bells blooming, harp glissando raining down, overwhelming golden radiance, the rarest arrival, no vocals
```

**Evolution stings** — evolutions NEVER play summon reveal stingers (summon sounds = luck, evolution sounds = earned progress; keep the associations pure). Tiered by target star:

*Standard (evolving to 2★–5★):*
```
radiant ascending choir swell, quick harp run, warm bells, triumphant short bloom, eight seconds, no vocals
```

*Grand (evolving to 6★)* — same musical phrase, bigger arrangement:
```
radiant ascending choir swell blooming into full cathedral choir, harp cascade, deep resonant bells, triumphant and majestic, ten seconds, no vocals
```

*7★ = the Ascension ceremony below (evolution-exclusive by design).*

**7★ Ascension ceremony** (evolution-exclusive peak — a 20–30s set piece, not a sting; the sacred layer at absolute maximum)
```
sacred ascension ceremony, solo choir voice over deep organ, cathedral bells tolling in celebration, full choir building wave on wave, funky bassline and jazz drums entering halfway like the world resuming, radiant climax, transcendence, no vocals
```

### Reuse map
- Forge / Market / Facilities / Farm → Base hub
- Guild Hall → Tavern; Guild War → Elite
- 10 tower zones → standard combat (low bands) / elite (mid) / boss-adjacent tension (top) — per-zone music is v2
- Chat drawer / modals / codex → no music switch

---

## 2.5 Adaptive combat music (fights are shorter than songs — solved)

1. **Session-persistent BGM**: combat track runs continuously across consecutive floors in a zone; resets only on leaving the tower. (Hades / Slay the Spire model — fits chained-floor climbing perfectly.)
2. **Layered intensity**: Get Stems on the combat track → drums-less mix plays on Tower Ascent / between fights, full mix crossfades in when combat starts — same timeline, so the drums just "kick in" with the fight. Two synced Web Audio buffers + gain crossfade.
3. **Boss phase → chorus jump**: on phase transition, seek the boss track to its chorus timestamp (mark once in Audacity). Roadmap already has boss phases; this makes the music feel composed per-fight.
4. **Jukebox** in Tavern/Hearth ("the bard's repertoire"): unlocked tracks play in full; unlocks tied to progression (clear zone → zone track; first 7★ → Ascension ceremony). OST as collectible content.
5. **Loop-cut placement**: combat loops start near the hook, not the intro — the first 30s are the only guaranteed listen. Slow intros are for linger-screens only.

## 3. Order of operations

1. Lock the winner: favorite it, save its Style, Get Stems, Crop the chorus
2. Cover chain: Boss → Title → Elite
3. Inspo chain: Hub → Summon bed + reveal stingers → Victory/Defeat
4. Engine: Web Audio BGM manager (gapless loops, per-screen routing, crossfade, ducking)
5. Remaining Inspo tracks: Synthesis, Athenaeum, Tavern regen, Arena, Expeditions, Memorial, Herald
6. Video-ad music: COVER the winner. Two options (judge rolls by the final 15s — the ending must slam shut, not noodle):

   *Instrumental:*
   ```
   epic cinematic trailer arrangement, starts sparse and mysterious with solo piano and distant choir, builds with rising drums and slap bass, explodes into full cathedral choir and brass carrying the main melody, dramatic pause before the final hit, huge clean ending, no fade out, no vocals
   ```

   *Vocal (Atlus-style anthem — uncheck Instrumental; optionally add "lyrics about climbing an endless tower, defying fate"):*
   ```
   epic stylish trailer anthem, confident female vocalist singing a short soaring hook over the main melody, funky slap bass, driving drums, cathedral choir answering the vocal line, church bells, builds to a massive final chorus with a clean powerful ending, no fade out, minimal lyrics, anthemic
   ```

## 4. Odds and ends

- **Suno Studio**: use at post phase for loop-cutting/stem work, not for generation.
- **Voices (née Personas)**: vocal-identity tool — irrelevant for instrumental OST. Ignored.
- **Licensing**: everything shipping must be generated while subscribed (Pro). Old f2p favorites can seed Covers/Inspo but can't ship themselves.
- **Logo**: SVG illuminated wordmark (drop-cap initial, gold leaf) + optional SD-generated emblem. Suno cover-art gen: not for this.
- **Publishing the OST**: never naked, always wearing the game. No Suno publishing (wrong audience), no pre-launch Spotify album (no discovery value + AI-music platform/backlash friction). DO: trailer, short-form gameplay clips with the boss chorus, teaser tracks in Discord pre-playtest, free OST playlist on the game's YouTube channel at launch.
