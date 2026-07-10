"""
Portrait Cache System
======================
Pre-generates hero portraits in the background (with race/hair/outfit/gender/class
variety baked in) so pulls feel instant, and generates hero-specific portraits from
LLM prompts when the cache is empty or a fallback profile was used.

House art style: dark fantasy anime, Solo Leveling manhwa aesthetic — moody rim
lighting, saturated colors, sharp lineart, tight face-focused framing.
"""

import threading
import queue as pqueue
import itertools
import random
import os
import re
import time
import database
from database import db

CACHE_TARGET = 20
MIN_PER_STAR = {1: 8, 2: 6, 3: 4, 4: 3, 5: 2, 6: 2, 7: 2}
# Hard ceiling per star — a last line of intelligence so a stray duplicate worker
# (e.g. two backend processes running at once) can't silently overfill the
# pool forever instead of just stopping at quota. min+1 rather than min*2 —
# doubling made sense for cheap common tiers but meant pre-generating twice
# as many of the expensive, rarely-pulled 7-star portraits as intended.
MAX_PER_STAR = {star: minimum + 1 for star, minimum in MIN_PER_STAR.items()}

CACHE_DIR = "static/portraits/cached"

# ---------------------------------------------------------------------------
# Shared generation queue — single worker, strict priority order. Hero-specific
# jobs (a player is looking at a blank portrait right now) always jump ahead
# of routine cache-pool refilling, since ComfyUI processes one job at a time
# on the GPU regardless of which Python thread submitted it.
# ---------------------------------------------------------------------------

PRIORITY_URGENT = 0   # hero waiting on a portrait (new pull, regenerate, upgrade)
PRIORITY_ENEMY = 5     # finite, one-time enemy/boss library fill — below an actual
                        # waiting hero, but above routine refill so it isn't endlessly
                        # crowded out every time the buffer pool needs topping up
PRIORITY_ROUTINE = 10  # background cache-pool top-up (no specific hero is waiting on this)

_job_queue = pqueue.PriorityQueue()
_job_seq = itertools.count()

def _enqueue(priority: int, fn, *args):
    _job_queue.put((priority, next(_job_seq), fn, args))

# ---------------------------------------------------------------------------
# House style — do not strip these tags, this is the look the game is built on
# ---------------------------------------------------------------------------

BASE_STYLE = (
    # style anchor at 1.3. POSITIVE-side weights only — weighted NEGATIVE
    # additions are what caused the r9 drift. Fading-into-bg is now handled by
    # the LIGHTING FIX block below (front key light) rather than by cranking
    # rim light, which only lit edges and left the front of the figure dark.
    "(Solo Leveling manhwa art style:1.3), dark fantasy anime, "
    # ink/lineart weights raised: the dominant volume-run reject is a glossy
    # 3D-CG drift whose defining absence is LINEART
    "(bold black ink outlines:1.25), (thick clean lineart:1.15), (cel shading:1.1), hard shadow edges, "
    "highly detailed facial shading, multiple distinct shading tones, colored midtones in shadow, "
    "detailed hair strands, textured hair shading, "
    "rich saturated colors, vivid true-to-color hair, natural skin tone unaffected by lighting, "
    # Danbooru-native background/lighting tags — NoobAI reads these far more
    # reliably than the old prose ("plain simple dark background..."), which
    # also fought the anti-flat-background negatives and compromised on gray.
    # A/B verified 2026-07-06 (fixed seed): true black gradient, richer gold
    # trim, truer costume colors.
    "simple background, dark background, (black background:1.1), gradient background, "
    # LIGHTING FIX (2026-07-08, A/B verified on Real_ToE ep10): the manhwa LoRA
    # is already dark-leaning, and backlighting/chiaroscuro/dramatic-shadow were
    # silhouetting the subject (lower bodies faded to pure black). Swapped those
    # three for a front key light + illumination tags, dropped black-bg 1.2->1.1
    # and rim 1.25->1.1. Full bodies now survive; void background preserved.
    "(rim lighting:1.1), (character fully illuminated:1.25), bright key light on the figure, "
    "front lighting, full body clearly visible, well-lit character, crisp visible details, high contrast, "
    # very awa / absurdres are NoobAI's own top-quality training tags — they
    # pull toward the highest-scored slice of its dataset.
    "intricate details, masterpiece, best quality, very awa, absurdres, newest, same universe aesthetic"
)

# Full-body, fixed framing. A single full-body asset is stored per hero and
# cropped two ways in the UI (card = head/chest via object-position:top; the
# expanded/leader view = the whole figure), so this framing must reliably
# put the WHOLE character in frame — head through feet — on a plain backdrop
# that composites/blends cleanly. The old "head and shoulders, close up"
# framing is exactly what produced bust shots with no legs.
FRAMING = (
    "(full body:1.35), (full-length character illustration:1.3), head to feet fully visible, "
    "entire body inside the frame, feet near the bottom edge of the frame, "
    "character centered horizontally, (the character fills most of the frame height:1.1), "
    "fully clothed, wearing a detailed outfit, plain empty background"
)

# Pose/camera variety — the old FRAMING hard-coded "standing heroic pose",
# which produced the same stiff mannequin stance on every hero. One of these
# is rolled per generation instead; all are full-body-compatible danbooru
# tag combos so the framing contract above still holds.
# GOLDEN SET — the exact 12 poses of the batch the user called perfect.
# The 22-pose expansion + camera angles (r7-r11) caused the progressive
# realism drift: complex compositions (foreshortened lunges, airborne
# leaps, map-crouches, dutch angles) push the model off its cel-shaded
# prior. Do NOT expand this list without A/B evidence.
POSES = [
    "standing, contrapposto, hand on hilt, cape billowing in the wind",
    "walking toward viewer, mid-stride, coat flaring behind",
    "fighting stance, weapon drawn and lowered at the side, blood on blade",
    "action pose, weapon raised, dynamic angle",
    "looking back over shoulder, three-quarter view, wind-swept",
    "kneeling on one knee, sword planted in the ground, head bowed slightly",
    "leaning weight on one leg, arms crossed, confident",
    "casting a spell, one arm extended, magic swirling around hand",
    "crouching low, ready to strike, predatory posture",
    "standing at ease, hand resting on weapon, gaze to the side",
    "mid-turn, cloak swirling, dramatic movement",
    "one hand raised adjusting gauntlet, casual poise",
]

# No camera tokens — the golden batch had none.
CAMERAS = [""]

# Weapon-referencing poses are wrong for non-combat professions (a Farmer
# posing with a raised weapon, r7). Support classes draw from the neutral
# list only.
_WEAPON_WORDS = ("weapon", "sword", "hilt", "sheath", "blade")
POSES_NEUTRAL = [p for p in POSES if not any(w in p for w in _WEAPON_WORDS)]
NONCOMBAT_CLASSES = {"Chef", "Medic", "Scout", "Blacksmith", "Quartermaster",
                     "Tactician", "Priest", "Alchemist", "Merchant", "Farmer", "Classless"}

def _random_pose(hero_class: str = None) -> str:
    pool = POSES_NEUTRAL if hero_class in NONCOMBAT_CLASSES else POSES
    return random.choice(CAMERAS) + random.choice(pool)

# Pushes generation away from the failure modes seen in practice:
# soft painterly/semi-realistic rendering, flat vector-poster coloring,
# crushed-black no-detail faces, loud solid-color backgrounds,
# washed-out/sketch-like underdeveloped renders, and hair glowing so hard
# it loses its actual color (the "everyone has cyan hair" problem).
NEGATIVE_STYLE = (
    # Eye/face integrity — at full-body framing the face is small, so eye
    # defects are the first thing to break; weight these hard.
    "(bad eyes:1.2), (asymmetric eyes:1.2), poorly drawn eyes, cross-eyed, "
    "wonky eyes, misaligned pupils, extra pupils, deformed iris, dead eyes, "
    "(bad face:1.1), poorly drawn face, malformed face, "
    "(text:1.3), (watermark:1.3), signature, artist name, logo, username, speech bubble, letters, "
    # The dominant volume-run reject: glossy 3D-CG render (porcelain skin,
    # chrome specular armor, no lineart). Weighted and early. The old
    # anti-flat weights below are DE-WEIGHTED — they were punishing cel
    # shading and pushing renders toward this glossy compromise.
    "(3d render:1.3), (cgi:1.25), (glossy plastic skin:1.2), porcelain doll skin, "
    "video game cinematic render, unreal engine, octane render, chrome specular highlights, "
    "soft airbrushed shading, painterly, semi-realistic skin texture, photographic, "
    "blurred shading, soft gradient blending, watercolor, flat vector art, solid flat color fill, "
    "face painted in one flat color, skin rendered as a single flat tone, no shadow tones on face, "
    "poster art, low contrast flat colors, muddy shading, "
    "blotchy skin discoloration, harsh shadow patches, uneven skin tone, "
    "completely black face, no facial detail, crushed blacks, underexposed face, silhouette face, "
    "pure white background, neon flat colored background, solid red background, "
    "(bright neon background:1.4), (loud saturated flat background:1.4), (glowing neon yellow background:1.3), "
    "(glowing neon green background:1.3), electric lime background, highlighter-colored background, "
    "(oversaturated:1.2), garish clashing colors, radioactive color palette, "
    "two-tone black and white illustration, ink silhouette art, manga lineart only, "
    "flat poster illustration, no midtone shading, character blending into background color, "
    "overexposed, blown out highlights, washed out, sketch, unfinished sketch, "
    "monochrome, no color saturation, "
    "halftone pattern, screentone dots, dot pattern texture, halftone dots, pixelated dither effect, "
    "newsprint halftone texture, polka dot artifact, "
    "western comic book art style, american superhero comic style, realistic painted comic shading, "
    "glowing hair, hair glowing with light, hair made of light, hair as a light source, flaming hair, "
    "hair color washed out by glow, hair overexposed, hair blown out white, hair losing color to lighting, "
    "halo blending into hair color, (flat solid color hair:1.3), (untextured hair:1.2), single-tone hair mass with no strand detail, "
    "skin tinted blue, unnatural skin discoloration from background lighting, "
    "huge oversized eyes, exaggerated eye proportions, disproportionate giant eyes, "
    "blurry, low quality, watermark, text, signature, (bad anatomy:1.2), "
    "(bad proportions:1.2), malformed limbs, extra limbs, missing limbs, short legs, "
    "long torso, wrong proportions, bad hands, extra fingers, lowres, "
    "deformed, ugly, disfigured, (worst quality:1.2), jpeg artifacts, "
    "hair extending beyond frame edges, hair cropped at image border, hair cut off by frame, "
    "long hair flowing out of frame, hair touching image edge, "
    # Full-body framing enforcement — these bust/crop modes were ~20-30% of
    # generations under the old close-up framing.
    "(cropped:1.4), (close-up:1.4), (bust shot:1.4), (headshot:1.4), (portrait crop:1.3), "
    "(upper body only:1.4), face close up, zoomed in on face, cut off at the waist, "
    "cropped at chest, cropped legs, cut off legs, missing legs, missing feet, "
    "feet out of frame, legs out of frame, out of frame, "
    # h02 failure: character rendered tiny/distant; h06 failure: dark outfit
    # dissolving into the black backdrop (2026-07-06)
    "(tiny distant figure:1.2), (zoomed out:1.2), far away shot, small figure in a large empty frame, "
    # keep these UNWEIGHTED-ish — bumping them to 1.3/1.2/1.2 in r9
    # coincided with a batch-wide realism drift (over-weighted negatives
    # distort style); r7's 1.2/plain/plain was the last good state
    "(body dissolving into darkness:1.2), limbs fading into the background, dark clothing merging with background, "
    "detailed scenery background, busy background, environment background, landscape background, "
    # ground/floor creep — the void should hold only a soft shadow under
    # the feet, never terrain (merchant-on-rubble / berserker-on-white-floor
    # failures, 2026-07-06)
    "(rocky ground:1.2), rubble, stone floor, dirt ground, grass, terrain, "
    "(textured floor:1.2), tiled floor, wooden floor, bright white floor, glowing floor, "
    "glowing orb behind character, glowing circle behind character, halo effect background, "
    "magic circle background, floating colored sphere background, spotlight circle background, "
    "vignette ring, glowing aura sphere, radial light burst background"
)

