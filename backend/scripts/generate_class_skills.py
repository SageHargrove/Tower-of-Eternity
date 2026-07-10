"""
Validation utilities for the 148-class skill-kit regeneration effort.

This used to also contain a Claude API caller (generate_one/main) that burned
real Anthropic credits on a run that produced templated/low-quality output,
then again on a real-but-abandoned Sonnet-API pipeline — both times
unintentionally, since the actual authoring for this pass is done directly
by the assistant in conversation, not by an automated script. That
API-calling code has been deleted outright so it can't fire again by
accident. What's left is pure local validation: every hand-authored class
kit gets checked against these rules before being merged into
generated_skills.json, with zero network calls of any kind.
"""
import os
import json

# Every one of the game's 148 classes gets a full 30-skill kit (10/8/6/4/2
# across common/uncommon/rare/epic/legendary) — none of the pre-existing
# hand-tuned kits actually hit that distribution (Warrior had 12, Knight had
# 6), so this is a full regeneration pass, not a "fill the gaps" one.
REQUIRED_COUNTS = {"common": 10, "uncommon": 8, "rare": 6, "epic": 4, "legendary": 2}

OUT_FILE = os.path.join(os.path.dirname(__file__), "generated_skills.json")


def try_rebalance(data: dict) -> bool:
    """A hand-authored kit occasionally lands with the right total (30) but
    the wrong per-rarity split (e.g. 7 rare instead of 6). Rather than
    discard otherwise-good content over a counting slip, move surplus
    skills from an over-full rarity to an under-full one — zero content is
    discarded or invented, only the rarity label (a bucket count, not
    creative substance) is corrected. Mutates data in place; returns True
    if it achieved the exact required distribution."""
    skills = data.get("skills")
    if not isinstance(skills, list) or len(skills) != 30:
        return False  # wrong total skill count isn't a rebalance-able problem

    by_rarity = {r: [] for r in REQUIRED_COUNTS}
    unknown = []
    for s in skills:
        if s.get("rarity") in by_rarity:
            by_rarity[s["rarity"]].append(s)
        else:
            unknown.append(s)
    if unknown:
        return False  # a skill tagged with a bogus rarity string — not safe to guess

    for _ in range(30):  # bounded — one move per iteration, never infinite
        over = [r for r, need in REQUIRED_COUNTS.items() if len(by_rarity[r]) > need]
        under = [r for r, need in REQUIRED_COUNTS.items() if len(by_rarity[r]) < need]
        if not over and not under:
            break
        if not over or not under:
            return False  # shouldn't happen when total==30, but bail safely
        src_r, dst_r = over[0], under[0]
        bucket = by_rarity[src_r]
        # Only donate a skill whose type won't break the donor's own
        # min-1-active/min-1-passive requirement once removed.
        donor_types = [s["type"] for s in bucket]
        movable = [s for s in bucket
                   if donor_types.count(s["type"]) > 1 or REQUIRED_COUNTS[src_r] <= 1]
        if not movable:
            return False
        # Prefer donating whichever type the destination is missing.
        dst_types = {s["type"] for s in by_rarity[dst_r]}
        pick = next((s for s in movable if s["type"] not in dst_types), movable[0])
        bucket.remove(pick)
        pick["rarity"] = dst_r
        by_rarity[dst_r].append(pick)

    if any(len(by_rarity[r]) != need for r, need in REQUIRED_COUNTS.items()):
        return False
    data["skills"] = [s for r in REQUIRED_COUNTS for s in by_rarity[r]]
    return True


def validate_kit(data: dict, class_name: str) -> list[str]:
    """Returns a list of problems; empty list means the kit is good."""
    problems = []
    if data.get("class_name") != class_name:
        problems.append(f"class_name mismatch: got {data.get('class_name')!r}")
    skills = data.get("skills")
    if not isinstance(skills, list):
        return [f"'skills' is not a list"]
    by_rarity = {}
    for s in skills:
        by_rarity.setdefault(s.get("rarity"), []).append(s)
    for rarity, expected in REQUIRED_COUNTS.items():
        got = len(by_rarity.get(rarity, []))
        if got != expected:
            problems.append(f"{rarity}: expected {expected}, got {got}")
        types = {s.get("type") for s in by_rarity.get(rarity, [])}
        if "active" not in types:
            problems.append(f"{rarity}: no active skill")
        if "passive" not in types:
            problems.append(f"{rarity}: no passive skill")
    ids = [s.get("id") for s in skills]
    if len(set(ids)) != len(ids):
        problems.append("duplicate skill ids within this class")
    active_count = sum(1 for s in skills if s.get("type") == "active")
    if active_count > 12:
        problems.append(f"too many actives ({active_count}) - spec wants passives to dominate (target <=12)")
    # A corrupted replacement character (U+FFFD) showed up in one earlier
    # kit's desc text — a real encoding fault, not a display artifact.
    # Reject outright rather than ship broken text.
    for s in skills:
        for field in ("name", "desc"):
            if "�" in (s.get(field) or ""):
                problems.append(f"corrupted character in {s.get('id')}.{field}")
    return problems
