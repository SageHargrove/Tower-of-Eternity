"""
Seasonal Summon — the limited-time banner on the Summon Altar (design:
"SEASONAL — EMBERFALL · Limited heroes · vanish with the season").

The roster is procedurally generated, so a "featured hero" pool doesn't map
cleanly. Instead the season is a real, distinct calling:

  • its own boosted gem-rarity table (the Gate "burns hotter" — richer odds),
  • every soul it grants is bound to the season's synergy group + visual
    theme, so seasonal pulls cohere into an identifiable set, and
  • a hard end date, after which the calling closes until the next season.

A season is defined by a start date and a length in days; days_left counts
down from there. Swap SEASONS / CURRENT_SEASON_KEY to rotate.
"""
from datetime import date, datetime, timezone

# ── Boosted gem table — a rate-up over the standard GEM_WEIGHTS. Same shape,
# but the high stars are pulled up several-fold (still brutal, just kinder).
# Total renormalizes automatically; only the ratios matter.
# 7★ is unsummonable everywhere, seasonal banners included — transcendence
# (6★ evolution) is the only way to a seventh star.
SEASONAL_GEM_WEIGHTS = {
    1: 60000,  # trimmed from 70860
    2: 22000,
    3: 12000,
    4:  4500,  # 4.5% vs standard 1.0%
    5:  1000,  # 1.0% vs standard 0.13% — the real draw
    6:   500,  # 0.50% vs 0.010% (absorbed the old 7★ share)
}

SEASONS = {
    "emberfall": {
        "key": "emberfall",
        "name": "EMBERFALL",
        "label": "SEASONAL — EMBERFALL",
        "blurb": "Limited heroes · vanish with the season",
        "equip_blurb": "Season-limited armaments",
        "synergy_group": "The Emberfall Court",
        "theme_desc": "clad in ember-lit ceremonial armor, banked coals and "
                      "falling autumn sparks trailing from their cloaks, warm "
                      "amber and ash-violet palette",
        # UTC calendar window.
        "start": date(2026, 7, 1),
        "length_days": 20,
        "weights": SEASONAL_GEM_WEIGHTS,
    },
}

CURRENT_SEASON_KEY = "emberfall"


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def current_season() -> dict:
    """The live season descriptor, with days_left computed against UTC today.
    `active` is False once the window has closed (days_left <= 0)."""
    s = SEASONS.get(CURRENT_SEASON_KEY)
    if not s:
        return {"active": False}
    end = date.fromordinal(s["start"].toordinal() + s["length_days"])
    days_left = (end - _utc_today()).days
    return {
        "active": days_left > 0,
        "key": s["key"],
        "name": s["name"],
        "label": s["label"],
        "blurb": s["blurb"],
        "equip_blurb": s["equip_blurb"],
        "synergy_group": s["synergy_group"],
        "theme_desc": s["theme_desc"],
        "days_left": max(0, days_left),
    }


def season_weights() -> dict:
    """The boosted gem weight table for the current season (falls back to a
    copy of the standard gem table if no season is configured)."""
    s = SEASONS.get(CURRENT_SEASON_KEY)
    if s and s.get("weights"):
        return dict(s["weights"])
    from services.gacha_service import GEM_WEIGHTS
    return dict(GEM_WEIGHTS)