# ---------------------------------------------------------------------------
# Monster style — separate from BASE_STYLE on purpose. The face-tuned rim-light
# + dark-background recipe above collapses full-body creatures into a flat
# black silhouette with only a single glow effect visible — confirmed by
# inspecting generated output: stone_golem, flame_wraith, and several boss
# archetypes all came back as pure black shapes with one colored light source
# and zero surface detail.
#
# Overcorrecting that ("fully lit", "every part illuminated") created the
# OPPOSITE failure for bright/icy subjects — frost_wight came back almost
# entirely blown-out white-blue with no visible creature shape at all. The
# goal is balanced: visible and detailed, not pitch black, not blown out.
# ---------------------------------------------------------------------------

# "monstrous and beast-like, not a human or attractive humanoid figure" is
# deliberate insurance, not redundant with the negative prompt — hero
# portraits get the same kind of insurance via FRAMING's "fully clothed,
# wearing detailed outfit", which monsters never had an equivalent for.
# Without it, this checkpoint's anime-style bias pulls small/humanoid-ish
# creature prompts (goblin, rat, hyena) toward sexualized "monster girl"
# anime-pinup interpretations instead of actual monsters.
MONSTER_STYLE = (
    # e621 anchor tags first — NoobAI is danbooru+e621 trained, and these
    # three tags are the strongest lever away from the anime-human prior.
    # A/B verified 2026-07-06 (fixed seed, Abyssal Lurker): without them the
    # "twisted abyssal beast" rendered as an anime merman; with them, an
    # actual quadruped creature.
    "no humans, monster, feral, "
    # NOTE: do NOT add e621's "toony"/"digital media (artwork)" style tags —
    # tried 2026-07-06, they made renders WORSE (r5 wolf/spider regressed vs
    # r4). The r4 recipe (this one) is the verified baseline: user kept its
    # wolf and chimera.
    "(Solo Leveling manhwa art style, cel-shaded anime illustration:1.35), dark fantasy anime monster design, "
    "monstrous and beast-like in form, not a human or attractive humanoid figure, fully non-sexual, "
    "(bold black ink outlines:1.25), thick clean lineart, cel shading, multiple distinct shading tones, "
    "well-lit subject with clearly visible surface detail and texture, balanced natural exposure, "
    "rich saturated but balanced colors across the entire body, vivid distinct material colors, "
    "highly detailed surface texture, intricate detailed anatomy, "
    "dark atmospheric background, soft directional lighting on the subject, "
    "dramatic rim lighting accenting edges only — the body itself stays clearly visible and colorful, "
    "neither shadowed into blackness nor blown out into white, "
    "intense contrast in shading without losing surface detail or overexposing, "
    "(well-lit subject:1.2), vibrant color accents, "
    "intricate details, masterpiece, best quality, very awa, absurdres, newest"
)

# Evil-humanoid style — for enemies that are actually person-shaped
# (knights, demons, lich, golem lords, etc.), built from BASE_STYLE's
# anime-portrait recipe (the same one heroes use for their 6-7★ "ornate
# armor, glowing aura, overwhelming presence" escalation) rather than
# MONSTER_STYLE, whose "not a human or attractive humanoid figure" line
# exists specifically to keep actual BEASTS from drifting into "monster
# girl" territory — that insurance would fight against rendering an
# intentionally humanoid villain here. Negative prompt is its own list
# rather than MONSTER_NEGATIVE, which blacklists "human, person, soldier"
# outright (correct for beasts, would sabotage this).
# Kept deliberately minimal — an earlier version baked "intricate ornate
# armor, elaborate accessories, glowing aura, commanding villainous
# presence" directly into this constant, and it overpowered every hint's
# actual creature description: Lizardman/Minotaur/Hobgoblin Berserker all
# came back as generic anime knights with zero scales/horns/tusks visible.
# Style/quality tags only now, same division of labor MONSTER_STYLE already
# uses successfully — the hint carries 100% of what the creature looks
# like, this constant only carries art-style and lighting.
HUMANOID_EVIL_STYLE = (
    "(Solo Leveling manhwa art style, cel-shaded anime illustration:1.3), dark fantasy anime, "
    "(bold black ink outlines:1.2), thick clean lineart, cel shading, "
    "well-lit subject with clearly visible surface detail and texture, balanced natural exposure, "
    "rich saturated but balanced colors across the entire body, vivid distinct material colors, "
    "highly detailed surface texture, full-body or three-quarter pose, "
    "dark atmospheric background, dramatic rim lighting accenting edges only, "
    "intricate details, masterpiece, best quality, very awa, absurdres, newest"
)

HUMANOID_EVIL_NEGATIVE = NEGATIVE_STYLE + (
    ", chibi, kawaii, cute, adorable, cartoon mascot, plush toy, big head small body, "
    "topless, nude, nudity, nsfw, sexualized, sexually suggestive, suggestive pose, seductive pose, "
    "cleavage, exposed breasts, bikini, lingerie, underwear, panties, swimsuit, partial nudity, "
    "monster girl, kemonomimi, pin-up pose, ecchi, fanservice, erotic, provocative, "
    "silhouette, full black silhouette, completely black figure, indiscernible black shape, "
    "heroic noble expression, friendly smile, kind face, good-aligned, holy radiant light"
)

# Which enemy/miniboss/boss names get HUMANOID_EVIL_STYLE instead of
# MONSTER_STYLE — actual person-shaped villains (knights, demons, golems
# built in a humanoid mold, lich, etc.) vs true beasts/monsters.
HUMANOID_ENEMY_NAMES = {
    "Hobgoblin", "Lizardman", "Hobgoblin Berserker", "Lizardman Stalker",
    "Plague Harbinger", "Minotaur", "Minotaur Juggernaut",
    "Stone Sentinel", "Lesser Golem", "Naga", "Death Knight", "Giant",
    "Black Knight Commander", "Demon", "Pit Fiend", "Wraith Sovereign",
    "Lich Acolyte", "Archdemon Enforcer",
    "Orc Warchief", "The Troll King", "Skarn the Lizard Chieftain",
    "The Hobgoblin Warlord", "The Grave Sovereign", "Bullhorn the Minotaur Lord",
    "The Ashen Colossus", "Stoneheart the Unbroken", "The Obsidian Tyrant",
    "The Drowned Naga Queen", "Knight-Captain Mordrek", "Pit Fiend Commander",
    "Goblin King", "Vaelor, the Fallen Ascendant",
    # Harpy/Frost Wight are person-shaped — they render far better through
    # the hero-grade humanoid recipe than MONSTER_STYLE (Liam, 2026-07-06:
    # "for humanoid ones you could pull from the humanoid prompts").
    "Harpy", "Frost Wight",
    "Kobold", "Skeleton", "Feral Ghoul", "Wraith", "Vampire Spawn", "Primordial Vampire",
    "Demon Lord", "Archdemon", "Ancient Guardian",
    "Gorrath the Bonebreaker", "The Rotcaller, Warlord of the Fester Host",
    "Mordane, the Hollow King", "Aetherion, the End of All Things",
}

MONSTER_NEGATIVE = NEGATIVE_STYLE + (
    # e621 tags pull hard toward photoreal wildlife — pin the 2D style with
    # weighted realism negatives (venom stalker/spider came back photoreal
    # without these, 2026-07-06)
    ", (photorealistic:1.3), (realistic:1.25), wildlife photography, taxidermy, "
    "live action, 3d model render, cgi creature, "
    "(murky:1.2), muddy dark rendering, underexposed subject, indistinct dark shapes, "
    "silhouette, full black silhouette, backlit silhouette, "
    "subject rendered as a flat black shape, glowing aura with no body detail visible, "
    "creature reduced to shadow, rim-lit silhouette with no surface detail, "
    "indiscernible black shape, mostly black image, almost entirely black image, "
    "two glowing dots on a black background, body swallowed by darkness, "
    "creature blending completely into the dark background, no visible color on the body, "
    "overexposed, blown out highlights, entirely white image, entirely bright blown-out image, "
    "creature dissolved into pure white or pure colored glow, body shape lost to overexposure, "
    "blinding light obscuring the subject, washed out into a single solid color, "
    "indiscernible bright glowing shape, no visible form due to brightness, glow overwhelming the entire image, "
    "glow filling the entire frame, monochromatic glowing image, image dominated by one single bright color, "
    "no dark contrast areas in the image, background and subject indistinguishable due to uniform brightness, "
    "subject and background the same brightness, flat even glow with no shadow, "
    "human, human figure, person, people, soldier, adventurer, tiny human silhouette, "
    "second character, multiple subjects, a human standing in the scene, "
    "topless, nude, nudity, nsfw, sexualized, sexually suggestive, suggestive pose, seductive pose, "
    "cleavage, exposed breasts, bikini, lingerie, underwear, panties, swimsuit, partial nudity, "
    "see-through clothing, skin-tight revealing clothing, exposed buttocks, "
    "monster girl, kemonomimi, anime girl with animal ears, attractive human woman, beautiful woman, "
    "pin-up pose, ecchi, fanservice, erotic, provocative, a human female body, voluptuous figure, "
    "anthropomorphized into an attractive human, humanoid female version of the creature, "
    "werewolf, lycanthrope, bipedal wolf, anthropomorphic wolf standing upright on two legs, "
    "wolf with human-like proportions, wolf with a humanoid torso, "
    "chibi, kawaii, cute, adorable, cartoon mascot, plush toy, big head small body, "
    "oversized head, large round cute eyes, cuddly, cartoonish proportions"
)

def _quality_tag(birth_star: int) -> str:
    """Render quality is the same at every star — rarity is expressed through
    wardrobe/aura (TIER_FLAVOR), not through a worse drawing. The old 1★ tag
    ("gritty realistic", no "masterpiece") both dropped the quality anchor
    AND pulled against the cel-shaded house style, which is why low-star
    heroes kept coming back flat/muddy while 3★+ looked fine."""
    return "highly detailed face, masterpiece"

# Escalating "epicness" by star rank — explicit rather than incidental, so
# rarity reads as more legendary regardless of which class/race got rolled.
TIER_FLAVOR = {
    # Low stars must be HUMBLE, not PLAIN — "plain worn clothes" kept
    # steering the model toward flat, low-effort renders (confirmed across
    # multiple 1★ batches while 4★+ looked great). The wardrobe stays
    # modest, but every word now demands rendering detail: fabric texture,
    # stitching, layering. Power/rarity still only escalates via
    # gear/effects at higher tiers.
    1: "humble commoner attire rendered in rich detail — layered weathered traveling clothes with "
       "visible fabric texture, stitched patches, frayed hems, worn leather cords, detailed cloth folds "
       "and creases, no armor, no magical effects, ordinary unassuming person",
    2: "novice adventurer outfit rendered in rich detail — sturdy layered travel garb with detailed "
       "stitching and buckles, a worn belt with small pouches, textured cloth and leather, "
       "lightly equipped, no magical effects",
    # "gear" is banned vocabulary — it tokenizes toward mecha (see
    # CLASS_OUTFITS comment; a Thief in "hooded leather gear" rendered in a
    # mech suit). "equipment"/"armor"/"attire" carry the same meaning safely.
    3: "(seasoned fighter:1.1), modest well-maintained equipment with detailed straps and fittings, no special effects",
    4: "(elite warrior:1.15), ornate detailed equipment, confident bearing",
    5: "(legendary hero:1.2), ornate armor and attire, intricate accessories, imposing presence",
    6: "(near-mythic champion:1.25), intricate ornate armor, elaborate jewelry, "
       "glowing magical aura in background, (commanding intimidating presence:1.1)",
    7: "(godlike legendary being:1.3), elaborate ornate armor, intricate magical markings, "
       "glowing weapon or artifact, dramatic glowing aura in background, "
       "overwhelming presence, reality-bending power",
}

