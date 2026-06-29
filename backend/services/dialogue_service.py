import random

# Static, instant, event-triggered one-liners — distinct from chat_service.py's
# LLM-generated ambient base-camp conversations (which run on a 5-minute
# worker loop and are about lived-in flavor, not a specific moment). This is
# the opposite shape: zero-latency reaction lines fired the instant a summon/
# assignment/victory/defeat/level-up happens, keyed off class archetype +
# rarity tier so a 7-star Mage and a 1-star Warrior never sound alike.

# The 17 real hero classes (see gacha_service.CLASS_STAT_LEAN) collapsed into
# the archetype voices the spec calls out by example, plus "support" as the
# catch-all for the crafting/economy classes that don't map to a combat
# archetype voice.
HERO_CLASS_ARCHETYPE = {
    "Warrior": "aggressive",
    "Spearman": "militaristic",
    "Thief": "terse",
    "Archer": "terse",
    "Mage": "intellectual",
    "Spellsword": "intellectual",
    "Acolyte": "spiritual",
    "Priest": "spiritual",
    "Tactician": "militaristic",
    "Scout": "militaristic",
    "Blacksmith": "support",
    "Medic": "support",
    "Quartermaster": "support",
    "Farmer": "support",
    "Merchant": "support",
    "Alchemist": "intellectual",
    "Magic Engineer": "intellectual",
}


def get_rarity_tier(star: int) -> str:
    if star <= 2:
        return "tier_1_2"
    if star <= 4:
        return "tier_3_4"
    if star == 5:
        return "tier_5"
    if star == 6:
        return "tier_6"
    return "tier_7"