def _tier_flavor(birth_star: int) -> str:
    return TIER_FLAVOR.get(birth_star, TIER_FLAVOR[1])

# ---------------------------------------------------------------------------
# Archetype variety pools
# ---------------------------------------------------------------------------

# ~80% human by design — fantasy races stay flavorful without taking over the roster.
RACES = [
    ("human", 80),
    ("elf, pointed ears, elegant exotic features", 6),
    ("beastfolk, animal ears, feral features, exotic aesthetics", 6),
    ("dark elf, dark skin, pointed ears, otherworldly beauty", 4),
    ("half-elf, slightly pointed ears", 4),
]

RACES_HIGH = [
    ("human", 70),
    ("elf, pointed ears, elegant exotic features", 5),
    ("beastfolk, animal ears, feral features, exotic aesthetics", 6),
    ("dark elf, dark skin, pointed ears, otherworldly beauty", 4),
    ("half-elf, slightly pointed ears", 4),
    ("half-dragon, subtle scales on cheek, slit pupils, draconic features", 5),
    ("celestial-blooded, faint glowing halo, ethereal features", 3),
    ("tiefling, small demonic horns, unnatural skin tone", 3),
]

# Natural tones dominate (black/brown most common, blonde common, red genuinely rare).
NATURAL_HAIR = [
    ("jet black", 35),
    ("dark brown", 30),
    ("golden blonde", 30),
    ("auburn red", 5),
]
EXOTIC_HAIR = [
    "silver-white", "midnight blue", "violet", "teal", "dark green", "ash grey",
    "icy blue", "deep purple",
]

def _pick_hair_color(birth_star: int) -> str:
    """~85% natural tones, ~15% exotic — higher stars skew a bit more exotic."""
    exotic_chance = 0.15 if birth_star < 5 else 0.25
    if random.random() < exotic_chance:
        return random.choice(EXOTIC_HAIR)
    colors = [c[0] for c in NATURAL_HAIR]
    weights = [c[1] for c in NATURAL_HAIR]
    return random.choices(colors, weights=weights, k=1)[0]
HAIR_STYLES_MALE = [
    "short messy hair", "slicked back hair", "long hair tied back",
    "undercut", "wild spiky hair", "shoulder-length hair",
]
HAIR_STYLES_FEMALE = [
    "long flowing hair", "twin braids", "short bob cut", "high ponytail",
    "wavy shoulder-length hair", "messy bun",
]

SKIN_TONES = ["pale skin", "fair skin", "tan skin", "dark skin", "olive skin", "deep brown skin"]

EYE_COLORS = [
    "sharp blue eyes", "piercing amber eyes", "glowing violet eyes",
    "cold grey eyes", "fierce green eyes", "deep red eyes", "golden eyes",
]

DISTINGUISHING_FEATURES = [
    "a thin scar across the cheek", "a faded tattoo near the eye", "a small piercing",
    "a jagged scar over one eyebrow", "freckles across the nose", "no notable markings",
]

# Kept separate from physical features so expression varies independently —
# without this, almost every character defaulted to an angry glare.
EXPRESSIONS = [
    "calm composed expression", "small confident smirk", "intense focused glare",
    "weary tired expression", "gentle subtle smile", "wary cautious expression",
    "prideful haughty expression", "sorrowful distant gaze", "alert sharp-eyed expression",
    "stoic unreadable expression",
]

# Danbooru-native clothing tags. Two hard-won rules: avoid the word "gear"
# (it tokenizes toward mecha/機械 — a Thief in "hooded leather gear" came out
# in a mech suit), and every class gets an explicit outfit — the old vague
# DEFAULT_OUTFIT ("dark fantasy adventurer's clothing") was where support
# classes like Merchant drifted off-style.
CLASS_OUTFITS = {
    "Warrior": "heavy armor, pauldrons, weathered torn cloak, gauntlets, sturdy leather boots",
    "Knight": "ornate plate armor, engraved pauldrons, surcoat, armored sabatons",
    "Berserker": "fur trim armor, war paint, bare shoulders, scars, fur-wrapped boots",
    "Paladin": "silver plate armor, white cape, glowing sigils, gorget, armored sabatons",
    "Spearman": "scale armor, leather straps, shoulder plate, sashes, leather boots",
    "Thief": "black hooded cloak, dark leather armor, dagger sheath on thigh, fingerless gloves, face-shadowing hood, soft leather boots",
    "Archer": "hooded green cloak, leather vambraces, quiver on back, bow, leather boots",
    # Tome, not staff — established art preference (staffs render badly and
    # the game's Mage identity is the Tome; see frontend prefs)
    "Mage": "long flowing robe, wide sleeves, glowing runes on fabric, holding an open arcane tome, glowing magical script floating from its pages, pointed leather shoes",
    "Acolyte": "simple holy vestments, prayer beads, cloth sash, simple sandals",
    "Spellsword": "half-plate armor over cloth, runed sword, glowing blade, armored boots",
    "Magic Engineer": "goggles on head, leather apron, mechanical gauntlet on one arm, tool belt, heavy work boots",
    "Classless": "worn traveling clothes, patched cloak, simple tunic",
    # support & profession classes — previously all fell to the default
    "Chef": "chef whites reimagined as fantasy garb, apron, rolled sleeves, cleaver at the belt, sturdy shoes",
    "Medic": "long coat with satchel, bandage rolls at the belt, gloves, leather shoes",
    "Scout": "camouflage cloak, light leather armor, spyglass at the hip, soft travel boots",
    "Blacksmith": "sturdy work shirt with rolled sleeves, heavy leather apron, thick gloves, soot smudges, hammer at the belt, heavy work boots",
    "Quartermaster": "practical field uniform, ledger satchel, many belt pouches, sturdy boots",
    "Tactician": "military longcoat with epaulettes, map case, white gloves, polished riding boots",
    "Priest": "ornate ecclesiastical robes, gold trim stole, censer, simple shoes",
    "Alchemist": "long dark coat, potion vials strapped across chest, stained gloves, leather shoes",
    "Merchant": "rich fabric doublet, fur-lined mantle, coin pouch and rings, traveling pack, fine leather boots",
    "Farmer": "rustic work clothes, straw hat on back, sickle at the belt, worn work boots",
}
DEFAULT_OUTFIT = "dark fantasy traveling clothes, worn cloak, leather boots"

# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

GLASSES_STYLES = ["thin wire-frame glasses", "round spectacles", "sharp rectangular glasses"]
GLASSES_BASE_CHANCE = 0.06
GLASSES_NON_MELEE_BONUS = 0.10  # additive — ranged/caster classes read better with glasses than frontline melee

def _glasses_trait(hero_class: str) -> str:
    """Rare standalone visual trait, independent of the Magic Engineer's
    goggles (which are baked into CLASS_OUTFITS, not this roll) — more
    likely on ranged/caster classes than melee."""
    from services.class_service import CLASS_MODIFIERS
    mods = CLASS_MODIFIERS.get(hero_class, {})
    is_non_melee = bool(mods.get("is_ranged")) or mods.get("power_stat") == "intelligence"
    chance = GLASSES_BASE_CHANCE + (GLASSES_NON_MELEE_BONUS if is_non_melee else 0)
    return random.choice(GLASSES_STYLES) if random.random() < chance else ""

def _random_traits(birth_star: int = 1, gender: str = "unknown", hero_class: str = "Classless") -> dict:
    if gender not in ("male", "female"):
        gender = random.choice(["male", "female"])

    race_pool = RACES_HIGH if birth_star >= 5 else RACES
    race = random.choices([r[0] for r in race_pool], weights=[r[1] for r in race_pool], k=1)[0]
    hair_style = random.choice(HAIR_STYLES_MALE if gender == "male" else HAIR_STYLES_FEMALE)

    return {
        "gender": gender,
        "race": race,
        "hair": f"{_pick_hair_color(birth_star)} hair, {hair_style}",
        "skin": random.choice(SKIN_TONES),
        "eyes": random.choice(EYE_COLORS),
        "feature": random.choice(DISTINGUISHING_FEATURES),
        "expression": random.choice(EXPRESSIONS),
        "glasses": _glasses_trait(hero_class),
    }

def _pick_class_for_star(birth_star: int) -> str:
    from services.class_service import assign_class
    hero_class, _ = assign_class(birth_star)
    return hero_class

def _prompt_from_traits(traits: dict, hero_class: str, birth_star: int) -> str:
    outfit = CLASS_OUTFITS.get(hero_class, DEFAULT_OUTFIT)
    gender_tag = "1boy" if traits["gender"] == "male" else "1girl"
    glasses_tag = f", {traits['glasses']}" if traits.get("glasses") else ""
    return (
        f"{gender_tag}, {traits['race']}, {traits['hair']}, {traits['skin']}, {traits['eyes']}, "
        f"{traits['expression']}, {traits['feature']}{glasses_tag}, {outfit}, {_tier_flavor(birth_star)}, "
        f"looking at viewer, {_quality_tag(birth_star)}, "
        f"{_random_pose(hero_class)}, {FRAMING}, {BASE_STYLE}"
    )

def build_varied_prompt(birth_star: int = 1, gender: str = "unknown") -> tuple:
    """Build a fully varied portrait prompt in the house style, including a fresh
    class roll. Returns (prompt, gender, hero_class)."""
    hero_class = _pick_class_for_star(birth_star)
    traits = _random_traits(birth_star, gender, hero_class)
    prompt = _prompt_from_traits(traits, hero_class, birth_star)
    return prompt, traits["gender"], hero_class

def build_appearance_prompt(birth_star: int, hero_class: str, gender: str = "unknown") -> str:
    """Reroll just the look (race/hair/eyes/skin/expression/feature) for an
    existing hero, keeping their class fixed. Used by the 'Regenerate Portrait'
    button so a player can reroll a bad-looking hero without losing their
    name, lore, or identity."""
    traits = _random_traits(birth_star, gender, hero_class)
    return _prompt_from_traits(traits, hero_class, birth_star)

# ---------------------------------------------------------------------------
# Cache pool (DB-backed)
# ---------------------------------------------------------------------------

def get_cache_counts() -> dict:
    with db() as conn:
        rows = conn.execute("""
            SELECT birth_star, COUNT(*) as cnt
            FROM portrait_cache
            WHERE used = 0
            GROUP BY birth_star
        """).fetchall()
    return {r["birth_star"]: r["cnt"] for r in rows}

def pop_cached_portrait(birth_star: int, class_name: str = None):
    """Claim a pre-generated portrait for this star. Returns (path, gender, class_name) or None.
    Pass class_name to prefer a portrait drawn for that class (spark wishlist)."""
    with db() as conn:
        row = None
        if class_name:
            row = conn.execute("""
                SELECT id, path, gender, class_name FROM portrait_cache
                WHERE birth_star = ? AND used = 0 AND class_name = ?
                ORDER BY created_at ASC
                LIMIT 1
            """, (birth_star, class_name)).fetchone()
        if not row:
            row = conn.execute("""
                SELECT id, path, gender, class_name FROM portrait_cache
                WHERE birth_star = ? AND used = 0
                ORDER BY created_at ASC
                LIMIT 1
            """, (birth_star,)).fetchone()
        if not row:
            return None
        conn.execute("UPDATE portrait_cache SET used = 1 WHERE id = ?", (row["id"],))
        return (row["path"], row["gender"], row["class_name"])

def add_to_cache(birth_star: int, path: str, gender: str, class_name: str):
    with db() as conn:
        conn.execute(
            "INSERT INTO portrait_cache (birth_star, path, gender, class_name) VALUES (?,?,?,?)",
            (birth_star, path, gender, class_name)
        )

def update_hero_portrait(hero_id: int, path: str):
    """Point a hero at a new portrait file, deleting the old custom one it
    replaces — regeneration (promotion upgrades, manual regen) otherwise
    leaves every previous version behind on disk forever."""
    with db() as conn:
        old = conn.execute("SELECT portrait_path FROM heroes WHERE id = ?", (hero_id,)).fetchone()
        old_path = old["portrait_path"] if old else None
        conn.execute("UPDATE heroes SET portrait_path = ? WHERE id = ?", (path, hero_id))
    if old_path and old_path != path and "default_" not in old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception:
            pass

def handle_fallen_portrait(hero_id: int, portrait_path: str, is_sacrifice: bool) -> str | None:
    """A fallen hero's portrait is only worth keeping if they were sacrificed
    (memorialized) — an ordinary combat death just loses its portrait, there's
    no alive/dead split to maintain otherwise. Returns the new path for a
    memorialized portrait, or None (nothing to move, or the portrait was
    deleted because this wasn't a sacrifice)."""
    if not portrait_path or not os.path.exists(portrait_path):
        return None

    if not is_sacrifice:
        try:
            os.remove(portrait_path)
            update_hero_portrait(hero_id, None)
        except Exception as e:
            print(f"[Cache] Failed to delete portrait for fallen hero {hero_id}: {e}")
        return None

    memorial_dir = f"static/portraits/{database.ACTIVE_PROFILE}/memorial"
    os.makedirs(memorial_dir, exist_ok=True)
    new_path = f"{memorial_dir}/{os.path.basename(portrait_path)}"
    try:
        os.rename(portrait_path, new_path)
        update_hero_portrait(hero_id, new_path)
        return new_path
    except Exception as e:
        print(f"[Cache] Failed to move memorialized portrait for hero {hero_id}: {e}")
        return None

def rename_portrait_for_hero(hero_id: int, old_path: str, hero_name: str):
    """Move a claimed cached portrait into the active profile's permanent folder. Returns new path or None."""
    if not old_path or not os.path.exists(old_path):
        return None
    custom_dir = f"static/portraits/{database.ACTIVE_PROFILE}/alive"
    os.makedirs(custom_dir, exist_ok=True)
    safe_name = re.sub(r'[^a-z0-9]', '_', hero_name.lower())[:30]
    new_path = f"{custom_dir}/custom_hero_{hero_id}_{safe_name}_{int(time.time())}.png"
    try:
        os.rename(old_path, new_path)
        update_hero_portrait(hero_id, new_path)
        with db() as conn:
            conn.execute("DELETE FROM portrait_cache WHERE path = ?", (old_path,))
        return new_path
    except Exception as e:
        print(f"[Cache] Failed to rename portrait for hero {hero_id}: {e}")
        return None

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def _generate_one_cached(birth_star: int):
    if get_cache_counts().get(birth_star, 0) >= MAX_PER_STAR.get(birth_star, 999):
        return
    try:
        from services.comfy_service import generate_portrait_comfy
        prompt, gender, hero_class = build_varied_prompt(birth_star)
        os.makedirs(CACHE_DIR, exist_ok=True)
        filename = f"{CACHE_DIR}/cached_{birth_star}star_{int(time.time())}_{random.randint(1000, 9999)}.png"
        # hires=True: two-pass upscale-refine. Cache fill is a background
        # job, so the ~2x generation time is free — and the second pass is
        # what rescues small faces/eyes at full-body framing.
        success = generate_portrait_comfy(prompt, filename, negative=NEGATIVE_STYLE, hires=True)
        if success:
            add_to_cache(birth_star, filename, gender, hero_class)
            print(f"[Cache] Generated {birth_star}★ {hero_class} ({gender}) portrait -> {filename}")
        else:
            print(f"[Cache] Generation failed for {birth_star}★")
    except Exception as e:
        print(f"[Cache] Error generating {birth_star}★: {e}")

def _generate_custom_portrait(hero_id: int, portrait_prompt: str, hero_name: str, gender: str = "unknown"):
    """Generate a hero-specific portrait from the LLM's portrait_prompt, in the house style."""
    try:
        from services.comfy_service import generate_portrait_comfy
        custom_dir = f"static/portraits/{database.ACTIVE_PROFILE}/alive"
        os.makedirs(custom_dir, exist_ok=True)
        safe_name = re.sub(r'[^a-z0-9]', '_', hero_name.lower())[:30]
        filename = f"{custom_dir}/custom_{safe_name}_{hero_id}_{int(time.time())}.png"

        gender_tag = "1boy" if gender == "male" else "1girl" if gender == "female" else "1person"
        full_prompt = (
            f"{gender_tag}, looking at viewer, {_quality_tag(5)}, "
            f"{FRAMING}, {BASE_STYLE}, " + portrait_prompt
        )
        success = generate_portrait_comfy(full_prompt, filename, negative=NEGATIVE_STYLE)
        if success:
            update_hero_portrait(hero_id, filename)
            _prewarm_card(hero_id, filename)
            print(f"[Cache] Custom portrait ready for hero {hero_id}")
    except Exception as e:
        print(f"[Cache] Custom portrait failed for hero {hero_id}: {e}")

def _prewarm_card(hero_id: int, portrait_path: str):
    """Run the card composite (both the full and grid-thumbnail variants)
    now, in this background thread, instead of leaving it to happen on
    whichever request first loads this hero's card — that first request
    used to be the player's own page load, stalling every portrait on
    screen at once."""
    try:
        with db() as conn:
            hero = conn.execute("SELECT birth_star, name, hero_class FROM heroes WHERE id = ?", (hero_id,)).fetchone()
        if not hero:
            return
        from services.card_template_service import composite_card
        composite_card(hero_id, portrait_path, hero["birth_star"], hero["name"], crop_face=False, hero_class=hero["hero_class"])
        composite_card(hero_id, portrait_path, hero["birth_star"], hero["name"], crop_face=True, hero_class=hero["hero_class"])
    except Exception as e:
        print(f"[Cache] Card prewarm failed for hero {hero_id}: {e}")

def queue_custom_portrait(hero_id: int, portrait_prompt: str, hero_name: str, gender: str = "unknown"):
    """A hero is waiting on a portrait right now — jump to the front of the generation queue."""
    _enqueue(PRIORITY_URGENT, _generate_custom_portrait, hero_id, portrait_prompt, hero_name, gender)

def queue_upgrade_portrait(hero_id: int, new_star: int):
    """Regenerate a hero's portrait at a star-rank milestone (more ornate gear/aura). Urgent — the
    player is looking at this hero's promotion result right now."""
    def _job():
        with db() as conn:
            hero = conn.execute(
                "SELECT name, hero_class, gender FROM heroes WHERE id = ?", (hero_id,)
            ).fetchone()
        if not hero:
            return
        upgrade_tag = {
            3: "battle-worn gear, sharper expression",
            5: "ornate gear, imposing presence",
            7: "legendary ornate armor, overwhelming presence",
        }.get(new_star, "upgraded gear")
        prompt = f"{hero['hero_class']}, {upgrade_tag}, promoted to {new_star} star rank"
        _generate_custom_portrait(hero_id, prompt, hero["name"], hero["gender"] or "unknown")
    _enqueue(PRIORITY_URGENT, _job)

# ---------------------------------------------------------------------------
# Enemy portraits — a small, finite, reused library (NOT one-per-instance).
# Enemy types are a fixed set reused across every fight (combat_service.py's
# ENEMY_TYPES), so each type gets exactly one portrait, generated once, ever.
# ---------------------------------------------------------------------------

ENEMY_DIR = "static/portraits/enemies"