DIALOGUE = {
    "aggressive": {
        "tier_1_2": {
            "summon": ["I'll fight! Just... point me at something."],
            "facility_assign": ["Training? Good. I need to get stronger."],
            "victory": ["We— we won! I actually held my ground!"],
            "defeat": ["I'm not done. Not yet. Just... not yet."],
            "level_up": ["I can feel it. I hit harder now."],
        },
        "tier_3_4": {
            "summon": ["Finally, a real fight waiting for me. Let's go."],
            "facility_assign": ["Training Grounds. Good — I was getting soft."],
            "victory": ["Ha! Told you nothing was going to stop us."],
            "defeat": ["This isn't over. Next time, I end it faster."],
            "level_up": ["My strikes grow sharper. I like this feeling."],
        },
        "tier_5": {
            "summon": ["Don't get in my way. I'll handle this."],
            "facility_assign": ["More training. Fine — I always want more."],
            "victory": ["Did you really think they'd survive me?"],
            "defeat": ["A loss. Mark it. I don't repeat my mistakes."],
            "level_up": ["Stronger. Always stronger. That's the only direction I know."],
        },
        "tier_6": {
            "summon": ["The outcome was decided the moment you called on me."],
            "facility_assign": ["Train me if it pleases you. It changes little."],
            "victory": ["Of course. There was never another outcome."],
            "defeat": ["Even legends stumble once. I won't stumble twice."],
            "level_up": ["Power like mine doesn't announce itself. It simply ends things."],
        },
        "tier_7": {
            "summon": ["I existed before your tower had a name."],
            "facility_assign": ["A formality. I indulge it."],
            "victory": ["The enemy was never a question. Only the timing was."],
            "defeat": ["A wound, not a defeat. Remember the difference."],
            "level_up": ["Even I did not know I had further to climb."],
        },
    },
    "militaristic": {
        "tier_1_2": {
            "summon": ["Reporting for duty. I'll try to hold the line."],
            "facility_assign": ["Yes sir. I'll do my best to keep formation."],
            "victory": ["We held! The formation held — barely, but it held."],
            "defeat": ["The line broke. I should have read the flank better."],
            "level_up": ["I'm learning. Slowly, but I'm learning the formation."],
        },
        "tier_3_4": {
            "summon": ["I've faced worse on the northern wall. Give me my orders."],
            "facility_assign": ["Discipline first, strength after. Understood."],
            "victory": ["Their formation broke at the flank, just as I called it."],
            "defeat": ["A tactical failure. I'll account for it next time."],
            "level_up": ["Sharper reflexes, steadier hands. The drills are paying off."],
        },
        "tier_5": {
            "summon": ["You called for strength? Here I am. Hold the line."],
            "facility_assign": ["Training sharpens the blade. I welcome it."],
            "victory": ["Discipline beats chaos. It always has."],
            "defeat": ["A setback, not a rout. We regroup and we return."],
            "level_up": ["Every campaign refines me. This was no exception."],
        },
        "tier_6": {
            "summon": ["I have commanded armies. Consider this a courtesy."],
            "facility_assign": ["Train the others. I require little of it myself."],
            "victory": ["The battle was won in the planning, not the swinging."],
            "defeat": ["Even the finest campaign has its dark days. We endure."],
            "level_up": ["Mastery isn't a peak. It's a road that keeps unfolding."],
        },
        "tier_7": {
            "summon": ["Wars were fought and forgotten before this Tower stood."],
            "facility_assign": ["I'll observe. It is not unwise to refine even legends."],
            "victory": ["No enemy alive has ever broken my line."],
            "defeat": ["A line bent is not a line broken. Remember that."],
            "level_up": ["Centuries of war, and still I find more to master."],
        },
    },
    "spiritual": {
        "tier_1_2": {
            "summon": ["I'll pray for our safety. Is... is this okay?"],
            "facility_assign": ["I'll tend to my devotions here. Thank you for trusting me."],
            "victory": ["The Light watched over us today. I felt it."],
            "defeat": ["I prayed, but it wasn't enough. I'll pray harder."],
            "level_up": ["My faith feels steadier now. Stronger, somehow."],
        },
        "tier_3_4": {
            "summon": ["The Light guides my hand. Leave this to me."],
            "facility_assign": ["A quiet place to reflect. I'll make good use of it."],
            "victory": ["Even in darkness, I sensed the divine current guiding us."],
            "defeat": ["The Light did not abandon us. We simply weren't ready."],
            "level_up": ["The rites grow clearer to me. I understand more now."],
        },
        "tier_5": {
            "summon": ["Even in darkness, I sense the divine current. I'm ready."],
            "facility_assign": ["Devotion deepens with discipline. I welcome the hours."],
            "victory": ["Faith made manifest. There was no other outcome."],
            "defeat": ["A trial, not an abandonment. The Light tests, it does not forsake."],
            "level_up": ["I feel closer to something vast. Closer than before."],
        },
        "tier_6": {
            "summon": ["Power like mine doesn't announce itself. It simply ends things."],
            "facility_assign": ["I require little instruction. I commune in my own way."],
            "victory": ["The outcome was written before the battle began."],
            "defeat": ["Even the divine permits sorrow. I accept it without complaint."],
            "level_up": ["The current runs deeper through me now than ever before."],
        },
        "tier_7": {
            "summon": ["You don't summon me. I allow myself to appear."],
            "facility_assign": ["A formality, nothing more. I am already complete."],
            "victory": ["The Light and I are no longer separate things."],
            "defeat": ["Even eternity stumbles, once, to remember what it climbed from."],
            "level_up": ["I touch something that has no further name."],
        },
    },
    "intellectual": {
        "tier_1_2": {
            "summon": ["I-I've read about combat. Theory and practice differ, I know."],
            "facility_assign": ["More to study. Good. I learn quickly, I promise."],
            "victory": ["My calculations held! I wasn't sure they would."],
            "defeat": ["I miscalculated. I'll revise the model and do better."],
            "level_up": ["Something clicked. I understand the pattern now."],
        },
        "tier_3_4": {
            "summon": ["Predictable. Their formation has seventeen calculable weaknesses."],
            "facility_assign": ["Research, finally. Don't disturb me unnecessarily."],
            "victory": ["As calculated. You waste my time doubting the math."],
            "defeat": ["An anomaly. I'll account for the variable I missed."],
            "level_up": ["My models are sharper now. Fewer blind spots."],
        },
        "tier_5": {
            "summon": ["You waste my time with easy targets. Show me something worth solving."],
            "facility_assign": ["Give me the materials. I'll have something better by morning."],
            "victory": ["Inevitable, once you understand the variables involved."],
            "defeat": ["An error in the model, not in the method. I'll correct it."],
            "level_up": ["Another layer of the puzzle resolves. Fascinating, really."],
        },
        "tier_6": {
            "summon": ["The outcome was decided the moment you called on me."],
            "facility_assign": ["I will improve this place whether instructed to or not."],
            "victory": ["I solved this before the first blow landed."],
            "defeat": ["A rare variable I hadn't accounted for. It won't recur."],
            "level_up": ["I see further now. The whole equation, almost."],
        },
        "tier_7": {
            "summon": ["I existed before your tower had a name, and before your numbers did."],
            "facility_assign": ["Curiosity, not necessity, brings me here."],
            "victory": ["There was never a version of this where I lost."],
            "defeat": ["A single miscalculation, against an infinity of correct ones."],
            "level_up": ["Even I am still solving what I am."],
        },
    },
    "terse": {
        "tier_1_2": {
            "summon": ["...Fine. I'll try."],
            "facility_assign": ["Okay."],
            "victory": ["We're alive. Good."],
            "defeat": ["...Sorry."],
            "level_up": ["Better. Good."],
        },
        "tier_3_4": {
            "summon": ["Done. What's next?"],
            "facility_assign": ["Fine by me."],
            "victory": ["They never saw it coming."],
            "defeat": ["Slipped up. Won't happen twice."],
            "level_up": ["Sharper now."],
        },
        "tier_5": {
            "summon": ["Done."],
            "facility_assign": ["Sure."],
            "victory": ["They never saw me."],
            "defeat": ["Mistake. Noted."],
            "level_up": ["Cleaner kills now."],
        },
        "tier_6": {
            "summon": ["I'm here. That's enough."],
            "facility_assign": ["Whatever."],
            "victory": ["Already forgotten them."],
            "defeat": ["Rare. Won't repeat."],
            "level_up": ["Faster. Quieter. Better."],
        },
        "tier_7": {
            "summon": ["You don't summon me. I allow myself to appear."],
            "facility_assign": ["Hm."],
            "victory": ["Inevitable."],
            "defeat": ["...Interesting."],
            "level_up": ["Even I didn't expect that."],
        },
    },
    "support": {
        "tier_1_2": {
            "summon": ["I'll do whatever helps the team. I promise."],
            "facility_assign": ["I'll learn the work as fast as I can."],
            "victory": ["We made it through together! I'm so relieved."],
            "defeat": ["I should have done more. I'm sorry, everyone."],
            "level_up": ["I think I'm finally getting the hang of this."],
        },
        "tier_3_4": {
            "summon": ["I've handled harder fights than this. Put me to work."],
            "facility_assign": ["Good. There's always something that needs fixing."],
            "victory": ["Everyone made it back. That's what matters."],
            "defeat": ["A rough one. We'll patch up and try again."],
            "level_up": ["My hands know the work better now. Good."],
        },
        "tier_5": {
            "summon": ["Leave the details to me. I won't let the team down."],
            "facility_assign": ["I'll have this running better within the week."],
            "victory": ["A clean win, and not a soul left behind. That's the standard."],
            "defeat": ["Not our day. We learn, we rebuild, we go again."],
            "level_up": ["I've refined the process. Fewer wasted motions."],
        },
        "tier_6": {
            "summon": ["The outcome was decided the moment you called on me."],
            "facility_assign": ["I'll set the standard everyone else follows here."],
            "victory": ["No one doubted the outcome but you."],
            "defeat": ["A loss, not a failure. I don't confuse the two."],
            "level_up": ["I no longer remember the version of me that struggled with this."],
        },
        "tier_7": {
            "summon": ["I existed before your tower had a name."],
            "facility_assign": ["A courtesy, nothing more — I need little guidance."],
            "victory": ["The team's survival was never truly in question."],
            "defeat": ["Even I misjudge, once a generation. Remember this one."],
            "level_up": ["I am still finding new ceilings to break."],
        },
    },
}

FALLBACK_LINES = {
    "summon": "I'm ready to fight for the team.",
    "facility_assign": "Understood. I'll get to work.",
    "victory": "We made it through. On to the next.",
    "defeat": "We'll come back stronger.",
    "level_up": "I can feel myself growing stronger.",
}


def get_hero_line(hero_class: str, birth_star: int, event: str) -> str:
    """event is one of: summon, facility_assign, victory, defeat, level_up."""
    archetype = HERO_CLASS_ARCHETYPE.get(hero_class, "support")
    tier = get_rarity_tier(birth_star)
    lines = DIALOGUE.get(archetype, {}).get(tier, {}).get(event)
    if not lines:
        return FALLBACK_LINES.get(event, "...")
    return random.choice(lines)