# Every hint calls out specific, bright/saturated material colors (not just one
# glow accent) — that's what keeps the sampler from collapsing the whole body
# into shadow. See MONSTER_STYLE/MONSTER_NEGATIVE above for why.
ENEMY_PORTRAIT_HINTS = {
    "Corpse Rat": "(rat, rodent, murid, feral, quadruped:1.3), a giant plague rat hunched in a torchlit sewer tunnel, a long pointed rat snout with whiskers, large round tattered ears, (a long pink hairless tail:1.2), oversized yellowed incisors, mottled grey-brown patchy fur with visible grime, sickly green glow from its eyes and open sores lighting its face, warm torchlight falling from a grate above",
    "Grave Scarab": "an armored undead SCARAB BEETLE, an insect with six segmented bronze-tinted legs and a glossy dark purple-black beetle carapace, glowing teal rune cracks across its shell, faintly glowing curled antennae, low to the ground like an insect",
    "Plague Crawler": "a centipede-like plague beast, a long segmented insectoid body with dozens of dark red jointed legs, sickly olive-green chitinous segments, oozing yellow pustules, small mandibles, low slithering posture",
    "Abyssal Spider": "(spider, arachnid, feral:1.2), a giant spider descending from luminous silk strands, glossy deep violet carapace with red banded markings (clearly lit:1.2), eight glowing amber eyes, curved fangs dripping pale green venom, thin segmented legs silhouetted against a mist-blue cave mouth lit by cold moonlight behind it",
    "Hollow Knight": "a hollow undead knight standing upright in weathered bronze-green plate armor, an empty helm with a faint blue spectral glow leaking from the visor and joints, a tattered crimson cloth sash, a knightly battle stance",
    "Bone Warden": "a skeletal guardian standing firmly on bleached white bone legs in a defensive stance, bone plating fused with tarnished silver armor across its chest and shoulders, glowing violet runes etched along its ribs and skull, gripping a weapon",
    "Flame Wraith": "a humanoid wraith composed of dark orange and red flame, charred black tattered robes with glowing ember-orange seams, flames visibly licking along its silhouette and within its hood, glowing ember-orange eyes",
    "Shriek Shade": "a screaming humanoid wraith, a hooded ghostly form rendered almost entirely in near-black with very dark deep-lavender undertones, subtle lighter-grey grain and highlights along the folds and tattered edges of its robes so the shape isn't perfectly flat, a clearly readable hooded humanoid silhouette, a gaping hollow mouth frozen in a scream, two small dim white dot-eyes, faint tendrils trailing from its form",
    "Stone Golem": "(golem, rock creature:1.2), a hulking stone golem standing in a torchlit ancient ruin, rough granite slabs stacked like overlapping armor with moss in the crevices, (molten orange light glowing from the cracks between plates, lighting its own chest and arms:1.2), two furnace-orange eyes in a craggy face, oversized boulder fists, warm torchlight on broken pillars behind",
    "Dread Brute": "a hulking humanoid brute, scarred dark-tan skin, rusted iron-brown armor plating on its shoulders and forearms, gripping a crude obsidian-black weapon with glowing red runes along the blade, a snarling expression",
    "Abyssal Lurker": "a twisted abyssal beast crouched low on multiple clawed limbs, slick dark teal hide with bioluminescent cyan markings, rows of glowing white eyes along its head, translucent membranous fins along its spine",
    "Carrion Bat": "(bat, feral, membranous wings:1.2), a giant carrion bat swooping beneath a full moon, leathery brown-purple wings spread wide and (backlit by moonlight, veins visible through the glowing membrane:1.2), a fanged snout open in a shriek, oversized pointed ears, glowing yellow eyes, patchy matted fur, silver moonlit clouds and a bone-littered ridge below",
    "Rotting Ghoul": "a feral humanoid ghoul, grey-green decaying flesh with visible muscle striations, torn dark tattered clothing, elongated blackened claws, glowing dull yellow eyes, a hunched predatory posture",
    "Iron Revenant": "an animated suit of rusted iron armor standing upright on its own, deep orange rust streaks over dark steel plating, faint blue spectral light glowing through the helm's eye slits, empty clenched gauntlets",
    # Concept redesigned 2026-07-06 — the original "reptilian creature"
    # rendered as a photoreal museum model across three recipe versions
    # (same curse as the old slimes). Now a venom-lit serpent-hound: canine
    # body prior renders reliably in-style, and the venom glow gives the
    # scene its own light source.
    "Venom Stalker": "(serpent, canine, feral:1.2), a gaunt venom-drenched serpent-hound, a lean black hound body with a scaled serpentine neck and snake head, glowing toxic-green eyes, luminous green venom dripping from its fangs and lighting its jaw and chest from below, glowing acid pools on the dark swamp floor around its paws, moonlit dead trees behind",
    "Frost Wight": "a frozen undead wight, a humanoid figure with pale icy-blue cracked skin, tattered frost-rimed dark robes, a dim subdued icy-blue glow in its eyes (not blindingly bright), jagged ice shard protrusions along its back, visible facial features beneath a frost-crusted hood",
    "Obsidian Behemoth": "(a massive behemoth whose entire hide is dominantly glossy black and deep purple volcanic obsidian, black and purple are the majority colors covering most of its body:1.3), on four powerful legs, rough jagged obsidian surface texture with individual visible cracked plates and shards, glossy black-purple reflective highlights along the broken edges, only thin glowing magma-orange veins as a minor accent threading sparingly between the dark obsidian plates — orange should cover a small minority of the surface, not the whole body, glowing red eyes, jagged obsidian spikes along its spine",
    # --- beginner/intermediate tier (added alongside the floor-gated monster
    # tiers in combat_service.py — these previously fell back to the thin
    # generic hint, which is why they looked inconsistent with the rest) ---
    # Renamed from "Giant Rat" — rodent shapes read as cute/cartoonish
    # against this game's tone (openspec/specs/enemy-art-overhaul). Prompt
    # text is the spec's own suggested phrasing.
    "Giant Spider": "a giant spider, eight legs, arachnid, cave dungeon background",
    "Mangy Hyena": "a feral hyena, tawny fur covered in dark brown spots and patches, a powerful jaw with bared yellowed teeth, glowing amber eyes, a hunched sloped back with powerful front shoulders, low aggressive stalking stance on all fours, dusty wasteland background",
    "Goblin": "a small wiry goblin humanoid, (sickly green mottled skin, green clearly visible as the skin color:1.3), oversized pointed ears, a hooked nose, sharp yellowed teeth bared in a snarl, ragged dark leather scraps for clothing, gripping a crude rusted blade, standing alert lunging stance mid-attack with weapon raised high, beady yellow eyes, gritty dungeon background",
    "Bandit": "a rough human bandit, weathered tan skin, a worn leather jerkin and a loose hood pushed back enough to show his face, narrowed eyes, scarred forearms, gripping a plain worn dagger, alert lean stance, dim alley background",
    "Wolf": "(wolf, canine, feral, quadruped:1.2), an adult wolf standing on all four legs in a snowy forest at night, dense grey and white fur, pointed ears forward, fangs bared in a snarl, glowing pale yellow eyes, a lean athletic build, bushy tail held low",
    "Orc": "a hulking orc warrior standing in a war-camp at dusk, green-grey skin evenly lit across his face and body, a jutting lower jaw with tusks, small dark eyes under a heavy brow, spiked iron armor plates over leather, gripping a heavy cleaver-like blade",
    "Ogre": "an enormous OGRE giant, twice the height and bulk of a normal man, a massive bloated frame with thick rolls of muscle and fat, warty greenish-brown skin, a disproportionately huge brutish jaw with jutting yellowed tusks, a small head sitting atop a vastly oversized hulking body, small dull eyes, wrapped in crude furs and rusted armor scraps that look small and stretched on its huge frame, gripping a tree-trunk-sized wooden club studded with nails, hunched towering stance dwarfing its surroundings",
    "Troll": "a tall gaunt TROLL, (sickly grey-green warty hide with patches of coarse moss-like growth, clearly visible color and texture, not solid black:1.2), an elongated jaw with crooked yellowed tusks, sunken glowing dull-yellow eyes, long gangly muscular arms ending in clawed hands, hunched predatory stance, well-lit damp cave background",
    "Harpy": "a fierce harpy warrior, a wild sharp-featured humanoid with large feathered wings in place of arms, mottled brown and rust-orange plumage with detailed individual feathers, taloned bird legs below the knee, tattered cloth wraps, wind-blown wild hair, piercing pale eyes, fierce snarl, wings flared wide mid-swoop, well-lit stormy cliffside background",
    "Shrouded Reaper": "(a tall hooded reaper-like figure shrouded entirely in flowing black robes and a deep hood concealing the face:1.3), bone-pale skeletal clawed hands visible at the sleeves, ornate dark engraved bracers, gripping a curved ornate ceremonial dagger low at the waist, standing motionless and imposing, faint cold blue ambient light, deep atmospheric fog, an aura of dread and supernatural menace, towering and elite",
    # --- floor 1-10 family elites — previously fell back to the thin generic
    # hint with no color/shape anchor, which is exactly why these rendered
    # as near-black blobs with nothing recognizable in them ---
    # Renamed from "Slime" — round/amorphous blobs render poorly through
    # this pipeline and read as cute rather than threatening
    # (openspec/specs/enemy-art-overhaul). Acid Slime removed entirely for
    # the same reason — gelatinous blobs never render well regardless of
    # prompt engineering effort.
    "Goblin Warrior": "a goblin warrior standing in torchlight in a dungeon, green skin clearly lit on his face and arms, oversized pointed ears, a hooked nose, yellowed teeth bared in a snarl, scavenged leather and scrap-metal armor over his chest, gripping a short iron sword, beady yellow eyes",
    "Goblin Shaman": "a goblin shaman standing in torchlight in a dungeon, green skin clearly lit on his face and hands, oversized pointed ears, a hooked nose, ragged brown cloth robes with bone trinkets tied on with twine, gripping a wooden staff topped with a glowing skull, green magic swirling around his raised hand, beady yellow eyes",
    "Spider Queen": "a massive spider queen perched on a throne of webs, crimson and ochre patterned abdomen, eight thick legs gripping silk strands, six glowing amber eyes, dim cave background",

    # Goblin King / Warren Tyrant (floor 5/10) never actually got dedicated
    # art despite the family-override system supporting it — discovered
    # while auditing portrait coverage for the floor 21-100 pass below,
    # both were silently falling back to the generic boss archetype pool.
    "Goblin King": "a crowned goblin king seated on a crude wooden throne, sickly green mottled skin clearly lit, oversized pointed ears, a hooked nose, a dented golden crown too big for his head, ragged dark velvet robes over scavenged armor, gripping a jagged scepter, beady yellow eyes, torchlit goblin-warren throne background",
    "The Warren Tyrant": "a colossal mutated rat overlord standing on its hind legs, matted dark brown-grey fur clearly lit with patches of scarred skin, an oversized scarred snout with broken yellowed incisors, a long thick ropey tail, glowing red eyes, hunched over a pile of bones and scraps, torchlit sewer-warren background",

    # --- floor 21-100 roster (added this pass) — humanoid ones use
    # HUMANOID_ENEMY_NAMES/HUMANOID_EVIL_STYLE instead of MONSTER_STYLE, see
    # _generate_enemy_portrait. Plain affirmative language throughout —
    # heavy "(NOT X:1.4)" negation backfired earlier in this same file
    # (the model partially keys on the negated word's tokens anyway).
    "Hobgoblin": "a hulking hobgoblin warrior standing in torchlight, leathery reddish-brown skin clearly lit, a broad brutish face with small tusks, wearing scavenged spiked armor over a muscular frame, gripping a heavy curved blade, yellow eyes, gritty dungeon background",
    "Lizardman": "a lizardman warrior standing in torchlight, scaled green-grey skin clearly lit across its body, a reptilian snouted face with a forked tongue, wearing simple woven straps and bone ornaments, gripping a serrated bone spear, slitted yellow eyes, swampy cave background",
    "Hobgoblin Berserker": "a scarred hobgoblin berserker mid-roar, reddish-brown leathery skin clearly lit, bulging muscles, war paint streaked across its face, wielding two crude jagged axes raised high, torn furs over its shoulders, bloodshot yellow eyes, torchlit battlefield background",
    "Lizardman Stalker": "a lean lizardman stalker crouched low, scaled dark-green skin clearly lit with faint mottled patterns, a sharp reptilian face with a hood of bony frills, gripping twin curved bone daggers, slitted amber eyes, misty swamp background",
    "Plague Harbinger": "a withered ghoul-priest in tattered grey-green burial robes, sickly pale-green rotting skin clearly lit on its gaunt face and hands, hollow sunken eyes glowing faint sickly yellow, clutching a rusted censer dripping dark plague vapor, hunched robed figure, dim crypt background",
    "Minotaur": "a towering minotaur standing upright, thick dark-brown fur covering a muscular humanoid body clearly lit, a bull's head with massive curved horns and a ring through its nose, gripping a huge stone battleaxe, glowing red eyes, torchlit labyrinth background",
    "Minotaur Juggernaut": "a massive armored minotaur juggernaut standing upright, dark-brown fur clearly lit beneath heavy plated bronze armor, a scarred bull's head with broken horns, gripping an enormous spiked maul, glowing crimson eyes, dust and rubble around its feet, torchlit arena background",
    "Stone Sentinel": "a humanoid stone sentinel construct standing at attention, rough grey granite body clearly lit with visible cracked seams, glowing faint blue runes etched across its chest and arms, a blank featureless carved face, fists like boulders, ancient ruin background",
    "Lesser Golem": "a humanoid clay golem standing stiffly, cracked sandy-brown clay body clearly lit with visible seams and patchwork repairs, a crude carved face with glowing dim orange eyes, simple blocky proportions, dusty workshop ruin background",
    "Naga": "a naga warrior with a humanoid torso and a long coiled serpent tail, scaled emerald-green skin clearly lit, a crowned hooded head with slitted golden eyes, wielding a trident, ornate gold armbands, mist-shrouded temple ruin background",
    "Death Knight": "an armored death knight standing tall, blackened plate armor clearly lit with glowing blue runic engravings, a closed helm with two piercing icy-blue eye slits, gripping a massive runed greatsword, a tattered dark cape, frosty battlefield background",
    "Giant": "a towering giant warrior standing upright, weathered tan-grey skin clearly lit over a massive muscular frame, a craggy brutish face with a braided beard, wrapped in crude furs and banded iron plates, gripping an uprooted tree as a club, mountain pass background",
    "Black Knight Commander": "an imposing black knight commander standing tall, polished obsidian-black plate armor clearly lit with sharp silver trim, a horned closed helm with glowing violet eye slits, gripping an ornate longsword raised, a flowing dark cape, torchlit fortress background",
    "Demon": "a horned demon warrior standing upright, deep crimson-red skin clearly lit over a muscular humanoid body, curved black horns, leathery folded wings, clawed hands, glowing amber eyes, wreathed in faint smoke, hellish cavern background",
    "Imp": "a small wiry imp grinning mischievously, dark reddish-purple skin clearly lit, small curved horns, batlike wings, a long barbed tail, clawed hands, glowing yellow eyes, perched on a rock, hellish cavern background",
    "Pit Fiend": "a massive armored pit fiend standing upright, charred dark-red skin clearly lit beneath spiked black armor plates, large curved horns, tattered leathery wings, gripping a flaming trident, glowing orange eyes, molten cavern background",
    "Wraith Sovereign": "a tall regal wraith draped in flowing tattered violet and black robes clearly lit, a pale gaunt face with glowing violet eyes beneath a torn hood, a ghostly crown hovering above its head, clawed translucent hands, misty graveyard background",
    "Lich Acolyte": "a robed lich acolyte standing with arms raised, pale bony hands and a skeletal face clearly lit beneath a tattered dark-purple hood, glowing violet eyes in hollow sockets, clutching an ancient tome, faint violet runes swirling around it, crypt background",
    "Archdemon Enforcer": "a hulking archdemon standing upright, charcoal scaled hide, bony spurs on its shoulders and spine, massive curling black horns, tattered leathery wings spread wide, clawed fists raised, burning red eyes, hellfire cavern background",
    "Orc Warchief": "a battle-scarred orc warchief standing tall, uniform green-grey skin clearly lit across his muscular body, war paint across his tusked face, wearing spiked iron pauldrons over leather, gripping a massive cleaver-axe raised high, war-camp background at dusk",
    "The Troll King": "a colossal troll king seated on a crude throne of bones, sickly grey-green warty hide clearly lit, a crooked iron crown jammed onto its elongated skull, jagged yellowed tusks, clutching a massive spiked club, glowing dull-yellow eyes, damp cave-throne background",
    "Skarn the Lizard Chieftain": "a regal lizardman chieftain standing proudly, scaled deep-green skin clearly lit with golden ceremonial markings, an ornate bone headdress, gripping a long ceremonial trident, slitted golden eyes, ancient swamp temple background",
    "The Hobgoblin Warlord": "an imposing hobgoblin warlord standing over a battlefield, reddish-brown leathery skin clearly lit beneath heavy spiked armor, a brutal scarred face, gripping a massive serrated greatsword, a tattered war banner behind him, torchlit battlefield background",
    "The Grave Sovereign": "a towering undead lord draped in regal tattered burial robes clearly lit in deep purple and faded gold, a skeletal crowned face with glowing violet eyes, clutching an ornate bone scepter, swirling graveyard mist, crypt-throne background",
    "Bullhorn the Minotaur Lord": "a massive armored minotaur lord standing triumphantly, dark-brown fur clearly lit beneath ornate bronze plate armor, enormous curved horns capped in gold, gripping a colossal battleaxe, glowing red eyes, torchlit labyrinth-throne background",
    "The Ashen Colossus": "a colossal ash-grey stone giant towering upward, cracked charcoal-black stone skin clearly lit with glowing embers seeping through the cracks, a crude carved face with glowing orange eyes, massive boulder fists, smoldering ash-covered ruins background",
    "Stoneheart the Unbroken": "a humanoid golem knight standing resolute, weathered grey granite body clearly lit with glowing teal runes across its chest, a stoic carved face, gripping a massive stone shield and warhammer, ancient ruin-throne background",
    "The Obsidian Tyrant": "an imposing obsidian golem tyrant standing tall, gleaming black volcanic-glass body clearly lit with glowing molten-orange cracks, a sharp angular carved face, gripping a massive obsidian warblade, molten cavern-throne background",
    "The Drowned Naga Queen": "a regal naga queen with a humanoid torso and a long coiled serpent tail, scaled deep-teal skin clearly lit with shimmering iridescent patterns, an ornate coral crown, slitted golden eyes, gripping a trident wreathed in mist, sunken temple background",
    "Knight-Captain Mordrek": "an armored death knight captain standing tall, blackened plate armor clearly lit with glowing icy-blue runic engravings and a captain's sash, a closed helm with piercing blue eye slits, gripping a massive runed greatsword raised high, frosty battlefield background",
    # The "Evil 7★" — written to read like a corrupted 7-star HERO portrait
    # (the pipeline's best output), not a monster: beautiful, regal, wrong.
    "Vaelor, the Fallen Ascendant": "a breathtakingly beautiful fallen hero ascendant standing in regal menace, an androgynous godlike face clearly lit with cold serene contempt, long silver-white hair drifting weightlessly, ornate celestial white-and-gold plate armor corrupted by spreading veins of void-black crystal, a cracked golden halo tilted behind his head, one arm wreathed in radiant light and the other dissolving into black flame, glowing violet eyes with faint tear-streaks of light, a magnificent greatsword of fractured starlight held point-down, ruined cathedral background with drifting golden embers",
    "Pit Fiend Commander": "a towering armored pit fiend commander standing upright, charred dark-red skin clearly lit beneath ornate spiked black armor and a commander's cape, large curved horns, gripping a flaming greatsword, glowing orange eyes, molten cavern-throne background",

    # beast/monster-style entries (MONSTER_STYLE) from the same pass
    "Scarab Swarmlord": "a massive armored beetle-like scarab, glossy dark-purple chitin shell clearly visible with iridescent sheen, oversized mandibles, six clawed legs, glowing violet eyes, surrounded by smaller scarabs skittering at its sides, torchlit crypt floor background",
    "Wyvern": "(wyvern, dragon, feral:1.2), a slate-grey wyvern rearing on a cliff at sunset, membranous wings spread wide and (backlit amber by the setting sun:1.2), visible wing veins, barbed tail coiled, bared fangs, glowing amber eyes, dramatic orange storm light across its scales, sunset thunderheads behind",
    "Wyvern Stormrider": "a fierce wyvern beast crackling with electricity, leathery storm-grey wings spread wide with faint blue lightning arcing along the membrane, a long barbed tail, bared fangs, glowing white eyes, stormy cliffside background",
    "Chimera": "(chimera, multi-headed, feral:1.2), a monstrous chimera with a lion's maned body, a goat's head growing from its back, and a serpent-headed tail, (tawny golden fur clearly lit and visible:1.2), patchy goat-grey fur on the second head, bared fangs on all three heads, glowing amber eyes, well-lit rocky wasteland background at dusk",
    "Hydra Spawn": "a young multi-headed hydra beast, three serpentine necks rising from a stocky scaled body, deep-green scales clearly visible with darker mottled patterns, each head baring fangs, glowing yellow eyes, swampy lair background",
    "Young Dragon": "a young dragon on all fours, quadruped, scales, horns, wings, fangs, mountain cave background",
    "Adult Dragon": "a massive adult dragon rearing up on powerful hind legs, overlapping dark-crimson and obsidian scales clearly visible with plate-like texture, large swept-back horns, enormous leathery wings spread wide, bared fangs with fire and smoke billowing from its jaws, blazing amber eyes, heavily scarred and battle-worn, rocky mountain peak background wreathed in flame",
    "Dracolich": "an undead dragon, bleached bone-white scales and exposed ribs clearly visible over a skeletal serpentine frame, tattered leathery wing-remnants, a skull-like draconic head with glowing violet eyes, faint violet mist trailing from its jaws, crypt-cavern background",
    "The Hydra Sovereign": "a colossal multi-headed hydra beast towering upward, five serpentine necks rising from a massive scaled body, deep emerald-green scales clearly visible with darker ridged patterns, each head baring fangs and glowing yellow eyes, swampy lair-throne background",
    "The Dracolich Herald": "an imposing undead dragon herald, bleached bone-white scales and exposed ribs clearly visible over a skeletal serpentine frame, tattered leathery wing-remnants trailing violet mist, a crowned skull-like draconic head with glowing violet eyes, crypt-cavern-throne background",

    # --- 13 checklist normals added to fill each decade out to its full
    # 4-normal/2-elite roster (PLAN_floor_workshop_enemies.md's family
    # table), plus 4 dedicated Raid Bosses for floors 20/40/60/80 ---
    "Kobold": "a small scaly kobold skirmisher crouched low, rough reddish-brown scaled skin clearly lit, a doglike reptilian snout with small horns, wielding a crude rusty dagger, beady red eyes, torchlit dungeon tunnel background",
    "Skeleton": "an animated skeleton warrior standing upright, bare bone clearly visible with no flesh, hollow dark eye sockets with faint blue glowing pinpricks, wielding a chipped rusty sword and a cracked wooden shield, tattered remnants of old armor, dim crypt corridor background",
    "Venomous Spider": "a sleek forest spider crouched on eight segmented legs, olive-brown and tan carapace with a distinctive darker stripe pattern clearly visible, rows of small eyes, dripping venomous fangs, dense forest undergrowth background, diffuse green-filtered light picking out the body texture",
    "Feral Ghoul": "a feral ghoul hunched forward, sickly grey-green rotting skin clearly lit, sunken yellow eyes, ragged torn clothing, long blackened claws, jaw stretched in a silent snarl, dim graveyard background",
    "Gargoyle": "a winged stone gargoyle perched low, rough grey granite hide clearly visible with cracked weathered texture, curling ram-like horns, leathery stone wings spread, clawed hands and feet, glowing faint green eyes, moonlit cathedral rooftop background",
    "Wraith": "a tall wraith draped in tattered grey-blue spectral robes clearly visible, a pale gaunt translucent face with hollow glowing blue eyes, clawed semi-transparent hands reaching forward, faint wisps trailing from its form, misty graveyard background",
    "Manticore": "a fearsome manticore beast with a lion's muscular tawny-furred body, large feathered wings, a spiked venomous scorpion tail curled over its back, a humanlike grimace with sharp fangs, glowing amber eyes, rocky desert background",
    "Elemental": "a swirling stone-and-magma elemental, jagged grey rock fragments clearly visible orbiting a glowing molten-orange core, cracks of lava light seeping between the rock plates, a roughly humanoid mass with no distinct face, rocky volcanic background",
    "Vampire Spawn": "a pale vampire spawn crouched predatorily, ashen grey-white skin clearly lit, sharp visible fangs bared, ragged dark formal clothing in tatters, clawed fingers, glowing red eyes, foggy moonlit graveyard background",
    "Primordial Vampire": "an ancient primordial vampire standing with regal menace, alabaster pale skin clearly lit on a gaunt imperious face, elongated fangs bared in a cold smile, ornate flowing robes of deep crimson and black silk centuries old, long dark hair, glowing blood-red eyes with vertical pupils, clawed hands with extended talons, shadowy gothic crypt background with drifting fog",
    "Hydra": "a massive multi-headed hydra beast, four serpentine necks rising from a thick scaled body, deep teal-green scales clearly visible with darker ridged patterning, each head baring fangs, glowing yellow eyes, swampy lake background",
    "Demon Lord": "an imposing horned demon lord standing tall, deep crimson-black skin clearly lit over a muscular humanoid frame, large curling black horns, tattered leathery wings, clawed hands wreathed in dark flame, glowing orange eyes, brimstone throne-cavern background",
    "Archdemon": "a towering archdemon standing upright, charcoal-grey scaled skin clearly lit, massive ram-like horns, leathery wings folded behind its back, a clawed muscular frame wreathed in faint dark smoke, glowing deep-red eyes, hellish cavern background",
    "Ancient Guardian": "an ancient stone guardian construct standing immobile, weathered pale-grey marble body clearly lit with faded golden runic engravings, a featureless carved face, massive folded arms, moss growing in its cracks, ancient ruined temple background",
    "Gorrath the Bonebreaker": "a towering orc-skeleton warlord standing over a battlefield of bones, half-rotted green-grey flesh clinging to exposed bone clearly lit, a cracked tusked jaw, wearing scavenged spiked plate armor, gripping a massive bone-studded warhammer, glowing red eyes, bone-littered battlefield background",
    "The Rotcaller, Warlord of the Fester Host": "a massive plague-ridden ghoul warlord standing tall, sickly mottled green-grey rotting flesh clearly lit, a swollen disease-bloated frame wrapped in tattered ceremonial robes, clutching a rusted plague-censer staff dripping dark vapor, glowing sickly yellow eyes, fetid swamp-battlefield background",
    "The Earthshaker Titan": "a colossal elemental titan towering upward, jagged grey-brown rock plates clearly visible fused over a massive humanoid frame, glowing molten-orange fissures cracking across its chest and arms, boulder-sized fists, a craggy faceless head, crumbling mountain-ruin background",
    "Mordane, the Hollow King": "an imposing vampire-knight king standing regally, pale ashen skin clearly lit beneath ornate tarnished black-and-crimson armor, a tattered royal cape, sharp fangs bared in a cold smile, clawed gauntlets, glowing crimson eyes, gothic throne-hall background",

    # Floor 50 and 100 raid bosses (added after the user flagged both floors
    # as "very important" and wanting dedicated raid encounters)
    "The Stormcaller, Sky-Tyrant": "a colossal storm-wreathed manticore-wyvern hybrid beast, a tawny-furred lion body clearly visible merging into scaled dragon wings crackling with blue lightning, a venomous spiked tail arcing with electricity, a roaring fanged maw, glowing white eyes, swirling storm-cloud background with lightning strikes",
    "Aetherion, the End of All Things": "an ancient cosmic being standing amidst shattering reality, radiant pale-gold skin clearly lit with cracks of void-black energy spreading across its body, an ornate celestial crown fused with corrupted dark metal, multiple glowing eyes arranged across its face, wings of pure light and shadow spread wide, clutching a blade made of fractured starlight, dark cosmic void background with shattering fragments",
}

def _generate_enemy_portrait(enemy_name: str, hint: str, tier_dir: str = "normal"):
    try:
        from services.comfy_service import generate_portrait_comfy
        from services.combat_service import ENEMY_WAVE
        wave = ENEMY_WAVE.get(enemy_name)
        out_dir = f"{ENEMY_DIR}/{tier_dir}/wave{wave}" if wave else f"{ENEMY_DIR}/{tier_dir}"
        os.makedirs(out_dir, exist_ok=True)
        slug = re.sub(r'[^a-z0-9]', '_', enemy_name.lower())
        path = f"{out_dir}/{slug}.png"
        if enemy_name in HUMANOID_ENEMY_NAMES:
            prompt = (
                f"{hint}, villain character design, centered composition, "
                f"imposing menacing pose, dramatic lighting, {HUMANOID_EVIL_STYLE}"
            )
            negative = HUMANOID_EVIL_NEGATIVE
        else:
            prompt = (
                f"{hint}, monster design, dark fantasy creature, centered composition, "
                f"menacing pose, dramatic lighting, {MONSTER_STYLE}"
            )
            negative = MONSTER_NEGATIVE
        success = generate_portrait_comfy(prompt, path, negative=negative)
        if success:
            print(f"[Cache] Generated enemy portrait: {enemy_name} -> {path}")
        else:
            print(f"[Cache] Enemy portrait generation failed for {enemy_name}")
    except Exception as e:
        print(f"[Cache] Error generating enemy portrait {enemy_name}: {e}")

def queue_missing_enemy_portraits():
    """Call once on startup. Each enemy type only ever needs generating once —
    unlike hero/cache jobs this never needs to re-run on a timer. Saves into
    enemies/<tier>/ (normal/elite) to match _enemy_portrait_path's lookup and
    keep the art library filterable by tier in the file browser."""
    try:
        import glob
        from services.combat_service import ENEMY_TYPES
        os.makedirs(ENEMY_DIR, exist_ok=True)
        queued = 0
        for name, *_rest, archetype, _tier in ENEMY_TYPES:
            tier_dir = "elite" if archetype == "elite" else "normal"
            slug = re.sub(r'[^a-z0-9]', '_', name.lower())
            path = f"{ENEMY_DIR}/{tier_dir}/{slug}.png"
            # Files may have been moved one level deeper into a "waveN"
            # subfolder for organizational review — still counts as present.
            in_wave_folder = glob.glob(f"{ENEMY_DIR}/{tier_dir}/wave*/{slug}.png")
            if not os.path.exists(path) and not os.path.exists(f"{ENEMY_DIR}/{slug}.png") and not in_wave_folder:
                hint = ENEMY_PORTRAIT_HINTS.get(name, f"{name}, dark fantasy monster")
                _enqueue(PRIORITY_ENEMY, _generate_enemy_portrait, name, hint, tier_dir)
                queued += 1
        if queued:
            print(f"[Cache] Queued {queued} missing enemy portrait(s) (lowest priority).")
    except Exception as e:
        print(f"[Cache] Failed to queue enemy portraits: {e}")

def queue_missing_family_portraits():
    """Named Miniboss/Boss uniques from services/enemy_families.py (e.g.
    "Goblin King", "The Warren Tyrant") aren't in ENEMY_TYPES, so the loop
    above never sees them — they need their own pass. Saves into
    enemies/miniboss/ or enemies/boss/ to match make_boss's family_override
    lookup (_enemy_portrait_path(name, "miniboss"/"boss"))."""
    try:
        from services.enemy_families import MINIBOSS_OVERRIDES, BOSS_OVERRIDES, RAID_BOSS_OVERRIDES
        os.makedirs(ENEMY_DIR, exist_ok=True)
        queued = 0
        for tier_dir, overrides in (("miniboss", MINIBOSS_OVERRIDES), ("boss", BOSS_OVERRIDES), ("raid_boss", RAID_BOSS_OVERRIDES)):
            for entry in overrides.values():
                families = entry if isinstance(entry, list) else [entry]
                for family in families:
                    name = family["name"]
                    if family.get("portrait_path"):
                        continue  # pinned to existing preserved art — never generate over it
                    slug = re.sub(r'[^a-z0-9]', '_', name.lower())
                    path = f"{ENEMY_DIR}/{tier_dir}/{slug}.png"
                    if not os.path.exists(path):
                        hint = ENEMY_PORTRAIT_HINTS.get(name, f"{name}, dark fantasy monster")
                        _enqueue(PRIORITY_ENEMY, _generate_enemy_portrait, name, hint, tier_dir)
                        queued += 1
        if queued:
            print(f"[Cache] Queued {queued} missing miniboss/boss portrait(s) (lowest priority).")
    except Exception as e:
        print(f"[Cache] Failed to queue family portraits: {e}")

# ---------------------------------------------------------------------------
# Boss portraits — also a small finite library, but keyed by VISUAL ARCHETYPE
# instead of name. Boss names/modifiers are generated fresh by the LLM every
# encounter (services/llm_service.py's generate_boss_enemy), so there's no
# stable name to pre-generate art against. Instead, each boss fight randomly
# picks one of these pre-generated archetypes for its portrait — the LLM's
# unique name/flavor text rides on top of whichever face it draws.
# ---------------------------------------------------------------------------

BOSS_DIR = "static/portraits/enemies/boss"

# Bosses get an extra "epic" flavor suffix on top of the hint — these should
# read as 6-7★ tier, not just a bigger regular monster.
BOSS_EPIC_FLAVOR = (
    "(godlike legendary being:1.2), overwhelming presence, reality-bending power, "
    "dramatic glowing aura surrounding the figure, imposing dominant pose, "
    "epic scale, towering dread, intricate ornate design details"
)

BOSS_ARCHETYPES = {
    "juggernaut": "colossal armored juggernaut, massive black-iron plate armor with glowing crimson runic engravings across the chestplate, exposed dark grey muscular arms, twin curved horns on a fully enclosed heavy steel helm with no visible face, only two narrow glowing molten-red eye-slits piercing the darkness within the helm",
    "lich_king": "a classic undead skeleton king, entirely made of plain weathered yellowed bone with no skin or flesh anywhere on its body, cracked and pitted bone texture, a bare bone skull head with hollow black eye sockets and two small glowing violet lights inside, a permanent bony grin with visible cracked teeth, gaunt bony fingers, wearing a tarnished corroded iron crown on its bare skull, heavily tattered and decayed black robes with dulled faded gold trim draped loosely over its skeletal body, dust and grime clinging to the fabric, gripping a worn ancient staff, a violet and purple magical aura glowing around it, dark gritty moody purple background",
    "demon_overlord": "an elegant male demon lord wearing a fully buttoned deep red suit jacket with black lapels over a black dress shirt and dark red necktie, tan human skin, dark slicked-back hair, a calm composed handsome face with sharp features, glowing crimson eyes, small curved horns on his forehead, dark formal gloves, a faint violet magical aura glowing behind his shoulders, dark moody background",
    "stone_titan": "a colossal hulking rock golem titan, its massive hunched silhouette entirely covered in thick rough-hewn slabs of grey granite rock fused together like overlapping armor plates, deep jagged cracks and heavily pitted weathered texture across every slab, patches of moss and loose rubble wedged in the crevices, glowing molten-orange fissures seeping through the cracks between the rock plates across its chest and arms, a craggy rock face with two glowing orange eyes, oversized boulder-like fists, towering and looming over the landscape",
    "specter_tyrant": "shadowy specter tyrant, flowing tattered cloak in deep purple and black with visible fabric texture, glowing violet runic markings along the cloak's edges, glowing pale white eyes within a hooded void face",
    "undead_monarch": "an imposing ancient vampire king standing tall and upright in a decayed gothic throne room, arms lowered at his sides, pale ash-white undead skin stretched over sharp aristocratic features, sunken dark eyes with glowing crimson irises, sharp visible fangs in a cold regal expression, slicked-back dark hair, an ornate ancient jeweled crown, an elaborate high-collared dark royal regalia in deep blood-red and tarnished black, a long tattered black cape draped from his shoulders, clawed pale hands with long sharp nails, dust and cobwebs clinging to the regalia, dim oppressive lighting with deep shadows, gritty dark fantasy anime illustration style, nothing cartoonish or bright",
    "masked_horror": "masked horror knight, featureless polished iron mask reflecting dim light, ornate dark-purple cursed armor with glowing teal runic engravings, dripping black ichor from its joints",
    "feral_titan": "a huge feral wolf-beast monster on all four legs, entirely covered in thick matted dark-brown fur from head to tail with no bare skin showing anywhere, a wolf-like head with a massive fanged maw and glowing amber eyes, visible scarring across its fur, cracked bone plating along its spine, glowing red markings on its fur, a bulky powerful build, standing on rocky ground at night, dark fantasy atmosphere, dark moody background",
    "arcane_abomination": "arcane abomination, writhing dark violet tentacled mass, glowing cyan runic markings pulsing across its many limbs, multiple glowing white eyes embedded throughout its form",
    "dragon": "majestic ancient dragon rearing back on powerful hind legs, wings spread wide casting a massive shadow, long sinuous serpentine neck arched high with its head thrown back in a roar, rows of curling ivory horns crowning its skull, glowing molten-amber reptilian eyes, rows of sharp ivory fangs bared, gleaming obsidian-black scales with glowing crimson cracks pulsing across its hide, four powerful clawed reptilian legs with sharp curved talons, a tail coiled close behind its body in proportion with its frame, billowing smoke and embers from its open jaws",
    "nightwing_devourer": "winged dark dragon-demon armored warrior, towering bat-like wings flaring out behind its shoulders, sharp curling horns crowning its helm, a glowing violet rune-core embedded in its chest, gleaming dark blue-black plated armor, clawed gauntlets raised, standing in a beam of cold blue light",
    "big_greg": "Big Greg, an enormous brutish humanoid giant covered in crude patchwork armor, missing teeth grin, small beady eyes, oversized club resting on one shoulder, dim dungeon background",
}

def _generate_boss_portrait(key: str, hint: str):
    try:
        from services.comfy_service import generate_portrait_comfy
        os.makedirs(BOSS_DIR, exist_ok=True)
        path = f"{BOSS_DIR}/boss_{key}.png"
        prompt = (
            f"{hint}, {BOSS_EPIC_FLAVOR}, monster design, dark fantasy creature, centered composition, "
            f"imposing menacing pose, dramatic lighting, epic atmosphere, {MONSTER_STYLE}"
        )
        success = generate_portrait_comfy(prompt, path, negative=MONSTER_NEGATIVE)
        if success:
            print(f"[Cache] Generated boss portrait '{key}' -> {path}")
        else:
            print(f"[Cache] Boss portrait generation failed for '{key}'")
    except Exception as e:
        print(f"[Cache] Error generating boss portrait '{key}': {e}")

def queue_missing_boss_portraits():
    """Call once on startup. Same one-time-ever pattern as enemy portraits."""
    try:
        os.makedirs(BOSS_DIR, exist_ok=True)
        queued = 0
        for key, hint in BOSS_ARCHETYPES.items():
            path = f"{BOSS_DIR}/boss_{key}.png"
            if not os.path.exists(path):
                _enqueue(PRIORITY_ENEMY, _generate_boss_portrait, key, hint)
                queued += 1
        if queued:
            print(f"[Cache] Queued {queued} missing boss portrait(s) (lowest priority).")
    except Exception as e:
        print(f"[Cache] Failed to queue boss portraits: {e}")

BOSS_TIER = {
    "juggernaut": "miniboss",
    "specter_tyrant": "miniboss",
    "masked_horror": "miniboss",
    "feral_titan": "miniboss",
    "nightwing_devourer": "miniboss",
    "big_greg": "miniboss",
    "lich_king": "boss",
    "demon_overlord": "boss",
    "stone_titan": "boss",
    "undead_monarch": "boss",
    "arcane_abomination": "boss",
    "dragon": "boss",
}

def get_random_boss_portrait(is_miniboss: bool = False) -> str:
    """Pick a random already-generated boss portrait from the tier-appropriate
    pool (lesser archetypes for minibosses, epic archetypes for full bosses).
    Falls back to the full pool if that tier hasn't finished generating yet."""
    try:
        if not os.path.isdir(BOSS_DIR):
            return ""
        all_files = [f for f in os.listdir(BOSS_DIR) if f.endswith(".png")]
        if not all_files:
            return ""
        tier = "miniboss" if is_miniboss else "boss"
        tier_keys = {k for k, t in BOSS_TIER.items() if t == tier}
        tier_files = [f for f in all_files if f[len("boss_"):-len(".png")] in tier_keys]
        files = tier_files or all_files
        return f"{BOSS_DIR}/{random.choice(files)}"
    except Exception:
        return ""

def _refill_routine_queue():
    """Top up the cache pool to quota. Only ever called once the job queue has been fully
    drained (see _portrait_worker_loop), so get_cache_counts() reflects every job that's
    actually finished — no stale snapshots, no double-counting a deficit that's already
    been queued but not yet generated."""
    try:
        counts = get_cache_counts()

        # First: at least 1 of every star, so a fresh cache spreads across all
        # rarities instead of finishing star 1's full quota before star 2 starts.
        for star in MIN_PER_STAR:
            if counts.get(star, 0) == 0:
                _enqueue(PRIORITY_ROUTINE, _generate_one_cached, star)
                counts[star] = 1

        # Then: fill the rest of each star's quota.
        for star, minimum in MIN_PER_STAR.items():
            needed = minimum - counts.get(star, 0)
            for _ in range(max(0, needed)):
                _enqueue(PRIORITY_ROUTINE, _generate_one_cached, star)
    except Exception as e:
        print(f"[Cache] Refill check failed: {e}")

def _portrait_worker_loop():
    print("[Cache] Portrait worker started.")
    while True:
        try:
            _, _, fn, fn_args = _job_queue.get(timeout=10.0)
            try:
                fn(*fn_args)
            except Exception as e:
                print(f"[Cache] Job failed: {e}")
        except pqueue.Empty:
            _refill_routine_queue()
            # Enemy/boss libraries used to only get checked once, at startup —
            # if a job silently failed or got cut short by a reload, nothing
            # ever retried it. Both functions are idempotent (skip anything
            # that already exists on disk), and this only runs once the queue
            # is fully drained, so it's safe to call every idle cycle.
            queue_missing_enemy_portraits()
            queue_missing_boss_portraits()

def start_cache_worker():
    t = threading.Thread(target=_portrait_worker_loop, daemon=True)
    t.start()

# Bump when the generation PIPELINE itself changes shape (framing, aspect,
# background) such that every existing portrait should be regenerated — as
# opposed to CARD_STYLE_VERSION, which only rebuilds the composited card
# over an unchanged portrait. v1 = the move to full-body framing.
PORTRAIT_STYLE_VERSION = 1


def maybe_reset_portrait_pipeline():
    """One-time-per-profile wipe when PORTRAIT_STYLE_VERSION advances: the
    old bust portraits and their cached cards are deleted and every hero is
    reset to a placeholder so reconcile_pending_portraits regenerates them
    full-body. Called on startup BEFORE reconcile. Safe/idempotent — guarded
    by base.portrait_style_version so it runs exactly once per bump."""
    try:
        with db() as conn:
            row = conn.execute("SELECT portrait_style_version FROM base WHERE id = 1").fetchone()
            current = (row["portrait_style_version"] if row and row["portrait_style_version"] is not None else 0)
            if current >= PORTRAIT_STYLE_VERSION:
                return

            # 1. Drop the unclaimed pre-generated pool (rows + files).
            pool = conn.execute("SELECT path FROM portrait_cache").fetchall()
            for p in pool:
                try:
                    if p["path"] and os.path.exists(p["path"]):
                        os.remove(p["path"])
                except Exception:
                    pass
            conn.execute("DELETE FROM portrait_cache")

            # 2. Reset every hero's portrait to a placeholder so reconcile
            #    re-queues it as full-body. Delete the old bust file too.
            heroes = conn.execute("SELECT id, portrait_path, gender FROM heroes").fetchall()
            for h in heroes:
                pp = h["portrait_path"]
                if pp and "default_" not in pp and os.path.exists(pp):
                    try:
                        os.remove(pp)
                    except Exception:
                        pass
                g = h["gender"] if h["gender"] in ("male", "female") else "unknown"
                conn.execute("UPDATE heroes SET portrait_path = ? WHERE id = ?",
                             (f"static/portraits/default_{g}.png", h["id"]))

            conn.execute("UPDATE base SET portrait_style_version = ? WHERE id = 1", (PORTRAIT_STYLE_VERSION,))

        # 3. Nuke the composited card cache (all stale bust-framed cards).
        try:
            from services.card_template_service import CARD_CACHE_DIR
            if os.path.isdir(CARD_CACHE_DIR):
                for f in os.listdir(CARD_CACHE_DIR):
                    try:
                        os.remove(os.path.join(CARD_CACHE_DIR, f))
                    except Exception:
                        pass
        except Exception:
            pass

        print(f"[Cache] Portrait pipeline v{PORTRAIT_STYLE_VERSION}: wiped old bust portraits + cards; heroes will regenerate full-body.")
    except Exception as e:
        print(f"[Cache] Portrait pipeline reset failed: {e}")


def reconcile_pending_portraits():
    """Re-queue any hero still stuck on a placeholder portrait. The generation
    queue lives in process memory, so a backend restart (or a crashed/lost job)
    can leave a hero's urgent portrait job gone with nothing to retry it. Call
    this on startup so those heroes always self-heal instead of staying blank
    forever until someone notices and clicks 'Regenerate Profile'."""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, name, gender, birth_star FROM heroes WHERE portrait_path LIKE '%default_%'"
        ).fetchall()
    for r in rows:
        hero = dict(r)
        gender = hero["gender"] if hero["gender"] in ("male", "female") else "unknown"
        prompt = build_varied_prompt(hero["birth_star"] or 1, gender)[0]
        queue_custom_portrait(hero["id"], prompt, hero["name"], gender)
    if rows:
        print(f"[Cache] Re-queued {len(rows)} hero portrait(s) left pending from a previous session.")

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def cleanup_portraits():
    """
    Delete truly orphaned portrait files only — files that are neither
    owned by a hero nor tracked in the unclaimed cache pool. Never wipes
    the cache pool itself; a backend restart should not discard cached
    portraits that are still good and unclaimed.
    """
    with db() as conn:
        hero_rows = conn.execute("SELECT portrait_path FROM heroes WHERE portrait_path IS NOT NULL").fetchall()
        owned = {os.path.basename(r["portrait_path"]) for r in hero_rows}

        cache_rows = conn.execute("SELECT id, path FROM portrait_cache").fetchall()
        cached_paths = {os.path.basename(r["path"]) for r in cache_rows}

        # Prune cache rows whose backing file no longer exists on disk.
        for r in cache_rows:
            if not os.path.exists(r["path"]):
                conn.execute("DELETE FROM portrait_cache WHERE id = ?", (r["id"],))

    keep = owned | cached_paths

    deleted = 0
    healed = 0
    cache_filename_re = re.compile(r"^cached_(\d)star_")
    for subdir in ("cached", database.ACTIVE_PROFILE):
        dir_path = f"static/portraits/{subdir}"
        if os.path.isdir(dir_path):
            for fname in os.listdir(dir_path):
                if not fname.endswith(".png") or fname in keep or fname.startswith("default_"):
                    continue
                # A file generated into the cache pool whose DB row never got written —
                # e.g. a reload killed the worker between the file write and the INSERT.
                # Heal it back into the pool instead of deleting a perfectly good
                # portrait; the only thing lost is which gender/class it was rolled for.
                m = cache_filename_re.match(fname) if subdir == "cached" else None
                if m:
                    # class_name is unrecoverable here (the only thing lost
                    # by healing instead of regenerating) — leave it NULL
                    # rather than guessing a real class name. pop_cached_portrait's
                    # caller only overrides the freshly-rolled class when
                    # class_name is truthy, so NULL safely defers to that
                    # roll instead of forcing every healed portrait into
                    # whatever placeholder class got hardcoded here.
                    with db() as conn:
                        conn.execute(
                            "INSERT INTO portrait_cache (birth_star, path, gender, class_name) VALUES (?,?,?,?)",
                            (int(m.group(1)), os.path.join(dir_path, fname), "unknown", None)
                        )
                    healed += 1
                    continue
                try:
                    os.remove(os.path.join(dir_path, fname))
                    deleted += 1
                except Exception:
                    pass

    print(f"[Cache] Startup cleanup: removed {deleted} orphaned files, healed {healed} untracked cache files back into the pool, kept {len(owned)} hero portraits and {len(cached_paths)} unclaimed cache portraits.")
